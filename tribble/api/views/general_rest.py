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

from tribble.api import utils
from tribble import info


mod = flask.Blueprint('general', __name__)
LOG = logging.getLogger('tribble-api')


@mod.route('/', methods=['GET'])
def index():
    """Return 200 response on GET '/'

    :return json, status: tuple
    """
    state = {'Version': info.__version__, 'Application': info.__appname__}
    LOG.debug('%s %s', flask.request.method, flask.request.path)
    return utils.return_msg(msg=state, status=200)
