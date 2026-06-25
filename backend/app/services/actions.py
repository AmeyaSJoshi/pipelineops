"""
Recruiter action drafting service.
Generates ready-to-use text for common recruiter workflows using the configured LLM.
Falls back to structured templates when LLM is unavailable.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

ACTION_DESCRIPTIONS = {
    "advance_stage": "Draft a message notifying the candidate they are advancing to the next interview stage.",
    "send_update": "Draft a status update message to keep the candidate informed on their application.",
    "schedule_interview": "Draft a message to the candidate requesting availability for an interview.",
    "reject": "Draft a professional, respectful rejection message for the candidate.",
    "make_offer": "Draft a verbal offer notification message to the candidate.",
    "request_references": "Draft a message requesting professional references from the candidate.",
    "reactivate": "Draft a message re-engaging a candidate whose application was previously on hold.",
}

FALLBACK_TEMPLATES = {
    "advance_stage": (
        "Hi {name},\n\n"
        "Thank you for your continued interest in the {role} position. "
        "I'm pleased to let you know that you've been selected to move forward in our process. "
        "I'll be in touch shortly with next steps.\n\n"
        "Best regards,\n{recruiter}"
    ),
    "send_update": (
        "Hi {name},\n\n"
        "I wanted to reach out with a quick update on your application for the {role} role. "
        "Your candidacy is still active, and we expect to have more information for you within the next few business days. "
        "Please don't hesitate to reach out if you have any questions.\n\n"
        "Best regards,\n{recruiter}"
    ),
    "schedule_interview": (
        "Hi {name},\n\n"
        "We'd love to schedule an interview with you for the {role} position. "
        "Could you please share your availability for a 45-minute call over the next week? "
        "Alternatively, feel free to book directly on my calendar using the link below.\n\n"
        "Looking forward to speaking with you!\n\n"
        "Best regards,\n{recruiter}"
    ),
    "reject": (
        "Hi {name},\n\n"
        "Thank you sincerely for the time and effort you invested in our interview process for the {role} role. "
        "After careful consideration, we have decided to move forward with another candidate whose background "
        "more closely aligns with our current needs.\n\n"
        "We genuinely appreciate your interest in our organization and encourage you to apply for future openings "
        "that may be a strong fit.\n\n"
        "We wish you all the best in your search.\n\n"
        "Warm regards,\n{recruiter}"
    ),
    "make_offer": (
        "Hi {name},\n\n"
        "I'm thrilled to share that we'd like to extend you a verbal offer for the {role} position! "
        "We're excited about the prospect of having you join the team. "
        "I'll be sending the formal written offer shortly with all the details. "
        "Please let me know if you have any questions in the meantime.\n\n"
        "Congratulations!\n\n"
        "Best regards,\n{recruiter}"
    ),
    "request_references": (
        "Hi {name},\n\n"
        "As we move forward in the process for the {role} role, "
        "we'd like to conduct professional reference checks. "
        "Could you please provide 2–3 professional references, including their name, title, company, and contact information?\n\n"
        "Thank you, and please reach out if you have any questions.\n\n"
        "Best regards,\n{recruiter}"
    ),
    "reactivate": (
        "Hi {name},\n\n"
        "I hope you're doing well! I'm reaching out because we have reopened the search for the {role} position "
        "and thought of you given your strong background. "
        "Would you still be open to exploring this opportunity?\n\n"
        "I'd love to reconnect. Please let me know if you're available for a brief call.\n\n"
        "Best regards,\n{recruiter}"
    ),
}


def draft_recruiter_action(
    action_type: str,
    candidate: Optional[Any],
    context: Dict[str, Any],
    settings: Any,
) -> Dict[str, Any]:
    """
    Draft a recruiter action message.
    Returns dict with: action_type, candidate_name, draft, mode, instructions.
    """
    if action_type not in ACTION_DESCRIPTIONS:
        return {
            "error": f"Unknown action type '{action_type}'.",
            "supported_actions": list(ACTION_DESCRIPTIONS.keys()),
        }

    candidate_name = candidate.full_name if candidate else context.get("candidate_name", "Candidate")
    role_title = context.get("role_title") or context.get("job_title") or "the position"
    recruiter_name = context.get("recruiter_name") or "Your Recruiter"

    if settings.llm_available():
        draft = _llm_draft(action_type, candidate_name, role_title, recruiter_name, context, settings)
        mode = "gmi_maas" if settings.gmi_configured() else "local_llm"
    else:
        draft = _template_draft(action_type, candidate_name, role_title, recruiter_name)
        mode = "template_fallback"

    return {
        "action_type": action_type,
        "candidate_name": candidate_name,
        "role_title": role_title,
        "draft": draft,
        "mode": mode,
        "instructions": "Review and personalize before sending. Do not send AI-generated text without human review.",
    }


def _template_draft(action_type: str, name: str, role: str, recruiter: str) -> str:
    template = FALLBACK_TEMPLATES.get(action_type, "")
    return template.format(name=name, role=role, recruiter=recruiter)


def _llm_draft(
    action_type: str,
    name: str,
    role: str,
    recruiter: str,
    context: Dict[str, Any],
    settings: Any,
) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(base_url=settings.get_llm_base_url(), api_key=settings.get_llm_api_key())

        additional = ""
        if context.get("current_stage"):
            additional += f"\nCurrent stage: {context['current_stage']}"
        if context.get("notes"):
            additional += f"\nContext notes: {context['notes']}"

        system_prompt = (
            "You are a professional recruiter drafting outreach messages. "
            "Write concisely and professionally. "
            "Do not invent details about compensation, timelines, or company information not provided. "
            "Use first-person from the recruiter's perspective."
        )
        user_prompt = (
            f"Draft a '{action_type}' message to a candidate.\n"
            f"Candidate name: {name}\n"
            f"Role: {role}\n"
            f"Recruiter name: {recruiter}"
            f"{additional}\n\n"
            f"Action description: {ACTION_DESCRIPTIONS[action_type]}\n\n"
            "Write only the message body, no subject line. Keep it under 200 words."
        )

        resp = client.chat.completions.create(
            model=settings.get_llm_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=400,
            temperature=0.4,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("LLM action draft failed, using template: %s", e)
        return _template_draft(action_type, name, role, recruiter)
