# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


class RetryError(Exception):
    pass


class NoGroupFound(Exception):
    pass


class CloudNotStopSystem(Exception):
    pass


class WSGIServerFailure(Exception):
    pass


class NoKnownMethod(Exception):
    pass


class NoImageFound(Exception):
    pass


class NoSizeFound(Exception):
    pass


class DeadOnArival(Exception):
    pass


class CantContinue(Exception):
    pass


class NoJobToDo(Exception):
    pass


class ProcessFailure(Exception):
    pass


class EventLogger(object):
    def __init__(self, logger, level='debug'):
        """Respond to the write command using a logger."""
        self.logger = logger
        self.level = level

    def write(self, msg):
        log = getattr(self.logger, self.level)
        log(msg.strip("\n"))
