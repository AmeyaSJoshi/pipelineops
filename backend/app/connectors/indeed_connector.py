from app.connectors.blocked_connector import BlockedConnector


class IndeedConnector(BlockedConnector):
    source_type = "indeed"
    block_reason = (
        "Indeed's Publisher API has been deprecated and is closed to new partners. "
        "No official public API exists for reading employer job postings or applicant data."
    )
    path_to_unblock = (
        "Apply to the Indeed Employer Integration Partner Program. "
        "Contact: partnerprogram@indeed.com. Availability is not publicly guaranteed."
    )
    workaround = (
        "Log in to your Indeed Employer dashboard, export candidates as CSV, "
        "and upload via the PipelineOps CSV connector."
    )
