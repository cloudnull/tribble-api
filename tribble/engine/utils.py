# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import random
import string
import time
import multiprocessing
from multiprocessing import cpu_count
from multiprocessing import Process
from collections import deque

import tribble
from tribble.common import system_config


CONFIG = system_config.ConfigurationSetup()


class EngineParser(object):
    """Base class for the engine parser.

    :param packet: ``dict``
    """
    def __init__(self, packet):
        self.packet = packet
        self.specs = {}

    def _get(self, *args):
        """Get string from dict.

        :param args: ``list``
        """
        item, all_args, value = args
        self.specs[item] = self.packet.get(value, all_args.get('default'))

    def _is(self, *args):
        """Set string.

        :param args: ``list``
        """
        item, all_args, value = args
        self.specs[item] = value

    def _action(self, *args):
        """Return an action from dict.

        :param args: ``list``
        :return ``object``
        """
        item, all_args, value = args
        action = getattr(self, '_%s' % value)
        return action()

    def _required(self, *args):
        """Check if a required item is present.

        :param args: ``list``
        """
        item, all_args, value = args
        if value is True and self.specs[item] is None:
            raise tribble.CantContinue(
                '"%s" is a required value but was set as None' % item
            )

    def _comma_split(self, *args):
        """Split a string into a list which is comma separated.

        :param args: ``list``
        """
        item, all_args, value = args
        self.specs[item] = self.specs[item].split(',')

    def _make(self, *args):
        """Modify a value.

        Supported types, "upper", "lower"

        :param args: ``list``
        """
        item, all_args, value = args
        if value == 'lower':
            self.specs[item] = self.specs[item].upper()
        elif value == 'upper':
            self.specs[item] = self.specs[item].lower()

    def _run(self, init_items):
        """Parser Example:
        'required_args': {
            'ex_force_auth_url': {
                'get': 'cloud_url',
                'required': True
            },
            'ex_force_auth_version': {
                'get': 'cloud_version',
                'default': '2.0'
            },
            'region': {
                'get': 'cloud_region',
                'make': 'lower',
                'required': True
            }
        }
        """

        wait = []
        for item, arguments in init_items.items():
            for key, value in arguments.items():
                if key in ['make', 'comma_split', 'required']:
                    wait.append({key: [item, arguments, value]})
                else:
                    try:
                        action = getattr(self, '_%s' % key)
                    except AttributeError:
                        pass
                    else:
                        action(item, arguments, value)
            else:
                for last_action in wait:
                    for key in last_action:
                        try:
                            action = getattr(self, '_%s' % key)
                        except AttributeError:
                            pass
                        else:
                            action(*last_action[key])

        return self.specs


def escape_quote(item):
    """removes a possible point of injection.

    :param item: ``dict``
    :return: ``dict``
    """
    return dict([(_cx[0], _cx[1].replace('"', '\\"')) for _cx in item.items()])


def rand_string(length=15):
    """
    Generate a Random string

    :param length: ``int``
    :return: ``str``
    """
    chr_set = string.ascii_uppercase
    output = ''
    for _ in range(length):
        output += random.choice(chr_set)
    return output


def worker_proc(job_action, num_jobs, t_args=None):
    """Requires the job_action and num_jobs variables for functionality.

    All threads produced by the worker are limited by the number of concurrency
    specified by the user. The Threads are all made active prior to them
    processing jobs.

    :param job_action: ``str``
    :param num_jobs: ``int``
    :param t_args: ``object``
    """
    proc_name = '%s-Worker' % str(job_action).split()[2]
    if t_args:
        processes = deque(
            [Process(
                name=proc_name,
                target=job_action,
                args=(t_args,)
            ) for _ in range(num_jobs)]
        )
    else:
        processes = deque(
            [Process(
                name=proc_name,
                target=job_action
            ) for _ in range(num_jobs)]
        )

    process_threads(processes=processes)


def compute_workers():
    """Determine the max number of available threads.

    The workers are set in config.

    :return: ``int``
    """

    default_config = CONFIG.config_args()
    return default_config.get('workers', 10)


def process_threads(processes):
    """Process the built actions.

    :param processes: ``list``
    """
    max_threads = compute_workers()
    post_process = []
    while processes:
        jobs = len(processes)
        if jobs > max_threads:
            cpu = max_threads
        else:
            cpu = jobs

        for _ in xrange(cpu):
            try:
                _jb = processes.popleft()
                post_process.append(_jb)
                _jb.start()
            except IndexError:
                break

    for _pp in reversed(post_process):
        _pp.join()


# ACTIVE STATE retry loop
# http://code.activestate.com/recipes/578163-retry-loop/
def retryloop(attempts, timeout=None, delay=None, backoff=1):
    """Enter the amount of retries you want to perform.

    The timeout allows the application to quit on "X".
    delay allows the loop to wait on fail. Useful for making REST calls.

    Example: Function for retring an action.
    >>> for retry in retryloop(attempts=10, timeout=30, delay=1, backoff=1):
    ...     something()
    ...     if somecondition:
    ...         retry()

    :param attempts: ``int``
    :param timeout: ``int``
    :param delay: ``int``
    :param backoff: ``int``
    """
    starttime = time.time()
    success = set()
    for _ in range(attempts):
        success.add(True)
        yield success.clear
        if success:
            return
        duration = time.time() - starttime
        if timeout is not None and duration > timeout:
            break
        if delay:
            time.sleep(delay)
            delay = delay * backoff
    raise tribble.RetryError


def stupid_hack():
    """Randomly set a sleep time between 1 and 10 seconds."""
    timer = random.randrange(1, 10)
    return timer
