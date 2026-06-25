from app.connectors.blocked_connector import BlockedConnector


class MonsterConnector(BlockedConnector):
    source_type = "monster"
    block_reason = (
        "Monster has no documented public employer-facing REST API for reading "
        "job postings or applicant data as of the audit date (2026-06-25)."
    )
    path_to_unblock = (
        "Contact Monster Business Development for an enterprise API partnership. "
        "No self-serve API program is currently active."
    )
    workaround = (
        "Export candidate data from the Monster Employer Center as CSV "
        "and upload via the PipelineOps CSV connector."
    )
