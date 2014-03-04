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
from httplib import BadStatusLine
import logging
import traceback
import time

from libcloud.compute.base import DeploymentError
from libcloud.compute.base import LibcloudError
from libcloud.compute.types import NodeState
from libcloud.compute.deployment import SSHKeyDeployment
from libcloud.compute.deployment import MultiStepDeployment
from libcloud.compute.deployment import ScriptDeployment

import tribble
import tribble.engine as engine
from tribble.api.application import DB
from tribble.common.db import db_proc
from tribble.common.db import zone_status
from tribble.plugins.chef_server import cheferizer
from tribble.engine import connection_engine
from tribble.engine import utils
from tribble.engine import config_manager


LOG = logging.getLogger('tribble-engine')


class InstanceDeployment(object):
    def __init__(self, packet):
        """Perform actions based on a described action."""

        self.driver = None
        self.user_data = None
        self.deployment_methods = None
        self.packet = packet
        self.user_specs = {
            'max_tries': 15,
            'timeout': 1200
        }
        self.zone_status = zone_status.ZoneState(cell=self.packet)

    def engine_setup(self):
        _engine = connection_engine.ConnectionEngine(
            packet=self.packet
        )
        self.driver, self.user_data, self.deployment_methods = _engine.run()

    def api_setup(self):
        self.engine_setup()

        if not self.driver:
            msg = 'No Available Connection'
            self.zone_status.error(error_msg=msg)
            raise DeploymentError(msg)

        image = self.user_specs['image'] = engine.ret_image(
            conn=self.driver, specs=self.packet
        )
        if not image:
            msg = 'No image_id found'
            self.zone_status.error(error_msg=msg)
            raise DeploymentError(msg)

        size = self.user_specs['size'] = engine.ret_size(
            conn=self.driver, specs=self.packet
        )
        if not size:
            msg = 'No size_id Found'
            self.zone_status.error(error_msg=msg)
            raise DeploymentError(msg)

        name_convention = self.packet.get('name_convention', 'tribble_node')
        node_name = '%s-%s'.lower() % (name_convention, utils.rand_string())
        self.packet['node_name'] = self.user_specs['name'] = node_name

        server_instances = int(self.packet.get('quantity', 1))
        utils.worker_proc(
            job_action=self.vm_constructor, num_jobs=server_instances
        )

    def vm_destroyer(self):
        """Kill an instance from information in our DB."""
        LOG.debug('Nodes to Delete %s' % self.packet['uuids'])

        try:
            node_list = [_nd for _nd in self.driver.list_nodes()]
        except LibcloudError, exp:
            self.zone_status.error(error_msg=exp)
            LOG.warn('Error When getting Node list for Deleting ==> %s' % exp)
            return False
        else:
            LOG.debug('All nodes in the customer API ==> %s' % node_list)

        for dim in node_list:
            if dim.id in self.packet['uuids']:
                LOG.info('DELETING %s' % dim.id)
                try:
                    time.sleep(utils.stupid_hack())
                    self.driver.destroy_node(dim)
                except Exception as exp:
                    self.zone_status.error(error_msg=exp)
                    LOG.info('Node %s NOT Deleted ==> %s' % (dim.id, exp))
                else:
                    cheferizer.ChefMe(
                        specs=self.packet,
                        name=dim.name.lower(),
                        function='chefer_remove_all',
                    )
        else:
            self._node_remove(ids=self.packet['uuids'])

    def ssh_deploy(self):
        """Prepare for an SSH deployment Method for any found config

        management and or scripts
        """
        script = '/tmp/deployment_tribble_%s.sh'
        dep_action = []

        if self.packet.get('ssh_key_pub'):
            ssh = SSHKeyDeployment(key=self.packet.get('ssh_key_pub'))
            dep_action.append(ssh)

        conf_init = config_manager.ConfigManager(packet=self.packet, ssh=True)
        if conf_init:
            conf_init = str(conf_init)
            LOG.debug(conf_init)
            con = ScriptDeployment(
                name=script % utils.rand_string(), script=conf_init
            )
            dep_action.append(con)

        if self.packet.get('config_script'):
            user_script = str(self.packet.get('config_script'))
            LOG.debug(user_script)
            con = ScriptDeployment(
                name=script % utils.rand_string(), script=user_script
            )
            dep_action.append(con)

        return MultiStepDeployment(dep_action)

    def _ssh_deploy(self, user_specs):
        node = self.driver.deploy_node(**user_specs)
        return self.state_wait(node=node)

    def _cloud_init(self, user_specs):
        return self.driver.create_node(**user_specs)

    def _list_instances(self):
        return self.driver.list_nodes()

    def vm_constructor(self):
        """Build VMs."""
        LOG.debug(self.user_specs)
        LOG.info('Building Node Based on %s' % self.user_specs)
        for deployment in self.deployment_methods:
            try:
                action = getattr(self, '_%s' % deployment)
                action(self.user_specs)
            except DeploymentError, exp:
                LOG.critical('Exception while Building Instance ==> %s' % exp)
                self.zone_status.error(error_msg=exp)
                self.check_for_dead_nodes()
            else:
                break

    def check_for_dead_nodes(self):
        all_nodes = self._list_instances()
        dead_node = [n for n in all_nodes if n.name == self.user_specs['name']]
        if not dead_node:
            return

        try:
            node = dead_node[0]
            time.sleep(utils.stupid_hack())
            msg = 'Removing Node that failed to Build ==> %s' % node
            LOG.debug(msg)
            self.driver.destroy_node(node)
        except tribble.RetryError:
            LOG.error(traceback.format_exc())
        except Exception:
            LOG.error(traceback.format_exc())
        else:
            self._node_post(info=node)

    def state_wait(self, node):
        """Wait for a node to go to a specsified state."""

        all_nodes = self._list_instances()
        for _retry in utils.retryloop(attempts=90, timeout=1800, delay=20):
            instances = [_nd for _nd in all_nodes if _nd.id == node.id]
            if not instances:
                _retry()

            try:
                instance = instances[0]
                if instance.state == NodeState.PENDING:
                    LOG.info('Waiting for active ==> %s' % instances)
                    _retry()
                elif instance.state == NodeState.TERMINATED:
                    raise DeploymentError(
                        'ID:%s NAME:%s was Never Active and has since been'
                        ' Terminated' % (node.id, node.name)
                    )
                elif instance.state == NodeState.UNKNOWN:
                    msg = (
                        'State Unknown for the instance will retry to pull'
                        ' information on %s' % instances
                    )
                    LOG.info(msg)
                    _retry()
                else:
                    LOG.info('Instance active ==> %s' % instances)
            except tribble.RetryError as exp:
                self.zone_status.error(error_msg=exp)
                LOG.critical(exp)
                raise DeploymentError(
                    'ID:%s NAME:%s was Never Active' % (node.id, node.name)
                )
            except BadStatusLine as exp:
                self.zone_status.error(error_msg=exp)
                LOG.critical(exp)
                time.sleep(utils.stupid_hack())
                _retry()
            except Exception as exp:
                self.zone_status.error(error_msg=exp)
                LOG.critical(exp)
                try:
                    if exp.errno in [errno.ECONNREFUSED, errno.ECONNRESET]:
                        time.sleep(utils.stupid_hack())
                        raise DeploymentError('No Available Connection')
                except tribble.RetryError, exp:
                    LOG.critical(exp)
                    self.zone_status.error(error_msg=exp)
                    raise DeploymentError(
                        'ID:%s NAME:%s was Never Active' % (node.id, node.name)
                    )
                except Exception as exp:
                    self.zone_status.error(error_msg=exp)
                    LOG.critical(exp)
                    raise DeploymentError(
                        'ID:%s NAME:%s was Never Active' % (node.id, node.name)
                    )
            else:
                return instance

    def _node_remove(self, ids):
        try:
            sess = DB.session
            schematic = db_proc.get_schematic_id(
                sid=self.packet['schematic_id'], uid=self.packet['auth_id']
            )
            zone = db_proc.get_zones_by_id(
                skm=schematic, zid=self.packet['zone_id']
            )
            instances = db_proc.get_instance_ids(zon=zone, ids=ids)
            for instance in instances:
                sess = db_proc.delete_item(session=sess, item=instance)
        except Exception, exp:
            self.zone_status.error(error_msg=exp)
            LOG.info('Critical Issues when Removing Instances %s' % exp)
        else:
            db_proc.commit_session(session=sess)

    def _node_post(self, info):
        try:
            sess = DB.session
            new_instance = db_proc.post_instance(ins=info, put=self.packet)
            sess = db_proc.add_item(
                session=sess, item=new_instance
            )
        except Exception, exp:
            self.zone_status.error(error_msg=exp)
            LOG.info('Critical Issues when Posting Instances %s' % exp)
        else:
            db_proc.commit_session(session=sess)
            LOG.info('Instance posted ID:%s NAME:%s' % (info.id, info.name))
