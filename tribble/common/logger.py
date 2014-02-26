# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import logging
import logging.handlers as lhs
import os
from tribble import info


def logger_setup(name=info.__appname__, debug_logging=False, handler=False):
    """
    Setup logging for your application
    """

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s:%(module)s:%(levelname)s => %(message)s"
    )

    log = logging.getLogger(name)

    fileHandler = logging.handlers.RotatingFileHandler(
        filename=return_logfile(filename='%s.log' % name),
        maxBytes=51200,
        backupCount=5
    )

    streamHandler = logging.StreamHandler()
    if debug_logging is True:
        log.setLevel(logging.DEBUG)
        fileHandler.setLevel(logging.DEBUG)
        streamHandler.setLevel(logging.DEBUG)
    else:
        fileHandler.setLevel(logging.INFO)
        streamHandler.setLevel(logging.ERROR)

    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    log.addHandler(streamHandler)
    log.addHandler(fileHandler)

    if handler is True:
        return fileHandler
    else:
        return log


def return_logfile(filename):
    """
    Return a path for logging file.

    IF "/var/log/" does not exist, or you don't have write permissions to
    "/var/log/" the log file will be in your working directory
    Check for ROOT user if not log to working directory
    """

    if os.path.isfile(filename):
        return filename
    else:
        user = os.getuid()
        log_loc = '/var/log'
        if not user == 0:
            logfile = filename
        else:
            try:
                logfile = '%s/%s' % (log_loc, filename)
            except Exception:
                logfile = '%s' % filename
        return logfile
