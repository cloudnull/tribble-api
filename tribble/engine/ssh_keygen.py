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
import os
import subprocess
import tempfile
import traceback

import tribble
from tribble.engine import utils


LOG = logging.getLogger('tribble-engine')


class KeyGen(object):
    """Create an SSH Public and Private Key.

    The key that is generated is saved in temp and deleted once the key's
    contents have been returned into memory.
    """
    def __init__(self):
        temp_dir = tempfile.mkdtemp()
        rand_str = utils.rand_string(length=24)
        self.sshkey = os.path.join(temp_dir, rand_str)

    def build_ssh_key(self):
        """Create an SSH KEY.

        This will use a subprocess call to create the SSH Key.

        :return: ``tuple``
        """
        try:
            LOG.info('Creating SSH Key Pair')
            # Call to BASH and create an SSH Key.
            cmd = "ssh-keygen -t rsa -f %s -N ''" % self.sshkey
            subprocess.check_call(cmd, shell=True)

            if not os.path.isfile(self.sshkey):
                raise tribble.SshKeyCreateFail('No private key created')
            else:
                with open(self.sshkey, 'rb') as private_key:
                    pri_key = private_key.read()

            if not os.path.isfile('%s.pub' % self.sshkey):
                raise tribble.SshKeyCreateFail('No public key created')
            else:
                with open('%s.pub' % self.sshkey, 'rb') as public_key:
                    pub_key = public_key.read()

        except Exception:
            LOG.info(traceback.format_exc())
            raise tribble.SshKeyCreateFail('Failed to create the SSH Keys')
        else:
            return pub_key, pri_key
        finally:
            if os.path.isfile(self.sshkey):
                os.remove(self.sshkey)
            if os.path.isfile('%s.pub' % self.sshkey):
                os.remove('%s.pub' % self.sshkey)
