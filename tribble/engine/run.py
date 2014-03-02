# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import traceback

from tribble.common import rpc
from tribble.common import logger
from tribble.common import system_config
from tribble.engine import mixin


CONFIG = system_config.ConfigureationSetup()


def log_level(debug):
    if debug is True:
        return 'DEBUG'
    else:
        return 'INFO'


def executable():
    default_config = CONFIG.config_args()
    debug = default_config.get('debug_mode', False)
    log = logger.logger_setup(name='tribble-engine', debug_logging=debug)

    handlers = ['tribble-api', 'tribble-engine']
    rpc.setup_logging(loglevel=log_level(debug=debug), loggers=handlers)

    conn = rpc.connect()
    try:
        worker = mixin.Worker(connection=conn)
        worker.run()
    except KeyboardInterrupt:
        raise SystemExit('Process Killed.')
    except Exception:
        log.error(traceback.format_exc())
    else:
        conn.release()


if __name__ == '__main__':
    executable()
