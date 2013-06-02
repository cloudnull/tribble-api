import traceback
import time
import random
from libcloud.compute.base import DeploymentError
from tribble.db.models import Instances
from tribble.appsetup.start import _DB, LOG
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
    conn = apiauth(packet=nucleus)
    node_list = [_nd for _nd in conn.list_nodes()]
    LOG.debug('Nodes to Delete %s' % nucleus['uuids'])
    LOG.debug('All nodes in the customer API ==> %s' % node_list)
    for dim in node_list:
        LOG.debug(dim.uuid)
        for uuid in nucleus['uuids']:
            if str(uuid) == dim.uuid:
                LOG.info('DELETING %s' % dim.id)
                time.sleep(stupid_hack())
                conn.destroy_node(dim)


def bob_builder(nucleus):
    """
    Build an instance from values in our DB

    nucleus = {'cloud_key': skm.cloud_key,
               'cloud_username': skm.cloud_username,
               'cloud_region': skm.cloud_region,
               'quantity': zon.quantity,
               'name': '%s%s' % (zon.name_convention, rand_string()),
               'image': zon.image_id,
               'size': zon.size_id,
               'credential_id': ssh.id,
               'schematic_script': zon.schematic_script,
               'provider': skm.cloud_provider,
               'ssh_username': ssh.ssh_user,
               'ssh_key_pri': ssh.ssh_key_pri,
               'ssh_key_pub': ssh.ssh_key_pub,
               'key_name': ssh.key_name}
    """
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
                        _retry()
                    else:
                        _nd = ins
                except utils.RetryError:
                    raise DeploymentError('ID:%s NAME:%s was Never Active'
                                          % (_nd.id, _nd.name))
                else:
                    LOG.debug(_nd.__dict__)

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
            scr = ScriptDeployment(name=('/tmp/deployment_tribble_%s.sh'
                                         % utils.rand_string()),
                                   script=user_script)
            dep = MultiStepDeployment([ssh, scr])
        else:
            dep = SSHKeyDeployment(key=nucleus.get('ssh_key_pub'))
        specs['deploy'] = dep
        return specs

    conn = ret_conn(nucleus=nucleus)
    if not conn:
        raise DeploymentError('No Available Connection')

    image = ret_image(conn=conn, nucleus=nucleus)
    if not image:
        raise DeploymentError('No Image found')

    size = ret_size(conn=conn, nucleus=nucleus)
    if not size:
        raise DeploymentError('No Size ID Found')

    time.sleep(stupid_hack())
    node_name = '%s%s' % (nucleus.get('name', utils.rand_string()),
                          utils.rand_string())
    specs = {'name': node_name,
             'image': image,
             'size': size,
             'max_tries': 15,
             'timeout': 1200}
    LOG.debug(specs)

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
            specs['ex_userdata'] = nucleus.get('cloud_init')
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
                wait_active(_nd)

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
                        conn.destroy_node(node)
                retry()
            except utils.RetryError:
                LOG.error(traceback.format_exc())
        except Exception:
            LOG.error(traceback.format_exc())
        else:
            node_post(info=_nd, atom=nucleus)


def node_post(info, atom):
    ins = Instances(instance_id=str(info.uuid),
                    public_ip=str(info.public_ips),
                    private_ip=str(info.private_ips),
                    server_name=str(info.name),
                    zone_id=atom.get('zone_id'))
    _DB.session.add(ins)
    _DB.session.flush()
    _DB.session.commit()
    LOG.info('Instance posted ID:%s NAME:%s' % (info.uuid, info.name))
