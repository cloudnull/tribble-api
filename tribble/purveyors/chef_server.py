import json
import os
import httplib
from StringIO import StringIO
from fabric.api import run, settings, put
from fabric.network import disconnect_all
from tribble.appsetup.start import LOG
from tribble.operations import ipsopenport


CLIENTRB = """
log_level               :info
log_location            STDOUT
chef_server_url         '%(config_server)s'
validation_key          '/etc/chef/validation.pem'
validation_client_name  '%(config_clientname)s'
node_name               '%(node_name)s'
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

    def temp_file(self):
        from tempfile import mktemp
        keyfile = mktemp()
        with open(keyfile, 'w') as _keyfile:
            _keyfile.write(self.nucleus['ssh_key_pri'])
        return keyfile

    def chef_system(self, instance):
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
                     'node_name': instance.get('name')}
        c_file = (CLIENTRB % build_crb)
        c_file_loc = '%s%sclient.rb' % (chef_dir, os.sep)

        self.logger.info('Getting the installation script')
        url = 'www.opscode.com'
        path = '/chef/install.sh'
        conn = httplib.HTTPSConnection(url)
        conn.request('GET', path)
        resp = conn.getresponse()
        r_r = resp.read()
        s_file = r_r
        s_file_loc = '/tmp/install.sh'

        LOG.info('Making my First Run JSON')
        run_list_args = self.nucleus['schematic_runlist'].split(',')
        fj_file = json.dumps({"run_list": list(run_list_args)})
        fj_file_loc = '/etc/chef/first-boot.json'

        bs_system = {'script': s_file,
                     'script_loc': s_file_loc,
                     'client': c_file,
                     'client_loc': c_file_loc,
                     'valid': v_file,
                     'valid_loc': v_file_loc,
                     'first_bt': fj_file,
                     'first_bt_loc': fj_file_loc,
                     'dirname': chef_dir}
        self.logger.debug('CHEF PREP ==> %s' % bs_system)
        return bs_system

    def fab_chef_client(self, instance):
        """
        Bootstrap Chef Client on an instance using The omibus Installer
        """
        _sd = self.chef_system(instance)
        self.logger.debug('recieved instance ==> %s' % instance)
        for host in ipsopenport(log=self.logger,
                                instance=instance,
                                nucleus=self.nucleus):
            self.logger.info('Cheferization attempt %s' % host)
            try:
                keyfile = self.temp_file()
                with settings(warn_only=True,
                              abort_on_prompts=True,
                              no_keys=True,
                              linewise=True,
                              keepalive=10,
                              combine_stderr=True,
                              connection_attempts=10,
                              disable_known_hosts=True,
                              key_filename=keyfile,
                              user=self.nucleus.get('ssh_user', 'root'),
                              port=self.nucleus.get('port', '22'),
                              host_string=host):

                    self.logger.info('Connecting to Host "%s"' % host)
                    put(StringIO('%s' % _sd['script']),
                        remote_path=_sd['script_loc'],
                        use_sudo=True)
                    self.logger.info('Using OPSCode Omnibus Installer'
                                     ' for Chef Client')
                    run("sudo bash /tmp/install.sh")

                    self.logger.info('Creating CHEF dir')
                    run("if [ ! -d '%(dirname)s' ]; then sudo mkdir -p"
                        " %(dirname)s 2>&1; else echo '%(dirname)s exists'; fi"
                        % _sd)

                    self.logger.info('Putting Validation Pem in place')
                    put(StringIO('%s' % _sd['valid']),
                        remote_path=_sd['valid_loc'],
                        use_sudo=True)

                    self.logger.info('Putting Client.rb in place')
                    put(StringIO('%s' % _sd['client']),
                        remote_path=_sd['client_loc'],
                        use_sudo=True)

                    self.logger.info('Backup Client.rb')
                    b_c = ("if [ ! -f '/etc/chef/client.rb.orig' ]; then sudo"
                           " cp /etc/chef/client.rb /etc/chef/client.rb.orig;"
                           " else echo 'backup found'; fi > /dev/null")
                    run(b_c)

                    self.logger.info('Setting the first boot JSON file')
                    put(StringIO('%s' % _sd['first_bt']),
                        remote_path=_sd['first_bt_loc'],
                        use_sudo=True)

                    self.logger.info('Making sure the log directory is present')
                    run("if [ ! -d '/var/log/chef' ]; then sudo mkdir"
                        " -p /var/log/chef; fi")

                    self.logger.info('Starting Chef')
                    run("sudo chef-client -j %s -c %s -E %s -L"
                        " /var/log/chef/chef-client.log"
                        % (_sd['first_bt_loc'],
                           _sd['client_loc'],
                           self.nucleus['config_env']))

                    # Log that the host is online
                    self.logger.info('Host "%s" is ready for action'
                                     % host)
                disconnect_all()
            except Exception, exp:
                import traceback
                LOG.critical(traceback.format_exc())
                LOG.error('%s ==> %s' % (host, exp))
            else:
                return True
            finally:
                os.remove(keyfile)
