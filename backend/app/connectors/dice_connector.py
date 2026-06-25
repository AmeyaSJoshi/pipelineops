from app.connectors.blocked_connector import BlockedConnector


class DiceConnector(BlockedConnector):
    source_type = "dice"
    block_reason = (
        "Dice (DHI Group) has no current public employer REST API for reading "
        "job postings or applicant data. The prior Job Seeker API has been deprecated."
    )
    path_to_unblock = (
        "Contact Dice Enterprise Sales for a data partnership arrangement. "
        "No self-serve API program is documented."
    )
    workaround = (
        "Log in to your Dice employer account, export candidate profiles as CSV, "
        "and upload via the PipelineOps CSV connector."
    )
