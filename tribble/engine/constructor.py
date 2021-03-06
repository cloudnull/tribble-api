# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import httplib
import logging
import time
import traceback

from libcloud.compute import base
from libcloud.compute import deployment
from libcloud.compute import types

import tribble
from tribble.api import application
from tribble.common.db import db_proc
from tribble.common.db import zone_status
import tribble.engine as engine
from tribble.engine import config_manager
from tribble.engine import connection_engine
from tribble.engine import utils


LOG = logging.getLogger('tribble-engine')
DB = application.DB


class InstanceDeployment(object):
    """Perform actions based on a described application action.

    :param packet: ``dict``
    """
    def __init__(self, packet):
        self.driver = None
        self.user_data = None
        self.deployment_methods = None
        self.packet = packet
        self.user_specs = {
            'max_tries': 15,
            'timeout': 3600
        }
        self.zone_status = zone_status.ZoneState(cell=self.packet)

    def engine_setup(self):
        """Load connection engine.

        this will set the driver user_data and deployment_methods.
        """
        _engine = connection_engine.ConnectionEngine(
            packet=self.packet
        )
        self.driver, self.user_data, self.deployment_methods = _engine.run()

    def api_setup(self):
        """Ensure that all parts of the Connection Driver is setup properly."""
        if not self.driver:
            msg = 'No Available Connection'
            self.zone_status.error(error_msg=msg)
            raise base.DeploymentError(msg)

        image = self.user_specs['image'] = engine.ret_image(
            conn=self.driver, specs=self.packet
        )
        if not image:
            msg = 'No image_id found'
            self.zone_status.error(error_msg=msg)
            raise base.DeploymentError(msg)

        size = self.user_specs['size'] = engine.ret_size(
            conn=self.driver, specs=self.packet
        )
        if not size:
            msg = 'No size_id Found'
            self.zone_status.error(error_msg=msg)
            raise base.DeploymentError(msg)

        server_instances = int(self.packet.get('quantity', 1))
        utils.worker_proc(
            job_action=self._vm_constructor, num_jobs=server_instances
        )

    def _build_exception(self, node=None):
        """Log exception on build failure.

        Cleanup the failed instance if provided.

        :param node: ``object``
        """
        tb = traceback.format_exc()
        msg = '%s ==> %s' % ('Exception while Building Instance', tb)
        if node is None:
            _msg = ('Node not deleted because the system did\nnot know what'
                    ' node to delete')
            node_none_msg = '%s\n%s' % (_msg, msg)
            self.check_for_dead_nodes()
            self.zone_status.error(error_msg=node_none_msg)
        else:
            self.driver.destroy_node(node=node)
            self.zone_status.error(error_msg=msg)
        LOG.critical(msg)

    def _vm_constructor(self):
        """Build a new Instance.

        This method will build a new instance with a known provider. If the
        provider from the application map has multiple deployment methods
        this method will break on the first successful deployment method.
        """
        name_convention = self.packet.get('name_convention', 'tribble_node')
        node_name = '%s-%s'.lower() % (name_convention, utils.rand_string())
        self.packet['node_name'] = self.user_specs['name'] = node_name

        LOG.debug(self.user_specs)
        LOG.info('Building Node Based on %s' % self.user_specs)

        for dep in self.deployment_methods:
            action = getattr(self, '_%s' % dep)
            node = action(self.user_specs)
            self._node_post(info=node)

    def vm_constructor(self):
        """Build VMs."""
        self.engine_setup()
        self.api_setup()

    def vm_destroyer(self):
        """Kill an instance from information in our DB.

        When an instance is destroyed the instance will be removed from the
        configuration management system set in the zones configuration
        management table.
        """
        self.engine_setup()
        LOG.debug('Nodes to Delete %s' % self.packet['uuids'])

        try:
            node_list = self.driver.list_nodes()
        except base.LibcloudError as exp:
            self.zone_status.error(error_msg=exp)
            LOG.warn('Error When getting Node list for Deleting ==> %s' % exp)
            return False
        else:
            LOG.debug('API connected.')

        for node in node_list:
            if node.id in self.packet['uuids']:
                LOG.info('DELETING %s' % node.id)
                try:
                    time.sleep(utils.stupid_hack())
                    self.driver.destroy_node(node)
                except Exception as exp:
                    self.zone_status.error(error_msg=exp)
                    LOG.info('Node %s NOT Deleted ==> %s' % (node.id, exp))
        else:
            self._node_remove(ids=self.packet['uuids'])

    def _remove_user_data(self):
        """Return the user data.

        :return: ``object``
        """
        remove_packet = self.packet.copy()
        remove_packet['job'] = 'instance_delete'
        config = config_manager.ConfigManager(packet=remove_packet)
        return config.check_configmanager()

    def _get_user_data(self, use_ssh=False):
        """Return the user data.

        :param use_ssh: ``bol``
        :return: ``object``
        """
        config = config_manager.ConfigManager(packet=self.packet, ssh=use_ssh)
        return config.check_configmanager()

    def ssh_deploy(self):
        """Return a Libcloud deployment.MultiStepDeployment object.

        Prepare for an SSH deployment Method for any found config management
        and or scripts.

        :return: ``object``
        """
        script = '/tmp/deployment_tribble_%s.sh'
        dep_action = []

        public_key = self.packet.get('ssh_key_pub')
        if public_key:
            ssh = deployment.SSHKeyDeployment(key=public_key)
            dep_action.append(ssh)

        conf_init = self._get_user_data(use_ssh=True)
        if conf_init:
            conf_init = str(conf_init)
            con = deployment.ScriptDeployment(
                name=script % utils.rand_string(), script=conf_init
            )
            dep_action.append(con)

        if dep_action:
            return deployment.MultiStepDeployment(dep_action)

    def _ssh_deploy(self, user_specs):
        """Deploy an instance via SSH.

        :param user_specs: ``dict``
        :return: ``object``
        """
        node = None
        try:
            user_specs['deploy'] = self.ssh_deploy()
            LOG.debug('DEPLOYMENT ARGS: %s' % user_specs)
            node = self.driver.deploy_node(**user_specs)
            return self.state_wait(node=node)
        except Exception:
            self._build_exception(node)

    def _cloud_init(self, user_specs):
        """Deploy an instance via Cloud Init.

        :param user_specs: ``dict``
        :return ``object``
        """
        user_specs['ex_userdata'] = self._get_user_data()
        LOG.debug('DEPLOYMENT ARGS: %s' % user_specs)
        return self.driver.create_node(**user_specs)

    def _list_instances(self):
        """Return a list of nodes.

        :return: ``object``
        """
        return self.driver.list_nodes()

    def check_for_dead_nodes(self):
        """Look for any instances which may not be in a Running state.

        If no nodes are dead return None and if any nodes are dead, delete
        the instance. All deleted nodes will be sent for DB and configuration
        management removal.

        :return: ``object``
        """
        all_nodes = self._list_instances()
        dead_nodes = []
        name = self.user_specs['name']
        for node in all_nodes:
            if node.name == name and node.state != types.NodeState.RUNNING:
                dead_nodes.append(node)

        if not dead_nodes:
            return

        remove_node = []
        for node in dead_nodes:
            try:
                msg = 'Removing Node that failed to Build ==> %s' % node
                LOG.debug(msg)
                self.driver.destroy_node(node)
                remove_node.append(node.instance_id)
            except Exception:
                LOG.error(traceback.format_exc())
                continue

        if remove_node:
            self._node_remove(ids=remove_node)

    def state_wait(self, node):
        """Wait for a node to go to a specified state.

        Wait for an instance to go into an active state.

        :param node: ``object``
        :return: ``object``
        """
        self.zone_status.pending()
        for retry in utils.retryloop(attempts=90, timeout=1800, delay=20):
            all_nodes = self._list_instances()
            instances = [n for n in all_nodes if n.id == node.id]
            if not instances:
                raise base.DeploymentError(
                    'Instance "%s" was not found while waiting.' % node
                )
            else:
                instance = instances[0]
                state = instance.state
                node_id = instance.id

            try:
                if state == types.NodeState.PENDING:
                    msg = 'Waiting for active ==> %s' % instances
                    LOG.info(msg)
                    self.zone_status.pending(pending_msg=msg)
                    retry()
                elif state == types.NodeState.TERMINATED:
                    raise base.DeploymentError(
                        'ID:%s NAME:%s was Never Active and has since been'
                        ' Terminated' % (instance.id, instance.name)
                    )
                elif state == types.NodeState.UNKNOWN:
                    msg = (
                        'State Unknown for the instance will retry to pull'
                        ' information on %s' % instances
                    )
                    self.zone_status.pending(pending_msg=msg)
                    LOG.info(msg)
                    retry()
                else:
                    LOG.info('Instance active ==> %s' % instances)
            except tribble.RetryError as exp:
                msg = ('Error while waiting for instance %s to go active.'
                       ' => %s' % (exp, node_id))
                self.zone_status.error(error_msg=msg)
                LOG.critical(msg)
                raise base.DeploymentError(
                    'ID:%s was Never Active' % node_id
                )
            except base.DeploymentError as exp:
                msg = ('Deployment error on instance %s Error %s'
                       % (node_id, exp))
                self.zone_status.error(error_msg=msg)
                LOG.critical(msg)
            except httplib.BadStatusLine as exp:
                self.zone_status.error(error_msg=exp)
                LOG.warn(exp)
                time.sleep(utils.stupid_hack())
                retry()
            else:
                return instance

    def _node_remove(self, ids):
        """Delete an instance from both the cloud provider and from the DB.

        :param ids: ``list``
        """
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
                db_proc.delete_item(session=sess, item=instance)
        except Exception as exp:
            self.zone_status.error(error_msg=exp)
            LOG.critical('Issues when Removing Instances %s' % exp)
        else:
            db_proc.commit_session(session=sess)
            self._remove_user_data()

    def _node_post(self, info):
        """Delete an instance from both the cloud provider and from the DB.

        :param info: ``object``
        """
        try:
            sess = DB.session
            new_instance = db_proc.post_instance(ins=info, put=self.packet)
            sess = db_proc.add_item(
                session=sess, item=new_instance
            )
        except Exception as exp:
            self.zone_status.error(error_msg=exp)
            LOG.critical('Issues when Posting Instances %s' % exp)
        else:
            db_proc.commit_session(session=sess)
            LOG.info('Instance posted ID:%s NAME:%s' % (info.id, info.name))
