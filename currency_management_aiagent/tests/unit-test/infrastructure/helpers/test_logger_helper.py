import logging
from infrastructure.helpers.logger_helper import setup_logging


def test_sets_level():
    setup_logging({"logger_level": logging.DEBUG, "logger_format": "%(message)s"})
    assert logging.getLogger().level == logging.DEBUG


def test_defaults():
    setup_logging({})
    assert logging.getLogger().level == logging.INFO


def test_custom_format():
    fmt = "%(name)s - %(message)s"
    setup_logging({"logger_level": logging.WARNING, "logger_format": fmt})
    assert logging.getLogger().level == logging.WARNING
