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
import subprocess
import tempfile
import os
import traceback


LOG = logging.getLogger('tribble-engine')


class SshKeyCreateFail(Exception):
    pass


class KeyGen(object):
    def __init__(self):
        self.sshkey = tempfile.mktemp()

    def check_files(self):
        if not os.path.isfile('%s' % self.sshkey):
            return False
        elif not os.path.isfile('%s.pub' % self.sshkey):
            return False
        else:
            return True

    def build_ssh_key(self):
        """
        Create an SSH KEY if Using Rackspace Public Cloud
        """
        if not self.check_files():
            try:
                LOG.info('Creating SSH Key Pair')
                if not os.path.isfile('%s' % self.sshkey):
                    cmd = "ssh-keygen -t rsa -f %s -N ''" % self.sshkey
                    subprocess.check_call(cmd, shell=True)
                if not self.check_files():
                    raise SshKeyCreateFail(
                        'Something bad happened while making the key'
                    )
                with open('%s' % self.sshkey, 'r') as _prik:
                    pri_key = _prik.read()
                with open('%s.pub' % self.sshkey, 'r') as _pubk:
                    pub_key = _pubk.read()
            except Exception:
                LOG.info(traceback.format_exc())
            else:
                return pub_key, pri_key
            finally:
                if os.path.isfile(self.sshkey):
                    os.remove(self.sshkey)
                if os.path.isfile('%s.pub' % self.sshkey):
                    os.remove('%s.pub' % self.sshkey)
