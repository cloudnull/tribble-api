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
import traceback

from tribble.common import plugin_loader
from tribble.engine import utils

LOG = logging.getLogger('tribble-engine')


SOP = """
try:
    OP_SCRIPT = \"\"\"%(op_script)s\"\"\"
    open(\"\"\"%(op_script_loc)s\"\"\", 'wb').write(OP_SCRIPT)'
    cmd = ['/bin/bash', \"\"\"%(op_script_loc)s\"\"\"]
    subprocess.check_call(cmd)
except Exception:
    print("Error When Running User Script")

"""


class ConfigManager(utils.EngineParser):
    """Build a script for use within a configuration management system.

    @inherits :class: ``utils.EngineParser.__init__``
    :param packet: ``dict``
    :param ssh: ``bol``
    """

    def __init__(self, packet, ssh=False):
        utils.EngineParser.__init__(self, packet)
        self.ssh = ssh
        self.return_action = None

    def check_configmanager(self):
        """Return configuration management data.

        Loads a plugin and then looks for available methods in the plugin.
        If the action is not None, the plugin is loaded and the information
        is returned as a dictionary.

        :return: ``dict``
        """
        try:
            LOG.info('Looking for config management')
            config_type = self.packet.get('config_type')
            if config_type is None:
                return None

            config_type = config_type.upper()
            plugin = plugin_loader.PluginLoad(config_type=config_type)
            config_manager = plugin.load_plugin

            required_args = config_manager.get('required_args')
            self._run(init_items=required_args)

            action = config_manager.get(self.packet['job'])
            if action is not None:
                self.return_action = action(self.specs, SOP, self.ssh)
        except Exception:
            LOG.error(traceback.format_exc())
        else:
            return self.return_action
