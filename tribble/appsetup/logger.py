import logging
import logging.handlers as lhs
import os
from tribble.info import __appname__


class NoLogLevelSet(Exception):
    pass


class Logging(object):
    def __init__(self, log_level, log_file=None):
        self.log_level = log_level
        self.log_file = log_file

    def logger_setup(self):
        """
        Setup logging for your application
        """
        logger = logging.getLogger("%s" % (__appname__.upper()))

        avail_level = {'DEBUG': logging.DEBUG,
                       'INFO': logging.INFO,
                       'CRITICAL': logging.CRITICAL,
                       'WARN': logging.WARN,
                       'ERROR': logging.ERROR}

        _log_level = self.log_level.upper()
        if _log_level in avail_level:
            lvl = avail_level[_log_level]
            logger.setLevel(lvl)
            formatter = logging.Formatter("%(asctime)s - %(name)s:%(levelname)s ==>"
                                          " %(message)s")
        else:
            raise NoLogLevelSet('I died because you did not set a known log level')

        if self.log_file:
            handler = lhs.RotatingFileHandler(self.log_file,
                                              maxBytes=51200,
                                              backupCount=5)
        else:
            handler = logging.StreamHandler()

        handler.setLevel(lvl)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


def return_logfile(filename):
    """
    Return a path for logging file.

    IF "/var/log/" does not exist, or you dont have write permissions to
    "/var/log/" the log file will be in your working directory
    Check for ROOT user if not log to working directory
    """
    if os.path.isfile(filename):
        return filename
    else:
        user = os.getuid()
        logname = ('%s' % filename)
        if not user == 0:
            logfile = logname
        else:
            if os.path.isdir('/var/log'):
                log_loc = '/var/log'
                logfile = '%s/%s' % (log_loc, logname)
            else:
                try:
                    os.mkdir('%s' % log_loc)
                    logfile = '%s/%s' % (log_loc, logname)
                except Exception:
                    logfile = '%s' % logname
        return logfile


def load_in(log_level='info'):
    """
    Load in the log handler. If output is not None, systen will use the default
    Log facility.
    """
    _file = '%s.log' % __appname__
    _log_file = return_logfile(filename=_file)
    log = Logging(log_level=log_level, log_file=_log_file)
    output = log.logger_setup()
    return output
