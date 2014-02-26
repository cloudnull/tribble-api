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

from flask import request
from flask import jsonify

from tribble import info
from tribble.common.db import db_proc
from tribble.api.views import not_found
from tribble.common import rosetta


LOG = logging.getLogger('tribble-api')


def cloudauth():
    """Authenticates a user with the Cloud System.

    If authentication is successful, then the system will allow the user
    to deploy through the application to the provider.
    """

    def decode(cipher, key, psw):
        """Attempt a decode of a password found in the database.

        This is a place holder currently pw is in Plane text
        """

        password = rosetta.decrypt(password=key, ciphertext=cipher)
        if password == psw:
            return True
        else:
            return False

    headers = request.headers
    if not headers:
        return not_found(message='Go Away', error=400)

    auth_headers = [
        ('x-user' in headers),
        ('x-secretkey' in headers),
        ('x-password' in headers)
    ]
    if not all(auth_headers):
        if not any(auth_headers):
            state = {
                'Version': info.__version__,
                'Application': info.__appname__
            }

            LOG.debug('%s %s', request.method, request.path)
            return jsonify(state), 200
        else:
            return not_found(message='No Credentials Provided', error=401)
    else:
        try:
            secrete = decode(
                cipher=db_proc.get_user_id(headers['x-user']).dcsecret,
                key=headers['x-secretkey'],
                psw=headers['x-password']
            )
        except Exception as exp:
            msg = ('Verify x-user, x-secret, and x-password headers'
                   ' are present and correct')
            LOG.warn('Failed Authentication => Headers %s => Exception %s'
                     % (headers, exp))
            return not_found(message=msg, error=401)
        else:
            if not secrete:
                msg = 'No Valid Credentials Provided'
                return not_found(message=msg, error=401)
            else:
                LOG.debug('Authentication Success => Headers %s' % headers)
