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


def check_configmanager(nucleus, ssh=False):
    try:
        LOG.info('Looking for config management')
        config_type = nucleus.get('config_type', 'NONE').upper()
        if config_type == 'CHEF_SERVER':
            LOG.info('Chef Server has been set for config management')
            if all([nucleus.get('config_key'),
                    nucleus.get('config_env'),
                    nucleus.get('config_server'),
                    nucleus.get('config_validation_key'),
                    nucleus.get('config_clientname'),
                    nucleus.get('config_runlist')]):
                LOG.info('Chef Server is confirmed as the config management')
                return init_chefserver(nucleus=nucleus, ssh=ssh)
            else:
                return nucleus.get('cloud_init')
        else:
            return nucleus.get('cloud_init')
    except Exception:
        LOG.error(traceback.format_exc())


def init_chefserver(nucleus, ssh=False):
    from tribble.plugins.chef import chef_server
    chef = chef_server.Strapper(nucleus=nucleus)
    chef_init = chef.chef_cloudinit()
    script = nucleus.get('config_script')
    if script and not ssh:
        _op = {
            'op_script': str(utils.escape_quote(script)),
            'op_script_loc': '/tmp/config_script.sh'
        }
        chef_init += SOP % _op
    return chef_init


def chef_update_instances(nucleus):
    from tribble.plugins.chef import cheferizer
    node_list = nucleus.get('db_instances')
    if node_list:
        for dim in node_list:
            cheferizer.ChefMe(
                nucleus=nucleus,
                name=dim.server_name,
                function='chefer_setup',
                logger=LOG
            )
