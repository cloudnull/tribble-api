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


class TribbleBaseException(Exception):
    def __init__(self, msg):
        self.log = logging.getLogger(__name__)
        self.msg = msg

    def __enter__(self):
        self.log.error(self.msg)

    def __exit__(self, e_typ, e_val, trcbak):
        self.log.debug(e_typ, e_val, trcbak)


class RetryError(TribbleBaseException):
    def __init__(self, msg):
        super(RetryError).__init__(msg=msg)


class NoGroupFound(TribbleBaseException):
    def __init__(self, msg):
        super(NoGroupFound).__init__(msg=msg)


class CloudNotStopSystem(TribbleBaseException):
    def __init__(self, msg):
        super(CloudNotStopSystem).__init__(msg=msg)


class WSGIServerFailure(TribbleBaseException):
    def __init__(self, msg):
        super(WSGIServerFailure).__init__(msg=msg)


class NoKnownMethod(Exception):
    def __init__(self, msg):
        super(NoKnownMethod).__init__(msg=msg)


class NoImageFound(Exception):
    def __init__(self, msg):
        super(NoImageFound).__init__(msg=msg)


class NoSizeFound(Exception):
    def __init__(self, msg):
        super(NoSizeFound).__init__(msg=msg)


class DeadOnArival(Exception):
    def __init__(self, msg):
        super(DeadOnArival).__init__(msg=msg)


class CantContinue(Exception):
    def __init__(self, msg):
        super(CantContinue).__init__(msg=msg)


class NoJobToDo(Exception):
    def __init__(self, msg):
        super(NoJobToDo).__init__(msg=msg)


class ProcessFailure(Exception):
    def __init__(self, msg):
        super(ProcessFailure).__init__(msg=msg)


class EventLogger(object):
    def __init__(self, logger, level='debug'):
        """Respond to the write command using a logger."""
        self.logger = logger
        self.level = level

    def write(self, msg):
        log = getattr(self.logger, self.level)
        log(msg.strip("\n"))
