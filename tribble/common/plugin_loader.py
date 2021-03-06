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
import pkgutil

import tribble
from tribble import plugins


LOG = logging.getLogger('tribble-common')


class PluginLoad(object):
    """Load a given Configuration Management plugin.

    :param config_type: ``str``
    """

    def __init__(self, config_type):
        self.config_type = config_type

    def get_method(self, method, name):
        """Import what is required to run the System.

        :param method:
        :param name:
        """

        to_import = '%s.%s' % (method.__name__, name)
        return __import__(to_import, fromlist="None")

    def validate_plugin(self):
        """Return True if a plugin is importable.

        :return: ``bol``
        """
        try:
            self.load_plugin()
        except tribble.DeadOnArival:
            return False
        else:
            return True

    def load_plugin(self):
        """Return plugin dictionary map if it is importable.

        :return: ``dict``
        """
        for mod, name, package in pkgutil.iter_modules(plugins.__path__):
            try:
                self.config_type = self.config_type.replace('-', '_')
                method = self.get_method(method=plugins, name=name)
                if self.config_type in method.CONFIG_APP_MAP:
                    return method.CONFIG_APP_MAP[self.config_type]
            except Exception:
                msg = 'Plugin "%s" failed to load correctly' % name
                LOG.error(msg)
                raise tribble.DeadOnArival(msg)
        else:
            msg = 'No Plugin "%s" found' % self.config_type
            LOG.warn(msg)
            raise tribble.DeadOnArival(msg)
