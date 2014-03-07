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

import flask
import flask_sqlalchemy

from tribble.api import views
from tribble.common import rpc
from tribble.common import system_config
from tribble import info


CONFIG = system_config.ConfigurationSetup()
LOG = logging.getLogger('tribble-api')
NEWRELIC = '/etc/tribble/newrelic.ini'
if os.path.exists(NEWRELIC):
    import newrelic.agent
    newrelic.agent.initialize(NEWRELIC)
    LOG.info('Newrelic Plugin Loaded')


app = flask.Flask(info.__appname__)

app.config['network'] = CONFIG.config_args(section='network')
sql_config = app.config['ssl'] = CONFIG.config_args(section='sql')
default_config = app.config['default'] = CONFIG.config_args()

if default_config.get('debug_mode', False) is True:
    app.debug = True
    app.config['SQLALCHEMY_ECHO'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = default_config['sql_connection']
app.config['SQLALCHEMY_POOL_SIZE'] = int(sql_config.get('pool_size', 250))
app.config['SQLALCHEMY_POOL_TIMEOUT'] = sql_config.get('pool_timeout', 60)
app.config['SQLALCHEMY_POOL_RECYCLE'] = sql_config.get('pool_recycle', 120)

DB = flask_sqlalchemy.SQLAlchemy(app)
DB.init_app(app)

# Load the RPC Queues
rpc.load_queues(rpc.connect())


def load_routes():
    r"""Load in the application and routes.

    The load method should only be called when the "application" module has
    already been imported by the "WSGI" server.

    :return app: ``class`` # Loaded Flask API application
    """

    app.threaded = True
    app.url_map.strict_slashes = False

    # Add in Error handling
    app.errorhandler(views.not_found)

    from tribble.api import authentication
    from tribble.api.views import general_rest
    from tribble.api.views import instances_rest
    from tribble.api.views import schematics_rest
    from tribble.api.views import zones_rest

    app.before_request(authentication.cloudauth)

    app.register_blueprint(general_rest.mod)
    app.register_blueprint(schematics_rest.mod)
    app.register_blueprint(zones_rest.mod)
    app.register_blueprint(instances_rest.mod)

    return app
