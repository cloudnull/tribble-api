# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import json
import logging
import os

from tribble.engine import utils


LOG = logging.getLogger('tribble-engine')


CLIENTRB = """
log_level               :info
log_location            STDOUT
chef_server_url         '%(config_server)s'
validation_key          '/etc/chef/validation.pem'
validation_client_name  '%(config_clientname)s'
node_name               '%(node_name)s'
"""


PLACESH = """#!/usr/bin/env python
# The cloud-init-er via Python
import os
import subprocess
import httplib

url = 'www.opscode.com'
path = '/chef/install.sh'
conn = httplib.HTTPSConnection(url)
conn.request('GET', path)
resp = conn.getresponse()
r_r = resp.read()

CLIENT = \"\"\"%(client_pem)s\"\"\"
VALID = \"\"\"%(validation_pem)s\"\"\"
FIRST = \"\"\"%(first_boot_json)s\"\"\"

open('%(script_location)s', 'w').write(r_r)
subprocess.call(['/bin/bash', '%(script_location)s'])

try:
    os.remove('%(script_location)s')
except Exception:
    print('File Not Found')

try:
    os.mkdir('%(chef_directory_name)s')
except Exception:
    print('Directory Exists')

open('%(client_pem_location)s', 'w').write(CLIENT)
open('%(validation_pem_location)s', 'w').write(VALID)
open('%(first_boot_json_location)s', 'w').write(FIRST)
subprocess.call(['/usr/bin/chef-client',
                 '-j',
                 '%(first_boot_json_location)s',
                 '-c',
                 '%(client_pem_location)s',
                 '-E',
                 '%(config_env)s',
                 '-L',
                 '/var/log/chef-client.log'])
"""


class Strapper(object):
    """Get strapped for Chef Server.

    :param specs: ``dict``
    """
    def __init__(self, specs):
        self.specs = specs

    def chef_system(self):
        """Get ready to chef-client.

        :return: ``dict``
        """
        chef_dir = '/etc/chef'

        LOG.info('Making Temp File for validation PEM')
        v_file = '%(config_validation_key)s' % self.specs
        v_file_loc = os.path.join(chef_dir, 'validation.pem')

        LOG.info('Making Temp File for client.rb')
        build_crb = {
            'config_server': self.specs.get('config_server'),
            'config_clientname': self.specs.get('config_clientname'),
            'node_name': self.specs.get('node_name')
        }

        # removes a possible point of injection if string replacement has """
        c_file = CLIENTRB % utils.escape_quote(item=build_crb)
        c_file_loc = os.path.join(chef_dir, 'client.rb')

        LOG.info('Getting the installation script')
        s_file_loc = 'omnibus_install.sh'

        LOG.info('Making my First Run JSON')
        _run_list = self.specs.get('config_runlist')
        if _run_list:
            _run_list = ''.join(_run_list.split()).split(',')

        fj_file = json.dumps({"run_list": list(_run_list)})
        fj_file_loc = os.path.join(chef_dir, 'first-boot.json')

        bs_system = {
            'script_location': s_file_loc,
            'client_pem': c_file,
            'client_pem_location': c_file_loc,
            'validation_pem': v_file,
            'validation_pem_location': v_file_loc,
            'first_boot_json': fj_file,
            'first_boot_json_location': fj_file_loc,
            'chef_directory_name': chef_dir
        }
        LOG.debug('CHEF PREP ==> %s' % bs_system)
        return bs_system

    def chef_cloudinit(self):
        """Return a script string for bootstrapping a node with chef.

        :return: ``str``
        """
        chef_script = self.chef_system()
        chef_script['config_env'] = self.specs.get('config_env')
        chef_init = PLACESH % utils.escape_quote(item=chef_script)
        return chef_init
