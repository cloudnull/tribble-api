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
import json

import kombu
from kombu.utils.debug import setup_logging

from tribble.common import system_config


CONFIG = system_config.ConfigureationSetup()
RPC_CFG = CONFIG.config_args('rpc')
LOG = logging.getLogger('tribble-api')


def load_queues(connection):
    """Load queues off of the set topic."""
    _routing_key = get_routing_key()
    _exchange = _load_exchange(connection)
    return declare_queue(_routing_key, connection, _exchange)


def _load_exchange(connection):
    """Load RPC exchange."""
    return exchange(conn=connection)


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


def declare_queue(routing_key, conn, topic_exchange):
    """Declare working queue."""

    return_queue = kombu.Queue(
        name=routing_key,
        routing_key=routing_key,
        exchange=topic_exchange,
        channel=conn.channel(),
        durable=RPC_CFG.get('durable_queues', False),
    )
    return_queue.declare()
    return return_queue


def publisher(message, topic_exchange, routing_key):
    """Publish Messages into AMQP."""

    try:
        msg_new = topic_exchange.Message(
            json.dumps(message), content_type='application/json'
        )
        topic_exchange.publish(msg_new, routing_key)
    except Exception:
        LOG.error(traceback.format_exc())


def get_routing_key(routing_key='control_exchange'):
    return '%s.info' % RPC_CFG[routing_key]


def default_publisher(message):
    conn = connect()
    _exchange = exchange(conn)
    _routing_key = get_routing_key()
    publisher(
        message=message, topic_exchange=_exchange, routing_key=_routing_key
    )
