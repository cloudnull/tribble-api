# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from tribble.api import wsgi
from tribble.common import logger
from tribble.common import system_config


CONFIG = system_config.ConfigurationSetup()


def executable():
    """Start the Tribble API."""

    default_config = CONFIG.config_args()

    logger.logger_setup(
        name='tribble-api',
        debug_logging=default_config.get('debug_mode', False)
    )

    wsgi_server = wsgi.Server()
    wsgi_server.start()
    wsgi_server.wait()

if __name__ == '__main__':
    executable()
