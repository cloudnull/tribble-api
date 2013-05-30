import traceback
import time
import random
from tribble.db.models import Instances
from tribble.appsetup.start import _DB, LOG
from libcloud.compute.deployment import MultiStepDeployment, ScriptDeployment
from libcloud.compute.deployment import SSHKeyDeployment
from libcloud.compute.base import DeploymentError
from tribble.operations.cloud_auth import apiauth
from tribble.operations import utils


class NoImageFound(Exception):
    pass


class NoSizeFound(Exception):
    pass


class DeadOnArival(Exception):
    pass


def stupid_hack():
    # Stupid Hack For Public Cloud so that it is not
    # overwhemled with instance creations
    timer = random.randrange(1, 10)
    time.sleep(timer)


def bob_destroyer(nucleus):
    """
    nucleus = {'id': skm.id,
               'cloud_key': skm.cloud_key,
               'cloud_username': skm.cloud_username,
               'cloud_region': skm.cloud_region,
               'provider': skm.cloud_provider}
    """
    conn = apiauth(packet=nucleus)
    LOG.debug(nucleus['uuids'])
    nodes = [_im for _im in conn.list_nodes() if _im.uuid in nucleus['uuids']]
    LOG.debug(nodes)
    if nodes:
        stupid_hack()
        for node in nodes:
            conn.destroy_node(node)


def bob_builder(nucleus):
    """
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
    try:
        conn = apiauth(packet=nucleus)
        if not conn:
            raise DeadOnArival('No Connection Available')

        _size = [_sz for _sz in conn.list_sizes()
                 if _sz.id == nucleus.get('size')]
        if not _size:
            raise NoSizeFound('Size not found')

        _image = [_im for _im in conn.list_images()
                  if _im.id == nucleus.get('image')]
        if not _image:
            raise NoImageFound('Image not found')
    except Exception, exp:
        LOG.warn(exp)
        return False
    else:
        image = _image[0]
        size = _size[0]

    stupid_hack()

    node_name = '%s%s' % (nucleus.get('name', utils.rand_string()),
                          utils.rand_string())
    specs = {'name': node_name,
             'image': image,
             'size': size,
             'max_tries': 15,
             'timeout': 1200}

    if nucleus['provider'].upper() in ('AMAZON', 'OPENSTACK'):
        if nucleus['provider'].upper() == 'AMAZON':
            specs['ssh_key'] = nucleus.get('ssh_key_pri')
        specs['ssh_username'] = nucleus.get('ssh_username')
        specs['ex_keyname'] = nucleus.get('key_name')
    else:
        specs['deploy'] = SSHKeyDeployment(key=nucleus.get('ssh_key_pub'))

    LOG.info('Building Node Based on %s' % specs)

    for retry in utils.retryloop(attempts=5, timeout=900, delay=10):
        try:
            if 'deploy' in specs:
                _nd = conn.deploy_node(**specs)
            else:
                _nd = conn.create_node(**specs)
        except DeploymentError, exp:
            from libcloud.compute.types import NodeState
            LOG.critical('Exception while Building Instance ==> %s' % exp)
            try:
                stupid_hack()
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
                    instance_ip=str(info.public_ips),
                    server_name=str(info.name),
                    zone_id=atom.get('zone_id'))
    _DB.session.add(ins)
    _DB.session.flush()
    _DB.session.commit()
    LOG.info('Instance Built ID:%s NAME:%s' % (info.uuid, info.name))
