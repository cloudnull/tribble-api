# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import errno
import logging
import os
import signal
import socket
import ssl
import time


import eventlet
from eventlet.green import ssl as wsgi_ssl
import eventlet.greenio
from eventlet import wsgi
import greenlet

import tribble
from tribble.api import application
from tribble import info


LOG = logging.getLogger('tribble-api')


class Server(object):
    """Start an Eventlet WSGI server."""
    def __init__(self):
        """Loads the flask application."""
        self.app = application.load_routes()
        self.net_cfg = self.app.config['network']
        self.ssl_cfg = self.app.config['ssl']
        self.def_cfg = self.app.config['default']
        self.debug = self.def_cfg.get('debug_mode', False)
        self.server_socket = self._socket_bind()

        wsgi.HttpProtocol.default_request_version = "HTTP/1.0"
        self.protocol = wsgi.HttpProtocol

        pool_size = int(self.net_cfg.get('connection_pool', 1000))
        self.spawn_pool = eventlet.GreenPool(size=pool_size)

        self.active = True
        self.worker = None

        eventlet.patcher.monkey_patch()

    def _ssl_kwargs(self):
        """Check if certificate files exist.

        When using SSL this will check to see if the keyfile, certfile
        and ca_certs exist on the system in the location provided by config.
        If a ca_cert is specified the ssl.CERT_REQUIRED will be set otherwise
        ssl.CERT_NONE is set.

        :return ssl_kwargs: ``dict``
        """
        ssl_kwargs = {'server_side': True}

        cert_files = ['keyfile', 'certfile', 'ca_certs']
        for cert_file in cert_files:
            cert = self.ssl_cfg.get(cert_file)
            if cert and not os.path.exists(cert):
                raise RuntimeError("Unable to find crt_file: %s" % cert)
            if cert:
                ssl_kwargs[cert_file] = cert

        if 'ca_certs' in ssl_kwargs:
            ssl_kwargs['cert_reqs'] = ssl.CERT_REQUIRED
        else:
            ssl_kwargs['cert_reqs'] = ssl.CERT_NONE

        return ssl_kwargs

    def _socket_bind(self):
        """Bind to socket on a host.

        From network config bind_host and bind_port will be used as the socket
        the WSGI server will be bound too. The method will attempt to bind to
        the socket for 30 seconds. If the socket is unusable after 30 seconds
        an exception is raised.

        :return sock: ``object``
        """
        tcp_listener = (
            str(self.net_cfg.get('bind_host', '0.0.0.0')),
            int(self.net_cfg.get('bind_port', 5150))
        )

        wsgi_backlog = self.net_cfg.get('backlog', 128)
        if wsgi_backlog < 1:
            raise SystemExit('the backlog value must be >= 1')

        sock = None
        retry_until = time.time() + 30
        while not sock and time.time() < retry_until:
            try:
                sock = eventlet.listen(
                    tcp_listener,
                    backlog=wsgi_backlog,
                    family=socket.AF_INET
                )

                if self.ssl_cfg.get('use_ssl', False) is True:
                    sock = wsgi_ssl.wrap_socket(
                        sock, **self._ssl_kwargs()
                    )

            except socket.error as err:
                if err.args[0] != errno.EADDRINUSE:
                    raise tribble.WSGIServerFailure(
                        'Not able to bind to socket %s %s' % tcp_listener
                    )
                retry_time_left = retry_until - time.time()
                LOG.warn('Waiting for socket to become available...'
                         ' Time available for retry %s' % int(retry_time_left))
                eventlet.sleep(1)
            else:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                return sock
        else:
            raise tribble.WSGIServerFailure('Socket Bind Failure.')

    def _start(self):
        """Start the WSGI server."""
        wsgi.server(
            self.server_socket,
            self.app,
            custom_pool=self.spawn_pool,
            protocol=self.protocol,
            log=tribble.EventLogger(LOG),
        )
        self.spawn_pool.waitall()

    def start(self):
        """Start the WSGI Server worker."""
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGHUP, self.stop)
        self.worker = eventlet.spawn(self._start)
        LOG.info('%s Has started.' % info.__appname__)

    def stop(self, *args):
        """Stop the WSGI server.

        :param args: ``list``
        """
        LOG.warn('Stopping Tribble WSGI server.')
        LOG.debug(args)
        if self.worker is not None:
            # Resize pool to stop new requests from being processed
            self.spawn_pool.resize(0)
            self.worker.kill()

    def wait(self):
        """Block, until the server has stopped."""
        try:
            if self.worker is not None:
                self.worker.wait()
        except greenlet.GreenletExit:
            LOG.warn("Tribble WSGI server has stopped.")
