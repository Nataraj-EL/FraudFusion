from app.core.errors import FraudFusionError
from app.schemas.ingestion import SourceType
from app.services.parsers.af_parser import AdaptiveFrictionParser
from app.services.parsers.base import BaseParser
from app.services.parsers.ff_parser import FundFlowParser
from app.services.parsers.ph_parser import PhishingParser

_PARSER_REGISTRY: dict[SourceType, BaseParser] = {
    SourceType.ADAPTIVE_FRICTION: AdaptiveFrictionParser(),
    SourceType.FUND_FLOW: FundFlowParser(),
    SourceType.PHISHING: PhishingParser(),
}


def get_parser(source_type: SourceType) -> BaseParser:
    """Returns the parser instance for the specified SourceType."""
    if source_type not in _PARSER_REGISTRY:
        raise FraudFusionError(f"No parser registered for source type '{source_type}'")
    return _PARSER_REGISTRY[source_type]


def auto_detect_source_type(filename: str, content: str | bytes | None = None) -> SourceType:
    """
    Attempts to auto-detect source domain based on filename or content cues.
    Defaults to FUND_FLOW if .csv, or ADAPTIVE_FRICTION if .json.
    """
    fn = filename.lower()
    if "ff" in fn or "fund_flow" in fn or fn.endswith(".csv"):
        return SourceType.FUND_FLOW
    if "phish" in fn or "ph_" in fn:
        return SourceType.PHISHING
    if "af" in fn or "friction" in fn:
        return SourceType.ADAPTIVE_FRICTION

    # Check content if provided
    if content:
        text = content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content
        if "phishing" in text.lower() or "domain_similarity" in text:
            return SourceType.PHISHING
        if "session_anomaly" in text or "biometric" in text:
            return SourceType.ADAPTIVE_FRICTION

    # Default based on extension
    if fn.endswith(".csv"):
        return SourceType.FUND_FLOW
    return SourceType.ADAPTIVE_FRICTION
