# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import traceback
import logging
import multiprocessing as multi

import kombu
from kombu.mixins import ConsumerMixin

from tribble.common import rpc
from tribble.common.db import zone_status
from tribble.engine import constructor
from tribble.engine import engine_maps
from tribble.common import system_config


CONFIG = system_config.ConfigureationSetup()
LOG = logging.getLogger('tribble-engine')


class Worker(ConsumerMixin):
    """Rip messages from Queue and then consume them."""

    def __init__(self, connection):
        """Open a worker connection for a consumer."""
        self.connection = connection
        self.active_jobs = []

    @staticmethod
    def work_doer(cell):
        """This is the "doing part of the work thread.

        Once an Item is taken out of the queue, it is processed. The first action
        of the process is to authenticate. If authentication is good the item will
        be processed. If authentication is bad, then the method will log the
        authentication failure, or raise an exception.
        """

        state = zone_status.ZoneState(cell=cell)
        deployment_manager = constructor.InstanceDeployment(packet=cell)

        try:
            job_action = engine_maps.JOBS_MAP.get(cell['job'])
            if 'enter_state' in job_action:
                enter_state = job_action['enter_state']
                state_action = getattr(state, enter_state)
                state_action()

            if 'jobs' in job_action:
                for job in job_action['jobs']:
                    action = getattr(deployment_manager, job)
                    action()

            if 'exit_state' in job_action:
                exit_state = job_action['exit_state']
                state_action = getattr(state, exit_state)
                state_action()
        except Exception as exp:
            LOG.error(traceback.format_exc())
            msg = (
                'Issues are happening while performing actions'
                ' MESSAGE: "%s"' % exp
            )
            state.error(error_msg=msg)

    def get_consumers(self, Consumer, channel):
        """Get the consumer."""
        return [
            Consumer(
                queues=[rpc.load_queues(self.connection)],
                accept=['json'],
                callbacks=[
                    self.process_task
                ]
            )
        ]

    def join_active(self):
        """Join active tasks."""
        if self.active_jobs:
            for job in self.active_jobs:
                job.join()
                self.active_jobs.remove(job)

    def _process_task(self, message):
        """Execute the code."""
        try:
            job = multi.Process(target=self.work_doer, args=(message,))
            self.active_jobs.append(job)
            job.start()
        except Exception as exp:
            LOG.error('task raised exception: %s', exp)
        else:
            self.join_active()

    def process_task(self, body, message):
        """Execute the code."""
        try:
            if message.acknowledged is not True:
                LOG.debug(message.__dict__)
                self._process_task(body)
        except Exception as exp:
            message.reject()
            LOG.error('task "%s" raised exception: "%s"', body, exp)
        else:
            message.ack()
