from app.connectors.blocked_connector import BlockedConnector


class CareerBuilderConnector(BlockedConnector):
    source_type = "careerbuilder"
    block_reason = (
        "CareerBuilder Connect API requires an approved publisher partnership agreement "
        "and is not available via self-serve signup."
    )
    path_to_unblock = (
        "Contact the CareerBuilder Partner Program at partnerprogram@careerbuilder.com. "
        "An executed MSA is required before API credentials are issued."
    )
    workaround = (
        "Export your candidate list from the CareerBuilder Employer portal as CSV "
        "and upload via the PipelineOps CSV connector."
    )
