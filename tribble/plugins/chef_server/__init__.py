# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from tribble.engine import utils

import chef_server
import cheferizer


def init_chefserver(*args):
    specs, sop, ssh = args
    chef = chef_server.Strapper(specs=specs)
    chef_init = chef.chef_cloudinit()
    script = specs.get('config_script')
    if script and not ssh:
        operation = {
            'op_script': str(utils.escape_quote(script)),
            'op_script_loc': '/tmp/config_script.sh'
        }
        chef_init += sop % operation
    return chef_init


def _chef_node(node_list, specs, function):
    for node in node_list:
        cheferizer.ChefMe(
            specs=specs,
            name=node.server_name,
            function=function,
        )


def chef_delete_node(*args):
    node_list = args[0].get('db_instances')
    if node_list:
        _chef_node(
            node_list=node_list, specs=args[0], function='chefer_node_remove'
        )


def chef_deploy_node(*args):
    node_list = args[0].get('db_instances')
    if node_list:
        _chef_node(
            node_list=node_list, specs=args[0], function='chefer_setup'
        )



CONFIG_APP_MAP = {
    'CHEF_SERVER': {
        'reconfig': chef_deploy_node,
        'build': init_chefserver,
        'redeploy_build': init_chefserver,
        'instance_delete': chef_delete_node,
        'required_args': {
            'config_key': {
                'get': 'config_key',
                'required': True
            },
            'config_env': {
                'get': 'config_env',
                'required': True
            },
            'config_server': {
                'get': 'config_server',
                'required': True
            },
            'config_validation_key': {
                'get': 'config_validation_key',
                'required': True
            },
            'config_clientname': {
                'get': 'config_clientname',
                'required': True
            },
            'config_runlist': {
                'get': 'config_runlist',
                'required': True
            },
            'node_name': {
                'get': 'node_name',
                'required': True
            }
        }
    }
}