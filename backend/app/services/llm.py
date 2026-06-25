from typing import Any, Dict, List, Optional
from app.config import get_settings

settings = get_settings()


def _get_client():
    if not settings.llm_available():
        return None
    try:
        from openai import OpenAI
        return OpenAI(
            base_url=settings.get_llm_base_url(),
            api_key=settings.get_llm_api_key(),
        )
    except ImportError:
        return None


def _chat(messages: List[Dict[str, str]], fallback: str) -> str:
    client = _get_client()
    if not client:
        return fallback
    try:
        response = client.chat.completions.create(
            model=settings.get_llm_model(),
            messages=messages,
            max_tokens=1024,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"{fallback} [LLM unavailable: {str(e)[:100]}]"


def classify_stage(raw_stage: str, context: Optional[str] = None) -> str:
    """Use LLM to classify ambiguous stages when rule-based mapping fails."""
    if not settings.llm_available():
        return "unknown"

    prompt = f"""You are a recruiting operations system. Map this raw stage label to one of these canonical stages:
new_lead, applied, recruiter_screen, qualified, submitted_to_client, client_review, interview_scheduled, interview_completed, offer, placed, rejected, withdrawn, unknown

Raw stage: "{raw_stage}"
{f'Context: {context}' if context else ''}

Reply with only the canonical stage name, nothing else."""

    result = _chat(
        [{"role": "user", "content": prompt}],
        fallback="unknown"
    )
    valid_stages = [
        "new_lead", "applied", "recruiter_screen", "qualified",
        "submitted_to_client", "client_review", "interview_scheduled",
        "interview_completed", "offer", "placed", "rejected", "withdrawn", "unknown"
    ]
    result = result.strip().lower()
    return result if result in valid_stages else "unknown"


def map_csv_headers(headers: List[str], sample_rows: List[Dict]) -> Dict[str, str]:
    """Map CSV column headers to canonical field names."""
    if not settings.llm_available():
        return _heuristic_header_map(headers)

    sample_str = str(sample_rows[:3]) if sample_rows else "N/A"
    prompt = f"""You are a recruiting data pipeline. Map these CSV column headers to canonical field names.

Available canonical fields: job_title, company, location, pay_rate, status, applicant_name, email, phone, stage, applied_date, recruiter, notes, external_id, openings

CSV Headers: {headers}
Sample rows: {sample_str}

Return a JSON object mapping each header to its canonical field. Use null if no mapping exists. Example: {{"Job Title": "job_title", "Location": "location"}}"""

    result = _chat(
        [{"role": "user", "content": prompt}],
        fallback="{}"
    )
    try:
        import json
        parsed = json.loads(result)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return _heuristic_header_map(headers)


def _heuristic_header_map(headers: List[str]) -> Dict[str, str]:
    mapping = {}
    canonical_map = {
        "title": "job_title", "job title": "job_title", "position": "job_title",
        "company": "company", "employer": "company", "client": "company",
        "location": "location", "city": "location",
        "pay": "pay_rate", "salary": "pay_rate", "pay rate": "pay_rate", "compensation": "pay_rate",
        "status": "status", "stage": "stage",
        "name": "applicant_name", "applicant": "applicant_name", "candidate": "applicant_name",
        "email": "email", "phone": "phone",
        "date": "applied_date", "applied": "applied_date",
        "recruiter": "recruiter", "owner": "recruiter",
        "notes": "notes", "openings": "openings", "id": "external_id",
    }
    for h in headers:
        h_lower = h.lower().strip()
        mapping[h] = canonical_map.get(h_lower)
    return mapping


def generate_report(metrics: Dict[str, Any], anomalies: List[Dict]) -> str:
    """Generate a manager-facing narrative summary."""
    from app.services.reporting import generate_narrative_summary
    base = generate_narrative_summary(metrics, anomalies)

    if not settings.llm_available():
        return base

    high_anomaly_titles = [a.get("title", "") for a in anomalies if a.get("severity") == "high"][:5]
    prompt = f"""You are a recruiting operations AI assistant. Write a concise, professional manager report summary (3-4 sentences) based on these pipeline metrics and issues. Do NOT fabricate data — use only what is provided.

Metrics: {metrics}
High-priority issues: {high_anomaly_titles}
Base summary: {base}

Write a clear, actionable summary for a recruiting manager."""

    return _chat(
        [{"role": "user", "content": prompt}],
        fallback=base
    )


def explain_anomaly(anomaly: Dict[str, Any], related_records: Optional[List[Dict]] = None) -> str:
    """Explain an anomaly in plain English for a recruiter."""
    base = anomaly.get("explanation", "This anomaly needs attention.")
    if not settings.llm_available():
        return base

    prompt = f"""You are a recruiting ops AI. Explain this pipeline issue in plain English for a recruiter. Be direct and actionable. One paragraph max.

Issue: {anomaly.get('title')}
Category: {anomaly.get('category')}
Details: {anomaly.get('explanation')}
Recommended fix: {anomaly.get('recommended_fix')}"""

    return _chat(
        [{"role": "user", "content": prompt}],
        fallback=base
    )


def answer_chat_question(question: str, retrieved_context: Dict[str, Any]) -> str:
    """Answer a recruiter's question using retrieved pipeline data."""
    if not settings.llm_available():
        return _deterministic_chat_response(question, retrieved_context)

    context_str = _format_context_for_llm(retrieved_context)
    prompt = f"""You are PipelineOps Agent, an AI recruiting operations assistant. Answer the recruiter's question using ONLY the data provided below. If the data doesn't answer the question, say so clearly. Do not hallucinate data.

Recruiting Pipeline Data:
{context_str}

Recruiter question: {question}

Answer concisely and professionally. Focus on actionable insights."""

    return _chat(
        [
            {"role": "system", "content": "You are PipelineOps Agent, a recruiting operations AI. Answer only from provided data."},
            {"role": "user", "content": prompt}
        ],
        fallback=_deterministic_chat_response(question, retrieved_context)
    )


def _format_context_for_llm(ctx: Dict[str, Any]) -> str:
    parts = []
    if ctx.get("metrics"):
        m = ctx["metrics"]
        parts.append(f"Pipeline: {m.get('open_roles')} open roles, {m.get('active_candidates')} active candidates")
        parts.append(f"Funnel: {m.get('submitted_to_client_count')} submitted, {m.get('interview_count')} interviews, {m.get('offer_count')} offers, {m.get('placement_count')} placed")
        parts.append(f"Hit rate: {m.get('overall_hit_rate', 0):.1%}")
        if m.get("stale_role_count"):
            parts.append(f"Stale roles: {m['stale_role_count']}")
    if ctx.get("anomalies"):
        high = [a.get("title") for a in ctx["anomalies"] if a.get("severity") == "high"][:3]
        if high:
            parts.append(f"High-priority issues: {', '.join(high)}")
    if ctx.get("roles"):
        role_names = [r.get("title", "") for r in ctx["roles"][:5]]
        parts.append(f"Top roles: {', '.join(role_names)}")
    return "\n".join(parts) if parts else "No pipeline data available."


def _deterministic_chat_response(question: str, context: Dict[str, Any]) -> str:
    q = question.lower()
    metrics = context.get("metrics", {})
    anomalies = context.get("anomalies", [])

    if any(w in q for w in ["stale", "old", "outdated", "inactive"]):
        count = metrics.get("stale_role_count", 0)
        return f"There are {count} stale roles that haven't been updated in 14+ days. Check the Anomalies tab for details on which roles need attention."

    if any(w in q for w in ["drop", "dropping off", "bottleneck", "stuck"]):
        submit_rate = metrics.get("submit_rate", 0)
        interview_rate = metrics.get("interview_rate", 0)
        if submit_rate < 0.2:
            return f"The biggest drop-off is at the submission stage — only {submit_rate:.1%} of applicants are being submitted to clients. Focus on screening and submitting more qualified candidates."
        if interview_rate < 0.3:
            return f"Candidates are dropping off after client submission — only {interview_rate:.1%} of submitted candidates reach interviews. Client feedback or candidate quality may be the issue."
        return f"Submit rate is {submit_rate:.1%} and interview rate is {interview_rate:.1%}. The pipeline looks relatively healthy."

    if any(w in q for w in ["offer rate", "best offer", "best client"]):
        roles_by_client = metrics.get("roles_by_client", {})
        if roles_by_client:
            top = max(roles_by_client, key=roles_by_client.get)
            return f"{top} has the most open roles ({roles_by_client[top]}). Full offer-rate-by-client analysis requires more detailed data — check the Reports tab."
        return "Not enough client data to compare offer rates. Run a full pipeline refresh first."

    if any(w in q for w in ["attention", "priority", "need help", "focus"]):
        stale = metrics.get("stale_role_count", 0)
        missing_pay = metrics.get("missing_pay_rate_count", 0)
        high_issues = [a for a in anomalies if a.get("severity") == "high"]
        resp = []
        if high_issues:
            resp.append(f"{len(high_issues)} high-severity issues need immediate attention.")
        if stale:
            resp.append(f"{stale} stale roles need client confirmation.")
        if missing_pay:
            resp.append(f"{missing_pay} roles are missing pay rates.")
        return " ".join(resp) if resp else "No critical issues found. Pipeline is in good shape."

    if any(w in q for w in ["report", "summary", "manager", "update", "weekly"]):
        open_r = metrics.get("open_roles", 0)
        placed = metrics.get("placement_count", 0)
        offers = metrics.get("offer_count", 0)
        interviews = metrics.get("interview_count", 0)
        return (
            f"This week's pipeline: {open_r} open roles, {interviews} candidates in interviews, "
            f"{offers} offers outstanding, {placed} placements confirmed. "
            f"Check the Reports tab to export the full manager summary."
        )

    # Generic fallback
    open_r = metrics.get("open_roles", 0)
    active = metrics.get("active_candidates", 0)
    return (
        f"Current pipeline has {open_r} open roles and {active} active candidates. "
        f"Use the dashboard for detailed metrics or check the Anomalies tab for issues. "
        f"[Demo mode — connect GMI MaaS for enhanced AI responses]"
    )
