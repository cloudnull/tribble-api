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

from tribble.engine import utils


LOG = logging.getLogger('tribble-engine')


def script_runner(*args):
    """Return a script for deployment on an instance.

    :param args: ``list``
    :return: ``str``
    """
    specs, sop, ssh = args
    config_script = specs.get('config_script')
    if config_script:
        operation = {
            'op_script': str(utils.escape_quote(config_script)),
            'op_script_loc': '/tmp/config_script.sh'
        }
        user_script = sop % operation
        LOG.debug(user_script)
        return user_script


CONFIG_APP_MAP = {
    'SCRIPT': {
        'reconfig': None,
        'build': script_runner,
        'redeploy_build': script_runner,
        'instance_delete': None,
        'required_args': {
            'node_name': {
                'get': 'node_name',
                'required': True
            }
        }
    }
}
