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
from multiprocessing import Queue
from collections import deque

import tribble


class EngineParser(object):
    def __init__(self, packet):
        self.packet = packet
        self.specs = {}

    def _get(self, *args):
        item, all_args, value = args
        self.specs[item] = self.packet.get(value, all_args.get('default'))

    def _is(self, *args):
        item, all_args, value = args
        self.specs[item] = value

    def _action(self, *args):
        item, all_args, value = args
        action = getattr(self, '_%s' % value)
        return action()

    def _required(self, *args):
        item, all_args, value = args
        if value is True and self.specs[item] is None:
            raise tribble.CantContinue(
                '"%s" is a required value but was set as None' % item
            )

    def _comma_split(self, *args):
        item, all_args, value = args
        self.specs[item] = self.specs[item].split(',')

    def _make(self, *args):
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
            'datacenter': {
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
    """removes a possible point of injection."""
    return dict([(_cx[0], _cx[1].replace('"', '\\"')) for _cx in item.items()])


def rand_string(length=15):
    """
    Generate a Random string
    """
    chr_set = string.ascii_uppercase
    output = ''
    for _ in range(length):
        output += random.choice(chr_set)
    return output


def basic_deque(iters=None):
    """
    iters="The iterable variables"
    Places interables into a deque
    """
    worker_q = deque([])
    if iters:
        for _dt in iters:
            worker_q.append(_dt)
    return worker_q


def basic_queue(iters=None):
    """
    iters="The iterable variables"
    Places interables into a deque
    """
    worker_q = Queue()
    if iters:
        for _dt in iters:
            worker_q.put(_dt)
    return worker_q


def worker_proc(job_action, num_jobs, t_args=None):
    """job_action="What function will be used".

    num_jobs="The number of jobs that will be processed"

    Requires the job_action and num_jobs variables for functionality.
    All threads produced by the worker are limited by the number of concurrency
    specified by the user. The Threads are all made active prior to them
    processing jobs.
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


def compute_workers(base_count=5):
    try:
        max_threads = (cpu_count() * base_count)
    except Exception:
        max_threads = base_count
    return max_threads


def process_threads(processes):
    """Process the built actions."""
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


def manager_dict(b_d=None):
    """OPTIONAL Variable:

    b_d = 'Base Dictionary'

    Create a shared dictionary using multiprocessing Managers
    If you use the "bd" variable you can specify a prebuilt dict
    the default is that bd=None
    """
    manager = multiprocessing.Manager()
    if b_d:
        managed_dictionary = manager.dict(b_d)
    else:
        managed_dictionary = manager.dict()
    return managed_dictionary


# ACTIVE STATE retry loop
# http://code.activestate.com/recipes/578163-retry-loop/
def retryloop(attempts, timeout=None, delay=None, backoff=1):
    """Enter the amount of retries you want to perform.

    The timeout allows the application to quit on "X".
    delay allows the loop to wait on fail. Useful for making REST calls.

    Example:
        Function for retring an action.
        for retry in retryloop(attempts=10, timeout=30, delay=1, backoff=1):
            something
            if somecondition:
                retry()
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
    """Stupid Hack For Public Cloud so that it is not overwhemled
    with instance creations.
    """
    timer = random.randrange(1, 10)
    return timer
