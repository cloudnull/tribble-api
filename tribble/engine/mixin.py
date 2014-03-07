# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import logging
import multiprocessing as multi
import traceback

from kombu import mixins

from tribble.common.db import zone_status
from tribble.common import rpc
from tribble.common import system_config
from tribble.engine import constructor
from tribble.engine import engine_maps


CONFIG = system_config.ConfigurationSetup()
LOG = logging.getLogger('tribble-engine')


class Worker(mixins.ConsumerMixin):
    """Rip messages from Queue and then consume them.

    Open a worker connection for a consumer.

    :param connection: ``object``
    """

    def __init__(self, connection):
        self.connection = connection
        self.active_jobs = []
        self.state = None

    def work_doer(self, cell):
        """This is the "doing part of the work thread.

        Once an Item is taken out of the queue, it is processed. The first
        action of the process is to authenticate. If authentication is good
        the item will be processed. If authentication is bad, then the method
        will log the authentication failure, or raise an exception.

        :param cell: ``dict``
        """

        deployment_manager = constructor.InstanceDeployment(packet=cell)

        try:
            job_action = engine_maps.JOBS_MAP.get(cell['job'])
            if 'enter_state' in job_action:
                enter_state = job_action['enter_state']
                state_action = getattr(self.state, enter_state)
                state_action()

            if 'jobs' in job_action:
                for job in job_action['jobs']:
                    action = getattr(deployment_manager, job)
                    action()

            if 'exit_state' in job_action:
                exit_state = job_action['exit_state']
                state_action = getattr(self.state, exit_state)
                state_action()
        except Exception as exp:
            LOG.error(traceback.format_exc())
            msg = (
                'Issues are happening while performing actions'
                ' MESSAGE: "%s"' % exp
            )
            self.state.error(error_msg=msg)

    def get_consumers(self, Consumer, channel):
        """Get the consumer.

        :param Consumer: ``object``
        :param channel: ``str``
        """
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
        """Execute the code.

        :param message: ``str``
        """
        try:
            job = multi.Process(target=self.work_doer, args=(message,))
            self.active_jobs.append(job)
            job.start()
        except Exception as exp:

            LOG.error('task raised exception: %s', exp)
        else:
            self.join_active()

    def process_task(self, body, message):
        """Execute the code and ack a message once it's been processes.

        If an exception happens the message will be rejected.

        :param message: ``str``
        :param body: ``object``
        """
        try:
            self.state = zone_status.ZoneState(cell=body)
            if message.acknowledged is not True:
                LOG.debug(message.__dict__)
                self._process_task(body)
        except Exception as exp:
            message.reject()
            LOG.error('task "%s" raised exception: "%s"', body, exp)
        else:
            message.ack()
