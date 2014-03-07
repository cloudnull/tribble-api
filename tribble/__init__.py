# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


class SshKeyCreateFail(Exception):
    """Exception when SSH can not be created."""
    pass


class RetryError(Exception):
    """Exception on retry error."""
    pass


class NoGroupFound(Exception):
    """Exception when no group found."""
    pass


class CloudNotStopSystem(Exception):
    """Exception when the cloud API can not stop an instance."""
    pass


class WSGIServerFailure(Exception):
    """Exception when WSGI application can not start."""
    pass


class NoKnownMethod(Exception):
    """Exception when no method was found."""
    pass


class NoImageFound(Exception):
    """Exception when no image is found."""
    pass


class NoSizeFound(Exception):
    """Exception when no size is found."""
    pass


class DeadOnArival(Exception):
    """Exception when the system is DOA."""
    pass


class CantContinue(Exception):
    """Exception when the application stack can not continue."""
    pass


class NoJobToDo(Exception):
    """Exception when no job can be found."""
    pass


class ProcessFailure(Exception):
    """Exception when the application stack has a process failure."""
    pass


class EventLogger(object):
    """Respond to the write command using a logger.

    :param logger: ``func``
    :param level: ``str``
    """
    def __init__(self, logger, level='debug'):
        self.logger = logger
        self.level = level

    def write(self, msg):
        log = getattr(self.logger, self.level)
        log(msg.strip("\n"))
