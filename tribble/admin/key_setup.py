# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os
import socket

from OpenSSL import crypto

from tribble.info import __appname__ as appname


def generate_self_signed_cert(cert_dir='/etc/%s' % appname, is_valid=True):
    """Generate a SSL certificate.

    If the cert_path and the key_path are present they will be overwritten.

    :param cert_dir: ``str``
    :param is_valid: ``bol``
    :return cert_path, key_path: ``tuple``
    """

    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    cert_path = os.path.join(cert_dir, '%s.crt' % appname)
    key_path = os.path.join(cert_dir, '%s.key' % appname)

    if os.path.exists(cert_path):
        os.unlink(cert_path)
    if os.path.exists(key_path):
        os.unlink(key_path)

    # create a key pair
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 1024)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = 'US'
    cert.get_subject().ST = 'San Antonio'
    cert.get_subject().L = 'United States'
    cert.get_subject().O = appname
    cert.get_subject().OU = 'Tribble'
    if is_valid:
        _host_name = socket.gethostname()
    else:
        _host_name = socket.gethostname()[::-1]

    cert.get_subject().CN = _host_name
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha1')

    with open(cert_path, 'wt') as _fd:
        _fd.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open(key_path, 'wt') as _fd:
        _fd.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    return cert_path, key_path
