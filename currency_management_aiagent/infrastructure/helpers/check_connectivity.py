import asyncio
import logging
from tenacity import (retry,
                      stop_never,
                      retry_if_exception_type,
                      before_sleep_log,
                      wait_exponential)

logger = logging.getLogger(__name__)


@retry(retry=retry_if_exception_type(OSError),
       stop=stop_never,
       wait=wait_exponential(multiplier=4, min=4, max=10),
       before_sleep=before_sleep_log(logger, logging.WARNING))
async def check_connectivity(host="sts.us-east-1.amazonaws.com",
                             port=443,
                             enabled=False) -> bool:
    """Check asynchronously if there is network connectivity.

    Args:
        host: Host to check connectivity against.
        port: Port to connect to.
        enabled: If False, skip the check.

    Returns:
        True if connectivity is active.
    """
    if not enabled:
        return False
    logger.info("Checking network connectivity to %s:%d...", host, port)
    await asyncio.open_connection(host, port)
    logger.info("Network connectivity is active.")
    return True
