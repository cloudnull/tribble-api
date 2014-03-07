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

import flask


LOG = logging.getLogger('tribble-api')


def not_found(message=None, error=None):
    """Return Message when an API request is not found.

    :param message: ``str``
    :param error: ``int``
    :return json, status: ``tuple``
    """
    if message is None:
        message = "resource not found"

    if error is None:
        error = 404

    return flask.jsonify({"response": message}), error
