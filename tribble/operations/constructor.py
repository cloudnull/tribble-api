import traceback
import time
import random
from libcloud.compute.base import DeploymentError
from libcloud.compute.types import NodeState
from tribble.appsetup.start import LOG, _DB, STATS
from tribble.operations import utils
from tribble.operations import ret_conn, ret_image, ret_size
from tribble.operations import config_manager as _cm
from tribble.purveyors import db_proc


def stupid_hack():
    # Stupid Hack For Public Cloud so that it is not
    # overwhemled with instance creations
    timer = random.randrange(1, 10)
    LOG.debug('Resting for %s' % timer)
    return timer


class MainOffice(object):
    def __init__(self, nucleus):
        """
        Perform actions based on a described action
        """
        self.nucleus = nucleus

    def bob_destroyer(self):
        """
        Kill an instance from information in our DB
        """
        from tribble.purveyors.chef import cheferizer
        conn = ret_conn(nucleus=self.nucleus)
        if not conn:
            raise DeploymentError('No Available Connection')

        node_list = [_nd for _nd in conn.list_nodes()]
        LOG.debug('Nodes to Delete %s' % self.nucleus['uuids'])
        LOG.debug('All nodes in the customer API ==> %s' % node_list)
        for dim in node_list:
            if dim.id in self.nucleus['uuids']:
                LOG.info('DELETING %s' % dim.id)
                try:
                    time.sleep(stupid_hack())
                    conn.destroy_node(dim)
                except Exception, exp:
                    LOG.info('Node %s NOT Deleted ==> %s' % (dim.id, exp))
                cheferizer.ChefMe(nucleus=self.nucleus,
                                  name=dim.name.lower(),
                                  function='chefer_remove_all',
                                  logger=LOG)
        self._node_remove(ids=self.nucleus['uuids'])

    def api_setup(self):
        self.conn = ret_conn(nucleus=self.nucleus)
        if not self.conn:
            raise DeploymentError('No Available Connection')

        self.image_id = ret_image(conn=self.conn, nucleus=self.nucleus)
        if not self.image_id:
            raise DeploymentError('No image_id found')

        self.size_id = ret_size(conn=self.conn, nucleus=self.nucleus)
        if not self.size_id:
            raise DeploymentError('No size_id Found')

        utils.worker_proc(job_action=self.bob_vm_builder,
                          num_jobs=int(self.nucleus.get('quantity', 1)))

    def vm_ssh_deploy(self):
        """
        Prepaire for an SSH deployment Method for any found config
        managemnet and or scripts
        """
        from libcloud.compute.deployment import SSHKeyDeployment
        from libcloud.compute.deployment import MultiStepDeployment
        from libcloud.compute.deployment import ScriptDeployment
        dep_action = []
        if self.nucleus.get('ssh_key_pub'):
            ssh = SSHKeyDeployment(key=self.nucleus.get('ssh_key_pub'))
            dep_action.append(ssh)

        conf_init = _cm.check_configmanager(nucleus=self.nucleus, ssh=True)
        if conf_init:
            _conf_init = str(conf_init)
            LOG.debug(_conf_init)
            con = ScriptDeployment(name=('/tmp/deployment_tribble_%s.sh'
                                         % utils.rand_string()),
                                   script=_conf_init)
            dep_action.append(con)

        if self.nucleus.get('schematic_script'):
            user_script = str(self.nucleus.get('schematic_script'))
            LOG.debug(user_script)
            scr = ScriptDeployment(name=('/tmp/deployment_tribble_%s.sh'
                                         % utils.rand_string()),
                                   script=user_script)
            dep_action.append(scr)

        if dep_action > 1:
            dep = MultiStepDeployment(dep_action)
        else:
            dep = dep_action[0]
        return dep

    def bob_vm_builder(self):
        """
        Build an instance from values in our DB
        """
        time.sleep(stupid_hack())
        _node_name = '%s%s' % (self.nucleus.get('name_convention',
                                                utils.rand_string()),
                               utils.rand_string())
        node_name = _node_name.lower()
        self.nucleus['node_name'] = node_name
        specs = {'name': node_name,
                 'image': self.image_id,
                 'size': self.size_id,
                 'max_tries': 15,
                 'timeout': 1200}

        LOG.debug('Here are the specs for the build ==> %s' % specs)
        if self.nucleus['cloud_provider'].upper() in ('AMAZON',
                                                      'OPENSTACK',
                                                      'RACKSPACE'):
            if self.nucleus.get('security_groups'):
                sec_groups = self.nucleus.get('security_groups').split(',')
                specs['ex_security_groups'] = sec_groups

            if self.nucleus['cloud_provider'].upper() == 'RACKSPACE':
                specs['deploy'] = self.vm_ssh_deploy()

            if self.nucleus['cloud_provider'].upper() in ('OPENSTACK',
                                                          'AMAZON'):
                specs['ex_keyname'] = self.nucleus.get('key_name')
                userdata = _cm.check_configmanager(nucleus=self.nucleus)
                specs['ex_userdata'] = userdata
                specs['ssh_key'] = self.nucleus.get('ssh_key_pri')
                specs['ssh_username'] = self.nucleus.get('ssh_username')

            if self.nucleus['cloud_provider'].upper() in ('OPENSTACK',
                                                          'RACKSPACE'):
                if self.nucleus.get('cloud_networks'):
                    networks = self.nucleus.get('cloud_networks').split(',')
                    specs['networks'] = networks
                if self.nucleus.get('inject_files'):
                    files = self.nucleus.get('inject_files').split(',')
                    specs['ex_files'] = files
        else:
            specs['deploy'] = self.vm_ssh_deploy()
        self.vm_constructor(specs=specs)

    def vm_constructor(self, specs):
        """
        Build VMs
        """
        LOG.debug(specs)
        LOG.info('Building Node Based on %s' % specs)
        for retry in utils.retryloop(attempts=5, timeout=900, delay=10):
            try:
                time.sleep(stupid_hack())
                if 'deploy' in specs:
                    _nd = self.conn.deploy_node(**specs)
                else:
                    _nd = self.conn.create_node(**specs)
                    _nd = self.state_wait(node=_nd)
            except DeploymentError, exp:
                LOG.critical('Exception while Building Instance ==> %s' % exp)
                try:
                    time.sleep(stupid_hack())
                    dead_node = [_nd for _nd in self.conn.list_nodes()
                                 if (_nd.name == specs['name'] and
                                     _nd.state == NodeState.UNKNOWN)]
                    if dead_node:
                        for node in dead_node:
                            LOG.warn('Removing Node that failed to Build ==> %s'
                                     % node)
                            try:
                                _nd = self.conn.destroy_node(node)
                            except Exception, exp:
                                LOG.error('Node was not removed an error occured'
                                          ' ==> %s' % exp)
                    retry()
                except utils.RetryError:
                    LOG.error(traceback.format_exc())
            except Exception:
                LOG.error(traceback.format_exc())
            else:
                self._node_post(info=_nd)

    def state_wait(self, node):
        """
        Wait for a node to go to a specified state
        """
        import errno
        from httplib import BadStatusLine
        for _retry in utils.retryloop(attempts=90, timeout=1800, delay=20):
            try:
                inst = [_nd for _nd in self.conn.list_nodes() if _nd.id == node.id]
                if inst:
                    ins = inst[0]
                    if ins.state == NodeState.PENDING:
                        LOG.info('Waiting for active ==> %s' % ins)
                        _retry()
                    elif ins.state == NodeState.TERMINATED:
                        raise DeploymentError('ID:%s NAME:%s was Never Active and'
                                              ' has since been Terminated'
                                              % (node.id, node.name))
                    elif ins.state == NodeState.UNKNOWN:
                        LOG.info('State Unknown for the instance will retry'
                                 ' to pull information on %s' % ins)
                        _retry()
                    else:
                        LOG.info('Instance active ==> %s' % ins)
                        return ins
                else:
                    _retry()
            except utils.RetryError, exp:
                LOG.critical(exp)
                LOG.debug(inst)
                raise DeploymentError('ID:%s NAME:%s was Never Active'
                                      % (node.id, node.name))
            except BadStatusLine, exp:
                LOG.critical(exp)
                time.sleep(stupid_hack())
                self.conn = ret_conn(nucleus=self.nucleus)
                _retry()
            except Exception, exp:
                LOG.critical(exp)
                try:
                    if exp.errno in (errno.ECONNREFUSED, errno.ECONNRESET):
                        time.sleep(stupid_hack())
                        self.conn = ret_conn(nucleus=self.nucleus)
                        if not self.conn:
                            raise DeploymentError('No Available Connection')
                        _retry()
                except utils.RetryError, exp:
                    LOG.critical(exp)
                    LOG.debug(inst)
                    raise DeploymentError('ID:%s NAME:%s was Never Active'
                                          % (node.id, node.name))
                except Exception, exp:
                    LOG.critical(exp)
                    raise DeploymentError('ID:%s NAME:%s was Never Active'
                                          % (node.id, node.name))

    def _node_remove(self, ids):
        sess = _DB.session
        schematic = db_proc.get_schematic_id(sid=self.nucleus['schematic_id'],
                                             uid=self.nucleus['auth_id'])
        LOG.info('SCHEMATIC ==> %s' % schematic)
        zone = db_proc.get_zones_by_id(skm=schematic,
                                       zid=self.nucleus['zone_id'])
        LOG.info('ZONE ==> %s' % zone)
        LOG.info('INSTANCES ==> %s' % ids)
        inss = db_proc.get_instance_ids(zon=zone,
                                        ids=ids)
        LOG.info('INSTANCES ==> %s' % inss)
        for ins in inss:
            sess = db_proc.delete_item(session=sess, item=ins)
        db_proc.commit_session(session=sess)
        for _ in ids:
            STATS.gauge('Instances', -1, delta=True)

    def _node_post(self, info):
        atom = self.nucleus
        sess = _DB.session
        sess = db_proc.add_item(session=sess,
                                item=db_proc.post_instance(ins=info,
                                                           put=atom))
        db_proc.commit_session(session=sess)
        STATS.gauge('Instances', 1, delta=True)
        LOG.info('Instance posted ID:%s NAME:%s' % (info.id, info.name))
