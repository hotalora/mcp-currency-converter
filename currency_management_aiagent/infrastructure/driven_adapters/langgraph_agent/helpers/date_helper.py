import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

CURRENT_DATE_PLACEHOLDER = "{{CURRENT_DATE}}"
DEFAULT_TIMEZONE = "America/Bogota"


def format_current_date(timezone: str = DEFAULT_TIMEZONE) -> str:
    """Generate the current date in ISO 8601 format (year-month-day).

    Args:
        timezone: IANA timezone string (e.g., "America/Bogota", "US/Eastern").

    Returns:
        String with ISO format: "2025-07-14"

    Notes:
        - If timezone is empty or None, uses America/Bogota as default.
        - If timezone is invalid, uses America/Bogota as fallback.
    """
    if not timezone:
        logger.warning("Empty or None timezone provided, using default: %s",
                       DEFAULT_TIMEZONE)
        timezone = DEFAULT_TIMEZONE

    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        logger.error("Invalid timezone '%s', using fallback: %s",
                     timezone,
                     DEFAULT_TIMEZONE)
        tz = ZoneInfo(DEFAULT_TIMEZONE)
    current_datetime = datetime.now(tz)
    return current_datetime.strftime("%Y-%m-%d")


def resolve_current_date_placeholder(system_prompt: str,
                                     timezone: str = DEFAULT_TIMEZONE) -> str:
    """Replace all occurrences of CURRENT_DATE in the prompt
    with the current formatted date.

    Args:
        system_prompt: The system prompt, possibly containing placeholders.
        timezone: IANA timezone string for date generation.

    Returns:
        The prompt with placeholders replaced, or the original prompt
        if it does not contain the placeholder.
    """
    if CURRENT_DATE_PLACEHOLDER not in system_prompt:
        return system_prompt
    formatted_date = format_current_date(timezone)
    return system_prompt.replace(CURRENT_DATE_PLACEHOLDER, formatted_date)
