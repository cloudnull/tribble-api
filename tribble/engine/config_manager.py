# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import traceback
import logging
import pkgutil

import tribble
from tribble import plugins
from tribble.engine import utils


LOG = logging.getLogger('tribble-engine')


SOP = """
try:
    OP_SCRIPT = \"\"\"%(op_script)s\"\"\"
    open(\"\"\"%(op_script_loc)s\"\"\", 'wb').write(OP_SCRIPT)'
    cmd = ['/bin/bash', \"\"\"%(op_script_loc)s\"\"\"]
    subprocess.call(cmd)
except Exception:
    print("Error When Running User Script")

"""


DEFAULT_APP = {
    'SCRIPT': {
        'required_args': {
            'node_name': {
                'get': 'node_name',
                'required': True
            }
        }
    }
}


class PluginLoad(object):
    def __init__(self, config_type):
        self.config_type = config_type

    def get_method(self, method, name):
        """Import what is required to run the System."""

        to_import = '%s.%s' % (method.__name__, name)
        return __import__(to_import, fromlist="None")

    def load_plugin(self):
        for mod, name, package in pkgutil.iter_modules(plugins.__path__):
            try:
                method = self.get_method(method=plugins, name=name)
                if self.config_type in method.CONFIG_APP_MAP:
                    return method.CONFIG_APP_MAP[self.config_type]
            except Exception:
                msg = 'Plugin %s failed to load correctly' % name
                LOG.error('%s %s' % (msg, traceback.format_exc()))
                raise tribble.DeadOnArival(msg)
            else:
                msg = '%s is loaded for config management' % self.config_type
                LOG.info(msg)


class ConfigManager(utils.EngineParser):
    def __init__(self, packet, ssh=False):
        super(ConfigManager, self).__init__(packet=packet)

        self.ssh = ssh

    def check_configmanager(self, packet):
        try:
            LOG.info('Looking for config management')
            config_type = packet.get('config_type')
            if config_type is not None:
                config_type = config_type.upper()
            plugin = PluginLoad(config_type=config_type)
            config_manager = plugin.load_plugin()
            required_args = config_manager.get('required_args')

            for item, value in required_args.items():
                spec_action = getattr(self, '_%s' % value)
                if spec_action is not None:
                    spec_action(item, value)

            action = config_manager['action']
            return action(packet=self.specs, sop=SOP, ssh=self.ssh)

        except Exception:
            LOG.error(traceback.format_exc())
