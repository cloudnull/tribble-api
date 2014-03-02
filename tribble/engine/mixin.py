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

    def _load_queues(self):
        """Load queues off of the set topic."""
        routing_key = '%s.info' % rpc.RPC_CFG['topic']
        exchange = self._load_exchange()
        return rpc.declare_queue(routing_key, self.connection, exchange)

    def _load_exchange(self):
        """Load RPC exchange."""
        return rpc.exchange(conn=self.connection)

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
                queues=[self._load_queues()],
                accept=['json'],
                callbacks=[
                    self.process_task,
                    self.join_active
                ]
            )
        ]

    def join_active(self):
        """Join active tasks."""
        if self.active_jobs:
            for job in self.active_jobs:
                job.join()

    def _process_task(self, message):
        """Execute the code."""
        try:
            job = multi.Process(target=self.work_doer, args=(message,))
            self.active_jobs.append(job)
            job.start()
        except Exception as exc:
            LOG.error('task raised exception: %r', exc)
        else:
            message.ack()

    def process_task(self, message):
        """Execute the code."""
        default_args = CONFIG.config_args()
        while len(self.active_jobs) <= default_args['worker']:
            if self.should_stop is False:
                break

            try:
                self._process_task(message)
            except Exception as exc:
                LOG.error('task "%s" raised exception: "%s"', (message, exc))
