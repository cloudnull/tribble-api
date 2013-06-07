import traceback
import time
import random
from libcloud.compute.base import DeploymentError
from tribble.db.models import Instances
from tribble.appsetup.start import LOG
from tribble.operations import utils
from tribble.operations import ret_conn, ret_image, ret_size


def stupid_hack():
    # Stupid Hack For Public Cloud so that it is not
    # overwhemled with instance creations
    timer = random.randrange(1, 10)
    LOG.debug('Resting for %s' % timer)
    return timer


def bob_destroyer(nucleus):
    """
    Kill an instance from information in our DB

    nucleus = {'id': skm.id,
               'cloud_key': skm.cloud_key,
               'cloud_username': skm.cloud_username,
               'cloud_region': skm.cloud_region,
               'provider': skm.cloud_provider}
    """
    from tribble.operations import cheferizer
    conn = ret_conn(nucleus=nucleus)
    if not conn:
        raise DeploymentError('No Available Connection')

    node_list = [_nd for _nd in conn.list_nodes()]
    LOG.debug('Nodes to Delete %s' % nucleus['uuids'])
    LOG.debug('All nodes in the customer API ==> %s' % node_list)
    for dim in node_list:
        if dim.id in nucleus['uuids']:
            LOG.info('DELETING %s' % dim.id)
            time.sleep(stupid_hack())
            try:
                conn.destroy_node(dim)
            except Exception, exp:
                LOG.info('Node %s NOT Deleted ==> %s' % (dim.id, exp))
            cheferizer.ChefMe(nucleus=nucleus,
                              name=dim.name.lower(),
                              function='chefer_remove_all',
                              logger=LOG)


def bob_builder(nucleus):
    """
    Build an instance from values in our DB

    nucleus = {'cloud_key': skm.cloud_key,
               'cloud_username': skm.cloud_username,
               'cloud_region': skm.cloud_region,
               'quantity': zon.quantity,
               'name': '%s%s' % (zon.name_convention, rand_string()),
               'image_id': zon.image_id,
               'size_id': zon.size_id,
               'credential_id': ssh.id,
               'schematic_script': zon.schematic_script,
               'provider': skm.cloud_provider,
               'ssh_username': ssh.ssh_user,
               'ssh_key_pri': ssh.ssh_key_pri,
               'ssh_key_pub': ssh.ssh_key_pub,
               'key_name': ssh.key_name}
    """
    from tribble.operations import config_manager as _cm

    def wait_active(_nd):
        """
        Wait for a node to go active
        """
        for _retry in utils.retryloop(attempts=90, timeout=1800, delay=20):
            inst = [node for node in conn.list_nodes() if node.id == _nd.id]
            if inst:
                try:
                    ins = inst[0]
                    if not ins.state == NodeState.RUNNING:
                        LOG.info('Waiting for active ==> %s' % ins)
                        _retry()
                    else:
                        LOG.info('Waiting for active ==> %s' % ins)
                        return ins
                except utils.RetryError:
                    LOG.debug(inst)
                    raise DeploymentError('ID:%s NAME:%s was Never Active'
                                          % (_nd.id, _nd.name))

    def ssh_deploy(nucleus):
        """
        Prepaire for a deployment Method
        """
        from libcloud.compute.deployment import SSHKeyDeployment
        from libcloud.compute.deployment import MultiStepDeployment
        from libcloud.compute.deployment import ScriptDeployment
        if nucleus.get('schematic_script'):
            ssh = SSHKeyDeployment(key=nucleus.get('ssh_key_pub'))

            user_script = str(nucleus.get('schematic_script'))
            LOG.debug(user_script)
            scr = ScriptDeployment(name=('/tmp/deployment_tribble_%s.sh'
                                         % utils.rand_string()),
                                   script=user_script)

            conf_init = str(_cm.check_configmanager(nucleus=nucleus, ssh=True))
            LOG.debug(conf_init)
            con = ScriptDeployment(name=('/tmp/deployment_tribble_%s.sh'
                                         % utils.rand_string()),
                                   script=conf_init)

            dep = MultiStepDeployment([ssh, con, scr])
        else:
            dep = SSHKeyDeployment(key=nucleus.get('ssh_key_pub'))
        specs['deploy'] = dep
        return specs

    conn = ret_conn(nucleus=nucleus)
    if not conn:
        raise DeploymentError('No Available Connection')

    image_id = ret_image(conn=conn, nucleus=nucleus)
    if not image_id:
        raise DeploymentError('No image_id found')

    size_id = ret_size(conn=conn, nucleus=nucleus)
    if not size_id:
        raise DeploymentError('No size_id Found')

    time.sleep(stupid_hack())
    _node_name = '%s%s' % (nucleus.get('name_convention', utils.rand_string()),
                           utils.rand_string())
    node_name = _node_name.lower()
    nucleus['node_name'] = node_name
    specs = {'name': node_name,
             'image': image_id,
             'size': size_id,
             'max_tries': 15,
             'timeout': 1200}
    LOG.debug('Here are the specs for the build ==> %s' % specs)
    if nucleus['cloud_provider'].upper() in ('AMAZON',
                                             'OPENSTACK',
                                             'RACKSPACE'):
        if nucleus.get('security_groups'):
            sec_groups = nucleus.get('security_groups').split(',')
            specs['ex_security_groups'] = sec_groups

        if nucleus['cloud_provider'].upper() == 'RACKSPACE':
            specs = ssh_deploy(nucleus)

        if nucleus['cloud_provider'].upper() in ('OPENSTACK', 'AMAZON'):
            specs['ex_keyname'] = nucleus.get('key_name')
            specs['ex_userdata'] = _cm.check_configmanager(nucleus=nucleus)
            specs['ssh_key'] = nucleus.get('ssh_key_pri')
            specs['ssh_username'] = nucleus.get('ssh_username')

        if nucleus['cloud_provider'].upper() in ('OPENSTACK', 'RACKSPACE'):
            if nucleus.get('cloud_networks'):
                networks = nucleus.get('cloud_networks').split(',')
                specs['networks'] = networks
            if nucleus.get('inject_files'):
                files = nucleus.get('inject_files').split(',')
                specs['ex_files'] = files
    else:
        specs = ssh_deploy(nucleus)

    LOG.debug(specs)
    LOG.info('Building Node Based on %s' % specs)
    from libcloud.compute.types import NodeState
    for retry in utils.retryloop(attempts=5, timeout=900, delay=10):
        try:
            time.sleep(stupid_hack())
            if 'deploy' in specs:
                _nd = conn.deploy_node(**specs)
            else:
                _nd = conn.create_node(**specs)
                _nd = wait_active(_nd)

        except DeploymentError, exp:
            LOG.critical('Exception while Building Instance ==> %s' % exp)
            try:
                time.sleep(stupid_hack())
                dead_node = [_nd for _nd in conn.list_nodes()
                             if (_nd.name == specs['name'] and
                                 _nd.state == NodeState.UNKNOWN)]
                if dead_node:
                    for node in dead_node:
                        LOG.warn('Removing Node that failed to Build ==> %s'
                                 % node)
                        try:
                            _nd = conn.destroy_node(node)
                        except Exception, exp:
                            LOG.error('Node was not removed an error occured'
                                      ' ==> %s' % exp)
                retry()
            except utils.RetryError:
                LOG.error(traceback.format_exc())
        except Exception:
            LOG.error(traceback.format_exc())
        else:
            node_post(info=_nd, atom=nucleus)


def node_post(info, atom):
    from tribble.appsetup.start import _DB
    from tribble.purveyors import db_proc
    sess = _DB.session
    sess = db_proc.add_item(session=sess,
                            item=db_proc.post_instance(ins=info, put=atom))
    db_proc.commit_session(session=sess)
    LOG.info('Instance posted ID:%s NAME:%s' % (info.id, info.name))


def node_update(info, atom):
    """
    Put an update for a node and its information
    """
    from tribble.appsetup.start import _DB
    from tribble.purveyors import db_proc
    sess = _DB.session
    instance = db_proc.get_instance_id(zid=atom.get('zone_id'),
                                       iid=info.uuid)
    up_instance = db_proc.put_instance(session=sess,
                                       inst=instance,
                                       put=info.__dict__)
    sess = db_proc.add_item(session=sess,
                            item=up_instance)
    db_proc.commit_session(session=sess)
    LOG.info('Instance updated ID:%s NAME:%s' % (info.uuid, info.name))
