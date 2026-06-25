"""Security helpers — ALLOW_WRITES guard and audit wrappers."""
from functools import wraps
from fastapi import HTTPException
from app.config import get_settings


def require_writes(func):
    """Decorator: raises 403 when ALLOW_WRITES=false."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        settings = get_settings()
        if not settings.ALLOW_WRITES:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "write_disabled",
                    "message": "ALLOW_WRITES=false. Set ALLOW_WRITES=true to enable mutations.",
                    "preview_mode": True,
                },
            )
        return func(*args, **kwargs)
    return wrapper


def check_writes_allowed() -> bool:
    return get_settings().ALLOW_WRITES


def sanitize_for_llm(text: str) -> str:
    """Strip obvious PII patterns before sending to LLM."""
    import re
    # Emails
    text = re.sub(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)
    # Phone numbers
    text = re.sub(r"\b\d{3}[\-.\s]\d{3}[\-.\s]\d{4}\b", "[PHONE]", text)
    # SSN-like
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]", text)
    return text
