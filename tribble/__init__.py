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


class ChefSearchError(Exception):
    pass


class EventLogger(object):
    def __init__(self, logger, level='debug'):
        """Respond to the write command using a logger."""
        self.logger = logger
        self.level = level

    def write(self, msg):
        log = getattr(self.logger, self.level)
        log(msg.strip("\n"))
