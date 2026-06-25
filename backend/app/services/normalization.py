import hashlib
import re
from typing import Any, Dict, Optional, Tuple


CANONICAL_STAGES = [
    "new_lead", "applied", "recruiter_screen", "qualified",
    "submitted_to_client", "client_review", "interview_scheduled",
    "interview_completed", "offer", "placed", "rejected", "withdrawn", "unknown"
]

STAGE_MAP = {
    # Job board style
    "applied": "applied",
    "new applicant": "applied",
    "new": "applied",
    "application received": "applied",
    "screened": "recruiter_screen",
    "phone screen": "recruiter_screen",
    "phone screening": "recruiter_screen",
    "recruiter screen": "recruiter_screen",
    "pre-screen": "recruiter_screen",
    "qualified": "qualified",
    "not selected": "rejected",
    "declined": "rejected",
    "rejected": "rejected",
    "disqualified": "rejected",
    "archive": "rejected",
    "archived": "rejected",
    "no": "rejected",
    "withdrawn": "withdrawn",
    "candidate withdrew": "withdrawn",
    "withdrew": "withdrawn",
    # Staffing/client style
    "sent to client": "submitted_to_client",
    "submitted": "submitted_to_client",
    "submitted to client": "submitted_to_client",
    "client submission": "submitted_to_client",
    "client review": "client_review",
    "hiring manager review": "client_review",
    "client considering": "client_review",
    "interview": "interview_scheduled",
    "interview scheduled": "interview_scheduled",
    "onsite": "interview_scheduled",
    "onsite interview": "interview_scheduled",
    "interview complete": "interview_completed",
    "interview completed": "interview_completed",
    "post interview": "interview_completed",
    "offer extended": "offer",
    "offer": "offer",
    "offered": "offer",
    "verbal offer": "offer",
    "start date confirmed": "placed",
    "placed": "placed",
    "hired": "placed",
    "started": "placed",
    "new lead": "new_lead",
    "lead": "new_lead",
    # ATS style
    "phone screen": "recruiter_screen",
    "technical screen": "recruiter_screen",
    "take home": "recruiter_screen",
    "hiring manager screen": "client_review",
    "approved": "placed",
    "approval": "placed",
}


def normalize_title(title: str) -> str:
    if not title:
        return ""
    t = title.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t.title()


def normalize_company(company: str) -> str:
    if not company:
        return ""
    c = company.strip().lower()
    c = re.sub(r"\b(inc|llc|corp|ltd|co|company|group|holdings)\b\.?", "", c)
    c = re.sub(r"\s+", " ", c).strip()
    return c


def parse_location(location_string: str) -> Dict[str, Optional[str]]:
    if not location_string:
        return {"city": None, "state": None, "country": "US", "remote_type": "unknown"}

    s = location_string.strip()
    remote_type = "onsite"

    s_lower = s.lower()
    if "remote" in s_lower and "hybrid" in s_lower:
        remote_type = "hybrid"
    elif "remote" in s_lower and ("united states" in s_lower or s_lower == "remote" or "us remote" in s_lower):
        return {"city": None, "state": None, "country": "US", "remote_type": "remote"}
    elif s_lower == "remote":
        return {"city": None, "state": None, "country": "US", "remote_type": "remote"}
    elif "remote" in s_lower:
        remote_type = "remote"
    elif "hybrid" in s_lower:
        remote_type = "hybrid"
        s = re.sub(r"hybrid\s*[-–]\s*", "", s, flags=re.IGNORECASE).strip()

    # Try to parse "City, ST" pattern
    match = re.match(r"^([^,]+),\s*([A-Z]{2})$", s.strip())
    if match:
        return {
            "city": match.group(1).strip(),
            "state": match.group(2).strip(),
            "country": "US",
            "remote_type": remote_type,
        }

    return {"city": s, "state": None, "country": "US", "remote_type": remote_type}


def parse_pay_range(pay_string: str) -> Tuple[Optional[float], Optional[float], str]:
    """Returns (pay_min, pay_max, pay_unit)."""
    if not pay_string or pay_string.strip().upper() in ("DOE", "TBD", "N/A", "", "NEGOTIABLE"):
        return None, None, "unknown"

    s = pay_string.strip()
    unit = "unknown"

    s_lower = s.lower()
    if any(x in s_lower for x in ["an hour", "/hr", "per hour", "/h", "hourly"]):
        unit = "hourly"
    elif any(x in s_lower for x in ["salary", "annual", "year", "/yr", "per year"]):
        unit = "salary"
    elif "k" in s_lower or "000" in s:
        unit = "salary"

    # Remove currency symbols, letters except k/K, slashes, spaces
    clean = re.sub(r"[^\d.\-k]", " ", s, flags=re.IGNORECASE)
    # Handle "up to X"
    up_to_match = re.search(r"up\s+to\s+\$?([\d,\.]+)(k?)", pay_string, re.IGNORECASE)
    if up_to_match:
        val = float(up_to_match.group(1).replace(",", ""))
        if up_to_match.group(2).lower() == "k":
            val *= 1000
        if unit == "unknown":
            unit = "hourly" if val < 200 else "salary"
        return None, val, unit

    # Extract all numbers
    nums = re.findall(r"[\d,]+(?:\.\d+)?", s)
    if not nums:
        return None, None, "unknown"

    values = []
    for n in nums:
        try:
            v = float(n.replace(",", ""))
            # Handle "k" multiplier
            idx = s.lower().find(n.replace(",", "").replace(".", ""))
            if idx >= 0 and idx + len(n) < len(s) and s[idx + len(n.replace(",", ""))].lower() == "k":
                v *= 1000
            values.append(v)
        except ValueError:
            pass

    # Handle explicit k suffix patterns like $70k-$85k
    k_matches = re.findall(r"\$?([\d]+)k", s, re.IGNORECASE)
    if k_matches:
        values = [float(v) * 1000 for v in k_matches]

    if not values:
        return None, None, unit

    if unit == "unknown":
        unit = "hourly" if max(values) < 500 else "salary"

    if len(values) == 1:
        return None, values[0], unit
    return min(values), max(values), unit


def canonicalize_stage(raw_stage: str, context: Optional[str] = None) -> str:
    if not raw_stage:
        return "unknown"
    key = raw_stage.strip().lower()
    if key in STAGE_MAP:
        return STAGE_MAP[key]
    # Fuzzy partial match
    for k, v in STAGE_MAP.items():
        if k in key or key in k:
            return v
    return "unknown"


def detect_remote_type(text: str) -> str:
    if not text:
        return "unknown"
    t = text.lower()
    if "hybrid" in t:
        return "hybrid"
    if "remote" in t:
        return "remote"
    if any(x in t for x in ["onsite", "on-site", "in office", "in-office"]):
        return "onsite"
    return "onsite"


def hash_email(email: str) -> Optional[str]:
    if not email:
        return None
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def hash_phone(phone: str) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7:
        return None
    return hashlib.sha256(digits.encode()).hexdigest()


def mask_email(email: str) -> Optional[str]:
    if not email or "@" not in email:
        return email
    local, domain = email.rsplit("@", 1)
    if len(local) <= 2:
        masked = local[0] + "*" * (len(local) - 1)
    else:
        masked = local[0] + "*" * (len(local) - 2) + local[-1]
    domain_parts = domain.split(".")
    masked_domain = domain_parts[0][0] + "*" * (len(domain_parts[0]) - 1)
    return f"{masked}@{masked_domain}.{'.'.join(domain_parts[1:])}"


def mask_phone(phone: str) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7:
        return phone
    return f"***-***-{digits[-4:]}"


def content_hash(record: Dict[str, Any]) -> str:
    import json
    serialized = json.dumps(record, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()


def normalize_job(raw_record: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    """Normalize a raw job record into canonical form."""
    title = raw_record.get("title") or raw_record.get("jobTitle") or raw_record.get("name") or ""
    company = (
        raw_record.get("company")
        or raw_record.get("clientCorporation", {}).get("name", "") if isinstance(raw_record.get("clientCorporation"), dict) else raw_record.get("clientCorporation", "")
        or ""
    )
    location_raw = (
        raw_record.get("location")
        or raw_record.get("jobLocation")
        or (raw_record.get("offices", [{}])[0].get("name") if raw_record.get("offices") else None)
        or ""
    )
    pay_raw = (
        str(raw_record.get("salary") or raw_record.get("payRate") or raw_record.get("pay") or "")
    )
    pay_min, pay_max, pay_unit = parse_pay_range(pay_raw)
    loc = parse_location(str(location_raw))

    return {
        "external_id": str(raw_record.get("id") or raw_record.get("jobPostingId") or raw_record.get("jobId") or ""),
        "title": title,
        "normalized_title": normalize_title(title),
        "company": company,
        "normalized_company": normalize_company(company),
        "location_city": loc["city"],
        "location_state": loc["state"],
        "location_country": loc.get("country", "US"),
        "remote_type": loc["remote_type"],
        "pay_min": pay_min,
        "pay_max": pay_max,
        "pay_unit": pay_unit,
        "openings_count": int(raw_record.get("openings") or raw_record.get("openingsCount") or 1),
        "employment_type": raw_record.get("employmentType") or raw_record.get("jobType"),
        "status": raw_record.get("status") or "open",
        "recruiter_owner": raw_record.get("recruiter") or raw_record.get("owner"),
        "source_type": source_type,
    }


def normalize_candidate(raw_record: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    name = (
        raw_record.get("full_name")
        or raw_record.get("fullName")
        or raw_record.get("name")
        or f"{raw_record.get('firstName', '')} {raw_record.get('lastName', '')}".strip()
        or "Unknown"
    )
    email = raw_record.get("email") or raw_record.get("emailAddress") or ""
    phone = raw_record.get("phone") or raw_record.get("phoneNumber") or raw_record.get("mobile") or ""
    return {
        "external_id": str(raw_record.get("id") or raw_record.get("candidateId") or ""),
        "full_name": name,
        "email_hash": hash_email(email),
        "email_display_masked": mask_email(email) if email else None,
        "phone_hash": hash_phone(phone),
        "phone_display_masked": mask_phone(phone) if phone else None,
        "location": raw_record.get("location") or raw_record.get("city"),
        "current_title": raw_record.get("current_title") or raw_record.get("currentTitle") or raw_record.get("title"),
        "current_company": raw_record.get("current_company") or raw_record.get("currentCompany"),
        "source_type": source_type,
    }


def normalize_application(raw_record: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    raw_stage = (
        raw_record.get("stage")
        or raw_record.get("status")
        or raw_record.get("applicationStatus")
        or ""
    )
    return {
        "external_id": str(raw_record.get("id") or raw_record.get("applicationId") or ""),
        "source": source_type,
        "raw_stage": raw_stage,
        "canonical_stage": canonicalize_stage(raw_stage),
        "status": "active",
        "applied_at": raw_record.get("appliedAt") or raw_record.get("createdAt"),
        "last_activity_at": raw_record.get("lastActivityAt") or raw_record.get("updatedAt"),
        "recruiter_owner": raw_record.get("recruiter") or raw_record.get("owner"),
        "offer_amount": raw_record.get("offerAmount") or raw_record.get("offer"),
        "notes_summary": raw_record.get("notes"),
    }
