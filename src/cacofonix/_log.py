import logging


_logger = None


def setup_logging(level):
    logging.basicConfig(level=level)
    global _logger
    _logger = logging.getLogger('cacofonix')


def _log_method(name):
    def __log_method(*a, **kw):
        global _logger
        if _logger is None:
            _logger = logging
        return getattr(_logger, name)(*a, **kw)
    return __log_method


debug = _log_method('debug')
warning = _log_method('warning')
info = _log_method('info')
error = _log_method('error')
exception = _log_method('exception')
