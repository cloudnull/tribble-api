CONFIG = None
QUEUE = None
LOG = None
APP = None
_DB = None
API = None


def setup_system(logger):
    """
    Take all of our globals and modify them such that they can be imported in
    other modules as preconfigured standalone variables.
    """
    global CONFIG, QUEUE, LOG, APP, _DB, API
    CONFIG = config_var()
    QUEUE = config_queue()
    LOG = logger
    APP = application(conf=CONFIG, eng=engine_config(conf=CONFIG))
    _DB, API = dbmod_apiset()


def start_worker():
    from tribble.operations import queue_worker
    from multiprocessing import Process
    Process(target=queue_worker.MainDisptach,).start()


def config_queue():
    """
    Return the general system queue
    """
    from tribble.operations.utils import basic_queue
    return basic_queue()


def config_var():
    """
    Get variables from Configuration file
    """
    from tribble.appsetup import system_config
    _config = system_config.ConfigureationSetup()
    config = _config.config_args()
    return config


def engine_config(conf):
    """
    Setup Engine URI
    """
    _eng = ('%(DB_ENGINE)s://%(DB_USERNAME)s:%(DB_PASSWORD)s'
            '@%(DB_HOST)s:%(DB_PORT)s/%(DB_NAME)s' % conf)
    return _eng


def application(conf, eng):
    """
    Setup the application
    """
    from flask import Flask
    app = Flask(__name__)
    for key in conf.keys():
        app.config[key] = conf[key]
    app.config['SQLALCHEMY_DATABASE_URI'] = eng
    app.config['SQLALCHEMY_POOL_SIZE'] = 250
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 60
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 120
    return app


def dbmod_apiset():
    from flask.ext.restful import Api
    from flask.ext.sqlalchemy import SQLAlchemy
    return [SQLAlchemy(APP), Api(APP)]


def start_server(debug=False):
    """
    Start the WSGI Server
    """
    from gevent import pywsgi, pool
    from gevent.baseserver import _tcp_listener
    from tribble import info
    from tribble.webapp import authentication, not_found
    from tribble.appsetup import restifier

    start_worker()

    if debug:
        CONFIG['debug_mode'] = True
        LOG.debug(CONFIG)
        LOG.info('Deploy Cloud Entering Debug Mode')
        APP.config['SQLALCHEMY_ECHO'] = True
        APP.debug = True

    pool = pool.Pool(int(CONFIG.get('connection_pool', 10000)))
    _tcp_listener = (str(CONFIG.get('BIND_HOST', '')),
                     int(CONFIG.get('BIND_PORT', 5150)))

    ck_file = '/etc/%s/%s' % (info.__appname__, info.__appname__)
    cert_key = (CONFIG.get('key_file', '%s.key' % ck_file),
                CONFIG.get('cert_file', '%s.crt' % ck_file))
    key, cert = cert_key
    specs = {'spawn': pool,
             'keyfile': key,
             'certfile': cert}

    restifier.routes(api=API)
    APP.errorhandler(not_found)
    APP.before_request(authentication.cloudauth)
    APP.threaded = True
    http_server = pywsgi.WSGIServer(_tcp_listener,
                                    APP,
                                    **specs)
    http_server.serve_forever()
