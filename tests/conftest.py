from _pytest.logging import get_log_level_for_setting
import logging

pytest_plugins = "pytester"


def pytest_configure(config):
    # Some of the pytest functions used here are not officially exposed through
    # their API. We test for different pytest versions so should be OK.
    level = get_log_level_for_setting(config, "log_cli_level")
    if not level:
        level = logging.WARNING
    handler = logging.StreamHandler()
    handler.setLevel(level)
    # Set levels on the root logger. Logging events are passed up
    # the chain to the root logger, which will emit the events.
    # For this to happen, the non-root loggers need to have set 'propagate'
    # to 'True', which is the default.
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
