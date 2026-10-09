import logging


def setup_logging(config: dict) -> None:
    """Set up logging configuration.

    Args:
        config: Dictionary with logger_level and logger_format keys.
    """
    logger_level = config.get("logger_level", logging.INFO)
    logger_format = config.get(
        "logger_format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.basicConfig(level=logger_level,
                        format=logger_format,
                        force=True)
