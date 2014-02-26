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
import traceback

import kombu

from tribble.common import system_config


CONFIG = system_config.ConfigureationSetup()
RPC_CFG = CONFIG.config_args('rpc')
LOG = logging.getLogger('tribble-api')


def connect():
    """Create the connection the AMQP."""

    return kombu.Connection(
        hostname=RPC_CFG.get('host', '127.0.0.1'),
        port=RPC_CFG.get('port', 5672),
        userid=RPC_CFG.get('userid', 'guest'),
        password=RPC_CFG.get('password', 'guest'),
        virtual_host=RPC_CFG.get('virtual_host', '/')
    )


def exchange(conn):
    """Bind a connection to an exchange."""

    return kombu.Exchange(
        RPC_CFG.get('control_exchange', 'tribble'),
        type='topic',
        durable=RPC_CFG.get('durable_queues', False),
        channel=conn.channel()
    )


def declare_queue(routing_key, conn, exchange):
    """Declare working queue."""

    return kombu.Queue(
        name=routing_key,
        routing_key=routing_key,
        exchange=exchange,
        channel=conn.channel(),
        durable=RPC_CFG.get('durable_queues', False),
    ).declare()


def publisher(message, exchange, routing_key):
    """Publish Messages into AMQP."""

    try:
        msg_new = exchange.Message(
            message.body, content_type='application/json'
        )
        exchange.publish(msg_new, routing_key)
    except Exception:
        LOG.error(traceback.format_exc())
