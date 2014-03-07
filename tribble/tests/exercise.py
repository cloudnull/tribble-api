# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import multiprocessing

import requests

from tribble.common import system_config


CONFIG = system_config.ConfigurationSetup()


def process_map():
    """Execute processes based on the provided map."""
    map = {
        'get_root': {
            'job': get_on_slash,
            'amount': 1000,
            'path': '/',
            'headers': {}
        }

    }

    for name, item in map.items():
        print('[ working on %s ]' % name)
        for _ in xrange(item['amount']):
            url = '%s%s' % (load_url(), item['path'])
            job = item['job']
            if item['headers']:
                job(url, headers=item['headers'])
            else:
                job(url)


def load_url():
    """Return API URL.

    :return: ``str``
    """
    ssl_config = CONFIG.config_args(section='ssl')
    network_config = CONFIG.config_args(section='network')

    bind_host = network_config.get('bind_host')
    bind_port = network_config.get('bind_port')
    use_ssl = ssl_config.get('use_ssl')
    if use_ssl is True:
        return 'https://%s:%s' % (bind_host, bind_port)
    else:
        return 'http://%s:%s' % (bind_host, bind_port)


def get_on_slash(url):
    """Perform a request on a URL.

    :param url: ``str``
    """
    requests.get(url)


def run():
    """Run the application."""
    default_config = CONFIG.config_args()
    workers = default_config.get('workers', 10)
    jobs = [
        multiprocessing.Process(target=process_map) for _ in range(workers)
    ]

    active_jobs = []
    for job in jobs:
        job.daemon = True
        job.start()
        active_jobs.append(job)

    for active_job in active_jobs:
        active_job.join()


if __name__ == '__main__':
    run()
