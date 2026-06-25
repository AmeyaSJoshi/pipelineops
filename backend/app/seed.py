"""Seed realistic synthetic demo data for PipelineOps Agent."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import (
    SourceAccount, Company, JobRole, Candidate, Application, SyncRun
)
from app.services.normalization import hash_email, hash_phone, mask_email, mask_phone


def seed_demo_data(db: Session) -> dict:
    # Source accounts
    # Blocked sources have no official public API — see CONNECTOR_AUDIT.md.
    # Live sources show needs_credentials until real API keys are set.
    sources = [
        SourceAccount(source_type="indeed",        display_name="Indeed",        status="blocked",           records_total=0),
        SourceAccount(source_type="careerbuilder", display_name="CareerBuilder", status="blocked",           records_total=0),
        SourceAccount(source_type="monster",       display_name="Monster",       status="blocked",           records_total=0),
        SourceAccount(source_type="dice",          display_name="Dice",          status="blocked",           records_total=0),
        SourceAccount(source_type="greenhouse",    display_name="Greenhouse",    status="needs_credentials", records_total=0),
        SourceAccount(source_type="lever",         display_name="Lever",         status="needs_credentials", records_total=0),
        SourceAccount(source_type="bullhorn",      display_name="Bullhorn",      status="needs_credentials", records_total=0),
        SourceAccount(source_type="csv",           display_name="CSV / Excel",   status="ready",             records_total=0),
        SourceAccount(source_type="google_sheets", display_name="Google Sheets", status="needs_credentials", records_total=0),
    ]
    for s in sources:
        db.add(s)
    db.flush()
    src_map = {s.source_type: s for s in sources}

    # Companies / clients
    companies_data = [
        ("Acme Logistics",   "acme logistics"),
        ("Northstar Health", "northstar health"),
        ("Meridian Robotics","meridian robotics"),
        ("Summit Finance",   "summit finance"),
        ("BluePeak Retail",  "bluepeak retail"),
    ]
    companies = []
    for name, normalized in companies_data:
        c = Company(name=name, normalized_name=normalized)
        db.add(c)
        companies.append(c)
    db.flush()
    acme, northstar, meridian, summit, bluepeak = companies

    now       = datetime.utcnow()
    stale     = now - timedelta(days=19)   # intentionally stale
    very_old  = now - timedelta(days=28)
    week_ago  = now - timedelta(days=7)
    two_weeks = now - timedelta(days=14)

    # ── Job Roles ──────────────────────────────────────────────────────────────
    roles_data = [
        # 0 Warehouse — stale, high volume
        JobRole(
            company_id=acme.id, source_account_id=src_map["indeed"].id,
            title="Warehouse Associate", normalized_title="Warehouse Associate",
            location_city="Dallas", location_state="TX", remote_type="onsite",
            pay_min=18, pay_max=22, pay_unit="hourly", openings_count=12,
            status="open", recruiter_owner="Sarah Mitchell",
            updated_at=stale, created_at=stale - timedelta(days=10),
        ),
        # 1 Medical
        JobRole(
            company_id=northstar.id, source_account_id=src_map["bullhorn"].id,
            title="Medical Assistant", normalized_title="Medical Assistant",
            location_city="Phoenix", location_state="AZ", remote_type="onsite",
            pay_min=23, pay_max=28, pay_unit="hourly", openings_count=5,
            status="open", recruiter_owner="Rachel Moore",
            updated_at=now - timedelta(days=3),
        ),
        # 2 Robotics — very stale
        JobRole(
            company_id=meridian.id, source_account_id=src_map["greenhouse"].id,
            title="Robotics Technician", normalized_title="Robotics Technician",
            location_city="San Jose", location_state="CA", remote_type="onsite",
            pay_min=35, pay_max=45, pay_unit="hourly", openings_count=3,
            status="open", recruiter_owner="David Chen",
            updated_at=stale - timedelta(days=5),
        ),
        # 3 Accountant
        JobRole(
            company_id=summit.id, source_account_id=src_map["lever"].id,
            title="Staff Accountant", normalized_title="Staff Accountant",
            location_city="Chicago", location_state="IL", remote_type="onsite",
            pay_min=70000, pay_max=85000, pay_unit="salary", openings_count=2,
            status="open", recruiter_owner="Jordan Blake",
            updated_at=now - timedelta(days=5),
        ),
        # 4 Retail
        JobRole(
            company_id=bluepeak.id, source_account_id=src_map["indeed"].id,
            title="Retail Shift Lead", normalized_title="Retail Shift Lead",
            location_city="Denver", location_state="CO", remote_type="onsite",
            pay_min=20, pay_max=24, pay_unit="hourly", openings_count=8,
            status="open", recruiter_owner="Marcus Webb",
            updated_at=now - timedelta(days=1),
        ),
        # 5 Java — remote
        JobRole(
            company_id=bluepeak.id, source_account_id=src_map["dice"].id,
            title="Java Backend Engineer", normalized_title="Java Backend Engineer",
            location_city=None, location_state=None, remote_type="remote",
            pay_min=120000, pay_max=150000, pay_unit="salary", openings_count=2,
            status="open", recruiter_owner="Priya Shah",
            updated_at=now - timedelta(days=2),
        ),
        # 6 Forklift — no pay rate, stale (double anomaly)
        JobRole(
            company_id=acme.id, source_account_id=src_map["careerbuilder"].id,
            title="Forklift Operator", normalized_title="Forklift Operator",
            location_city="Dallas", location_state="TX", remote_type="onsite",
            pay_min=None, pay_max=None, pay_unit="unknown", openings_count=4,
            status="open", recruiter_owner="Sarah Mitchell",
            updated_at=stale,
        ),
        # 7 Data Analyst — new, minimal activity
        JobRole(
            company_id=summit.id, source_account_id=src_map["lever"].id,
            title="Data Analyst", normalized_title="Data Analyst",
            location_city="Chicago", location_state="IL", remote_type="hybrid",
            pay_min=75000, pay_max=95000, pay_unit="salary", openings_count=1,
            status="open", recruiter_owner="Jordan Blake",
            updated_at=now - timedelta(days=2),
        ),
        # 8 CNA — Northstar
        JobRole(
            company_id=northstar.id, source_account_id=src_map["bullhorn"].id,
            title="Certified Nursing Assistant", normalized_title="Certified Nursing Assistant",
            location_city="Phoenix", location_state="AZ", remote_type="onsite",
            pay_min=17, pay_max=21, pay_unit="hourly", openings_count=6,
            status="open", recruiter_owner="Rachel Moore",
            updated_at=now - timedelta(days=4),
        ),
    ]
    for r in roles_data:
        db.add(r)
    db.flush()
    (role_warehouse, role_medical, role_robotics, role_accountant,
     role_retail, role_java, role_forklift, role_analyst, role_cna) = roles_data

    # ── Candidates (50 total — spec says 40-80) ───────────────────────────────
    raw_candidates = [
        # Warehouse pool (Dallas)
        {"name": "James Rivera",      "email": "james.rivera@email.com",   "phone": "214-555-0101", "loc": "Dallas, TX",       "title": "Warehouse Worker",        "src": "indeed"},
        {"name": "Linda Park",        "email": "linda.park@email.com",     "phone": "214-555-0102", "loc": "Dallas, TX",       "title": "Logistics Associate",     "src": "indeed"},
        {"name": "Carlos Mendez",     "email": "c.mendez@email.com",       "phone": "214-555-0103", "loc": "Fort Worth, TX",   "title": "Warehouse Team Lead",     "src": "indeed"},
        {"name": "Steven Garcia",     "email": "s.garcia@email.com",       "phone": "214-555-0701", "loc": "Dallas, TX",       "title": "Shipping Clerk",          "src": "careerbuilder"},
        {"name": "Maria Gonzalez",    "email": "maria.g@email.com",        "phone": "214-555-0702", "loc": "Dallas, TX",       "title": "Receiving Associate",     "src": "careerbuilder"},
        # Intentional duplicate — same person, different email capitalization
        {"name": "james rivera",      "email": "James.Rivera@Email.com",   "phone": "214-555-0101", "loc": "Dallas, TX",       "title": "Warehouse Worker",        "src": "careerbuilder"},
        {"name": "Darnell Brown",     "email": "d.brown@email.com",        "phone": "214-555-0104", "loc": "Dallas, TX",       "title": "Material Handler",        "src": "indeed"},
        {"name": "Rosa Fuentes",      "email": "rosa.f@email.com",         "phone": "214-555-0105", "loc": "Irving, TX",       "title": "Picker Packer",           "src": "monster"},
        {"name": "Terry Owens",       "email": "terry.o@email.com",        "phone": "214-555-0106", "loc": "Grand Prairie, TX","title": "Forklift Driver",         "src": "monster"},
        {"name": "Cynthia Ellis",     "email": "cynthia.e@email.com",      "phone": "214-555-0107", "loc": "Dallas, TX",       "title": "Inventory Clerk",         "src": "careerbuilder"},
        # Medical pool (Phoenix)
        {"name": "Natalie Johnson",   "email": "natalie.j@email.com",      "phone": "602-555-0601", "loc": "Phoenix, AZ",      "title": "Medical Assistant",       "src": "bullhorn"},
        {"name": "Omar Hassan",       "email": "o.hassan@email.com",       "phone": "602-555-0602", "loc": "Phoenix, AZ",      "title": "Phlebotomist",            "src": "bullhorn"},
        {"name": "Crystal Brooks",    "email": "c.brooks@email.com",       "phone": "602-555-0603", "loc": "Scottsdale, AZ",   "title": "Medical Office Specialist","src": "bullhorn"},
        {"name": "Hector Ramirez",    "email": "h.ramirez@email.com",      "phone": "602-555-0604", "loc": "Phoenix, AZ",      "title": "Clinical Assistant",      "src": "bullhorn"},
        {"name": "Tanya White",       "email": "tanya.white@email.com",    "phone": "602-555-0605", "loc": "Mesa, AZ",         "title": "Medical Assistant",       "src": "bullhorn"},
        {"name": "Brianna Walters",   "email": "b.walters@email.com",      "phone": "602-555-0606", "loc": "Tempe, AZ",        "title": "Patient Care Tech",       "src": "indeed"},
        {"name": "Felix Ortega",      "email": "f.ortega@email.com",       "phone": "602-555-0607", "loc": "Phoenix, AZ",      "title": "Medical Scribe",          "src": "indeed"},
        # Robotics pool (San Jose)
        {"name": "Michael Torres",    "email": "michael.torres@email.com", "phone": "408-555-0301", "loc": "San Jose, CA",     "title": "Electronics Technician",  "src": "greenhouse"},
        {"name": "Rachel Nguyen",     "email": "r.nguyen@email.com",       "phone": "408-555-0302", "loc": "San Jose, CA",     "title": "Automation Engineer",     "src": "greenhouse"},
        {"name": "Kevin Patel",       "email": "k.patel@email.com",        "phone": "415-555-0303", "loc": "San Jose, CA",     "title": "Robotics Engineer",       "src": "greenhouse"},
        {"name": "Andre Martin",      "email": "a.martin@email.com",       "phone": "408-555-0801", "loc": "San Jose, CA",     "title": "Electronics Technician",  "src": "monster"},
        {"name": "Priya Sharma",      "email": "priya.s@email.com",        "phone": "408-555-0802", "loc": "Santa Clara, CA",  "title": "Automation Technician",   "src": "monster"},
        {"name": "Marcus Bell",       "email": "marcus.bell@email.com",    "phone": "408-555-0803", "loc": "Fremont, CA",      "title": "Field Technician",        "src": "monster"},
        # Accountant pool (Chicago)
        {"name": "Patricia Flores",   "email": "p.flores@email.com",       "phone": "312-555-0501", "loc": "Chicago, IL",      "title": "Senior Accountant",       "src": "lever"},
        {"name": "Brian Scott",       "email": "brian.scott@email.com",    "phone": "312-555-0502", "loc": "Chicago, IL",      "title": "Accountant II",           "src": "lever"},
        {"name": "Megan Turner",      "email": "m.turner@email.com",       "phone": "312-555-0503", "loc": "Evanston, IL",     "title": "Staff Accountant",        "src": "lever"},
        {"name": "Alex Thompson",     "email": "alex.t@email.com",         "phone": "312-555-0504", "loc": "Chicago, IL",      "title": "Financial Analyst",       "src": "lever"},
        {"name": "Nicole Washington", "email": "n.washington@email.com",   "phone": "312-555-0505", "loc": "Chicago, IL",      "title": "Accounting Specialist",   "src": "indeed"},
        {"name": "Raymond Cho",       "email": "r.cho@email.com",          "phone": "312-555-0506", "loc": "Naperville, IL",   "title": "Bookkeeper",              "src": "indeed"},
        # Retail pool (Denver)
        {"name": "Tyrone Jackson",    "email": "tyronej@email.com",        "phone": "303-555-0201", "loc": "Denver, CO",       "title": "Shift Supervisor",        "src": "indeed"},
        {"name": "Ashley Kim",        "email": "ashley.kim@email.com",     "phone": "303-555-0202", "loc": "Denver, CO",       "title": "Retail Associate",        "src": "indeed"},
        {"name": "Robert Kim",        "email": "r.kim@email.com",          "phone": "303-555-0301", "loc": "Denver, CO",       "title": "Store Lead",              "src": "careerbuilder"},
        {"name": "Jennifer Walsh",    "email": "j.walsh@email.com",        "phone": "303-555-0302", "loc": "Littleton, CO",    "title": "Customer Service Rep",    "src": "careerbuilder"},
        {"name": "Derrick Simmons",   "email": "d.simmons@email.com",      "phone": "303-555-0303", "loc": "Aurora, CO",       "title": "Floor Lead",              "src": "monster"},
        {"name": "Amanda Price",      "email": "a.price@email.com",        "phone": "303-555-0304", "loc": "Denver, CO",       "title": "Cashier Supervisor",      "src": "monster"},
        # Java/tech pool (Remote)
        {"name": "Ethan Clark",       "email": "ethan.clark@email.com",    "phone": "512-555-0901", "loc": "Austin, TX",       "title": "Senior Java Developer",   "src": "dice"},
        {"name": "Samantha Reid",     "email": "s.reid@email.com",         "phone": "512-555-0902", "loc": "Remote",           "title": "Backend Engineer",        "src": "dice"},
        {"name": "Vijay Krishnan",    "email": "v.krishnan@email.com",     "phone": "512-555-0903", "loc": "Dallas, TX",       "title": "Java Engineer",           "src": "dice"},
        {"name": "Emily Foster",      "email": "emily.foster@email.com",   "phone": "512-555-0904", "loc": "Remote",           "title": "Software Engineer",       "src": "dice"},
        {"name": "Sophia Lee",        "email": "sophia.lee@email.com",     "phone": "650-555-0401", "loc": "Remote",           "title": "Full Stack Engineer",     "src": "greenhouse"},
        {"name": "Daniel Wu",         "email": "d.wu@email.com",           "phone": "650-555-0402", "loc": "Remote",           "title": "Senior Engineer",         "src": "greenhouse"},
        {"name": "Marcus Reed",       "email": "m.reed@email.com",         "phone": "737-555-0101", "loc": "Remote",           "title": "Java Spring Developer",   "src": "dice"},
        {"name": "Yuki Tanaka",       "email": "y.tanaka@email.com",       "phone": "737-555-0102", "loc": "San Francisco, CA","title": "Backend Software Engineer","src": "dice"},
        # CNA pool (Phoenix)
        {"name": "Gabrielle Moore",   "email": "g.moore@email.com",        "phone": "602-555-0701", "loc": "Phoenix, AZ",      "title": "CNA",                     "src": "bullhorn"},
        {"name": "Isaac Perkins",     "email": "i.perkins@email.com",      "phone": "602-555-0702", "loc": "Chandler, AZ",     "title": "Nursing Assistant",       "src": "bullhorn"},
        {"name": "Latoya Harris",     "email": "l.harris@email.com",       "phone": "602-555-0703", "loc": "Glendale, AZ",     "title": "Patient Care Aide",       "src": "indeed"},
        {"name": "Ryan Castillo",     "email": "r.castillo@email.com",     "phone": "602-555-0704", "loc": "Phoenix, AZ",      "title": "CNA",                     "src": "indeed"},
        # Data Analyst (Chicago)
        {"name": "Olivia Grant",      "email": "o.grant@email.com",        "phone": "312-555-0601", "loc": "Chicago, IL",      "title": "Data Analyst",            "src": "lever"},
        {"name": "Nathan Brooks",     "email": "n.brooks@email.com",       "phone": "312-555-0602", "loc": "Chicago, IL",      "title": "Business Intelligence Analyst","src": "lever"},
        # Duplicate across sources — same phone, slightly different name
        {"name": "Nathaniel Brooks",  "email": "nbrooks.alt@email.com",    "phone": "312-555-0602", "loc": "Chicago, IL",      "title": "BI Analyst",              "src": "indeed"},
    ]

    candidate_objs = []
    for rc in raw_candidates:
        sa = src_map.get(rc["src"])
        c = Candidate(
            source_account_id=sa.id if sa else None,
            full_name=rc["name"],
            email_hash=hash_email(rc["email"]),
            email_display_masked=mask_email(rc["email"]),
            phone_hash=hash_phone(rc["phone"]),
            phone_display_masked=mask_phone(rc["phone"]),
            location=rc["loc"],
            current_title=rc["title"],
        )
        db.add(c)
        candidate_objs.append(c)
    db.flush()

    # Unpack all 50 candidates
    (c_james, c_linda, c_carlos, c_steven, c_maria, c_james_dup,
     c_darnell, c_rosa, c_terry, c_cynthia,
     c_natalie, c_omar, c_crystal, c_hector, c_tanya, c_brianna, c_felix,
     c_michael, c_rachel_n, c_kevin, c_andre, c_priya_s, c_marcus_b,
     c_patricia, c_brian, c_megan, c_alex, c_nicole, c_raymond,
     c_tyrone, c_ashley, c_robert, c_jennifer, c_derrick, c_amanda,
     c_ethan, c_samantha, c_vijay, c_emily, c_sophia, c_daniel,
     c_marcus_r, c_yuki,
     c_gabrielle, c_isaac, c_latoya, c_ryan,
     c_olivia, c_nathan, c_nathaniel_dup) = candidate_objs

    # ── Applications ─────────────────────────────────────────────────────────
    def app(cand, role, src, raw, canonical, days_ago_applied, days_ago_active, offer=None, rejected=False):
        return Application(
            candidate_id=cand.id, job_role_id=role.id,
            source=src, raw_stage=raw, canonical_stage=canonical,
            status="active" if not rejected else "inactive",
            applied_at=now - timedelta(days=days_ago_applied),
            last_activity_at=now - timedelta(days=days_ago_active),
            offer_amount=offer,
            recruiter_owner=role.recruiter_owner,
        )

    apps = [
        # ── Warehouse (Acme Logistics) ──
        app(c_james,     role_warehouse, "indeed",        "phone screen",         "recruiter_screen",    24, 19),
        app(c_linda,     role_warehouse, "indeed",        "applied",              "applied",             22, 19),
        app(c_carlos,    role_warehouse, "indeed",        "sent to client",       "submitted_to_client", 28, 14),
        app(c_steven,    role_warehouse, "careerbuilder", "Application Received", "applied",             21, 19),
        app(c_maria,     role_warehouse, "careerbuilder", "Screened",             "recruiter_screen",    20, 19),
        app(c_james_dup, role_warehouse, "careerbuilder", "applied",              "applied",             19, 19),  # duplicate
        app(c_darnell,   role_warehouse, "indeed",        "applied",              "applied",             18, 18),
        app(c_rosa,      role_warehouse, "monster",       "new applicant",        "applied",             17, 17),
        app(c_terry,     role_warehouse, "monster",       "applied",              "applied",             16, 16),
        app(c_cynthia,   role_warehouse, "careerbuilder", "applied",              "applied",             15, 15),

        # ── Medical (Northstar) ──
        app(c_natalie,  role_medical, "bullhorn", "Approved",       "placed",              30,  5, offer=25.0),
        app(c_omar,     role_medical, "bullhorn", "Interview",      "interview_scheduled", 20, 20),  # no interview date — anomaly
        app(c_crystal,  role_medical, "bullhorn", "Submitted",      "submitted_to_client", 18, 14),
        app(c_hector,   role_medical, "bullhorn", "New Lead",       "new_lead",            10, 10),
        app(c_tanya,    role_medical, "bullhorn", "Offer Extended", "offer",               15,  2, offer=None),  # offer no amount
        app(c_brianna,  role_medical, "indeed",   "applied",        "applied",              8,  8),
        app(c_felix,    role_medical, "indeed",   "phone screen",   "recruiter_screen",     6,  4),

        # ── Robotics (Meridian) — very stale ──
        app(c_michael,  role_robotics, "greenhouse", "Phone Screen",          "recruiter_screen",    34, 24),
        app(c_rachel_n, role_robotics, "greenhouse", "Hiring Manager Review", "client_review",       32, 22),
        app(c_kevin,    role_robotics, "greenhouse", "Offer",                 "offer",               35, 21, offer=None),  # offer no amount
        app(c_andre,    role_robotics, "monster",    "screened",              "recruiter_screen",    24, 19),
        app(c_priya_s,  role_robotics, "monster",    "submitted",             "submitted_to_client", 22, 19),
        app(c_marcus_b, role_robotics, "monster",    "client review",         "client_review",       21, 19),

        # ── Accountant (Summit) ──
        app(c_patricia, role_accountant, "lever", "Hiring Manager Screen", "client_review", 15,  5),
        app(c_brian,    role_accountant, "lever", "Offer Extended",        "offer",         20,  3, offer=None),  # offer no amount
        app(c_megan,    role_accountant, "lever", "Applied",               "applied",        8,  8),
        app(c_alex,     role_accountant, "lever", "New Applicant",         "applied",        5,  5),
        app(c_nicole,   role_accountant, "indeed","applied",               "applied",        4,  4),
        app(c_raymond,  role_accountant, "indeed","applied",               "applied",        3,  3),

        # ── Retail (BluePeak) ──
        app(c_tyrone,  role_retail, "indeed",        "interview",      "interview_scheduled", 10, 3),
        app(c_ashley,  role_retail, "indeed",        "applied",        "applied",              5, 5),
        app(c_robert,  role_retail, "careerbuilder", "Sent to Client", "submitted_to_client",  8, 4),
        app(c_jennifer,role_retail, "careerbuilder", "Not Selected",   "rejected",             9, 6, rejected=True),
        app(c_derrick, role_retail, "monster",       "phone screen",   "recruiter_screen",     7, 5),
        app(c_amanda,  role_retail, "monster",       "applied",        "applied",              4, 4),

        # ── Java (BluePeak remote) ──
        app(c_ethan,    role_java, "dice",       "new applicant",    "applied",              12, 12),
        app(c_samantha, role_java, "dice",       "phone screen",     "recruiter_screen",     10,  6),
        app(c_vijay,    role_java, "dice",       "sent to client",   "submitted_to_client",   8,  4),
        app(c_emily,    role_java, "dice",       "interview",        "interview_scheduled",   6,  2),
        app(c_sophia,   role_java, "greenhouse", "Technical Screen", "recruiter_screen",      9,  5),
        app(c_daniel,   role_java, "greenhouse", "Hired",            "placed",               20,  1, offer=None),
        app(c_marcus_r, role_java, "dice",       "applied",          "applied",               3,  3),
        app(c_yuki,     role_java, "dice",       "applied",          "applied",               2,  2),

        # ── CNA (Northstar) ──
        app(c_gabrielle,role_cna, "bullhorn", "New Lead",       "new_lead",            12, 12),
        app(c_isaac,    role_cna, "bullhorn", "phone screen",   "recruiter_screen",     9,  7),
        app(c_latoya,   role_cna, "indeed",   "applied",        "applied",              6,  6),
        app(c_ryan,     role_cna, "indeed",   "Submitted",      "submitted_to_client",  5,  3),

        # ── Data Analyst (Summit) ──
        app(c_olivia,        role_analyst, "lever", "Applied",  "applied",          3, 3),
        app(c_nathan,        role_analyst, "lever", "Applied",  "applied",          2, 2),
        # Duplicate suggestion — same phone, slightly different name
        app(c_nathaniel_dup, role_analyst, "indeed","applied",  "applied",          2, 2),

        # Forklift — no applications (role open, zero activity → anomaly)
    ]

    for a in apps:
        db.add(a)
    db.commit()

    return {
        "sources_created":      len(sources),
        "companies_created":    len(companies),
        "roles_created":        len(roles_data),
        "candidates_created":   len(raw_candidates),
        "applications_created": len(apps),
    }


def reset_demo_data(db: Session) -> list:
    """Clear all data tables for a fresh seed."""
    tables = [
        "audit_logs", "report_snapshots", "anomalies", "pipeline_events",
        "applications", "candidates", "job_roles", "companies",
        "external_records", "sync_runs", "source_accounts",
    ]
    from sqlalchemy import text
    for table in tables:
        try:
            db.execute(text(f"DELETE FROM {table}"))
        except Exception:
            pass
    db.commit()
    return tables
