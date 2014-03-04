# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import pkgutil

import tribble
from tribble import plugins


class PluginLoad(object):
    def __init__(self, config_type):
        self.config_type = config_type

    def get_method(self, method, name):
        """Import what is required to run the System."""

        to_import = '%s.%s' % (method.__name__, name)
        return __import__(to_import, fromlist="None")

    def validate_plugin(self):
        if self.load_plugin():
            return True

    def load_plugin(self):
        for mod, name, package in pkgutil.iter_modules(plugins.__path__):
            try:
                self.config_type = self.config_type.replace('-', '_')
                method = self.get_method(method=plugins, name=name)
                if self.config_type in method.CONFIG_APP_MAP:
                    return method.CONFIG_APP_MAP[self.config_type]
            except Exception:
                msg = 'Plugin "%s" failed to load correctly' % name
                raise tribble.DeadOnArival(msg)
        else:
            raise tribble.DeadOnArival(
                'No Plugin "%s" found' % self.config_type
            )
