import json
import os
from tribble.appsetup.start import LOG


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

CLIENT = \"\"\"%(client)s\"\"\"
VALID = \"\"\"%(valid)s\"\"\"
FIRST = \"\"\"%(first_bt)s\"\"\"

open('%(script_loc)s', 'w').write(r_r)
subprocess.call(['/bin/bash', '%(script_loc)s'])

try:
    os.remove('%(script_loc)s')
except Exception:
    print('File Not Found')

try:
    os.mkdir('%(dirname)s')
except Exception:
    print('Directory Exists')

open('%(client_loc)s', 'w').write(CLIENT)
open('%(valid_loc)s', 'w').write(VALID)
open('%(first_bt_loc)s', 'w').write(FIRST)
subprocess.call(['/usr/bin/chef-client',
                 '-j',
                 '%(first_bt_loc)s',
                 '-c',
                 '%(client_loc)s',
                 '-E',
                 '%(config_env)s',
                 '-L',
                 '/var/log/chef-client.log'])
"""


class ChefClientStartError(Exception):
    pass


class Strapper(object):
    def __init__(self, nucleus, logger):
        """
        Get strapped for Chef Server
        """
        self.nucleus = nucleus
        self.logger = LOG

    def escape_quote(self, item):
        return dict([(_cx[0], _cx[1].replace('"', '\\"'))
                     for _cx in item.items()])

    def temp_file(self):
        from tempfile import mktemp
        keyfile = mktemp()
        with open(keyfile, 'w') as _keyfile:
            _keyfile.write(self.nucleus['ssh_key_pri'])
        return keyfile

    def chef_system(self):
        """
        Get ready to chef
        """
        chef_dir = '/etc/chef'

        self.logger.info('Making Temp File for validation PEM')
        v_file = ('%(config_validation_key)s' % self.nucleus)
        v_file_loc = '%s%svalidation.pem' % (chef_dir, os.sep)

        self.logger.info('Making Temp File for client.rb')
        build_crb = {'config_server': self.nucleus.get('config_server'),
                     'config_clientname': self.nucleus.get('config_clientname'),
                     'node_name': self.nucleus.get('node_name')}
        # removes a possible point of injection if string replacement has """
        c_file = CLIENTRB % self.escape_quote(item=build_crb)
        c_file_loc = '%s%sclient.rb' % (chef_dir, os.sep)

        self.logger.info('Getting the installation script')
        s_file_loc = 'omnibus_install.sh'

        LOG.info('Making my First Run JSON')
        _run_list = self.nucleus.get('schematic_runlist')
        if _run_list:
            _run_list = _run_list.split(',')
        run_list_args = _run_list
        fj_file = json.dumps({"run_list": list(run_list_args)})
        fj_file_loc = '/etc/chef/first-boot.json'

        bs_system = {'script_loc': s_file_loc,
                     'client': c_file,
                     'client_loc': c_file_loc,
                     'valid': v_file,
                     'valid_loc': v_file_loc,
                     'first_bt': fj_file,
                     'first_bt_loc': fj_file_loc,
                     'dirname': chef_dir}
        self.logger.debug('CHEF PREP ==> %s' % bs_system)
        return bs_system

    def chef_cloudinit(self):
        _sd = self.chef_system()
        _sd['config_env'] = self.nucleus.get('config_env')
        # removes a possible point of injection if string replacement has """
        chef_init = PLACESH % self.escape_quote(item=_sd)
        return chef_init
