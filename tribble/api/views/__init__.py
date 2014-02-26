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

from flask import jsonify


LOG = logging.getLogger('tribble-api')


def not_found(message=None, error=None):
    if message:
        msg = {"error_text": message}
    else:
        msg = {"error_text": "Resource not found"}

    if error:
        LOG.warn('%s %s', msg, error)
        return jsonify(msg), error
    else:
        LOG.warn(msg)
        return jsonify(msg), 404
