from sqlalchemy import and_
from tribble.purveyors import db_proc
from tribble.db.models import CloudAuth, Schematics, ConfigManager
from tribble.db.models import Instances, InstancesKeys, Zones


def post_instance(ins, put):
    """
    Post information on an Instnace
    """
    return Instances(instance_id=str(ins.get('uuid')),
                     public_ip=str(ins.get('ip_address')),
                     private_ip=None,
                     server_name=str(ins.get('server_name')),
                     zone_id=ins.get('server_map_id'))


def post_configmanager(session, post):
    """
    Look up schematics from Schematic ID and auth ID and return it as a
    Narciss Blueprint
    """
    return ConfigManager(config_env=post.get('chef_env'),
                         config_key=post.get('chef_key'),
                         config_server=post.get('chef_server'),
                         config_username=post.get('chef_username'),
                         config_clientname=post.get('validation_client_name'),
                         config_validation_key=post.get('validation_key'))


def post_schematic(session, post, con, uid):
    return Schematics(auth_id=uid,
                      config_id=con.id,
                      cloud_key=post.get('api_key'),
                      cloud_url=post.get('auth_url'),
                      cloud_username=post.get('user_name'),
                      cloud_provider=post.get('cloud_provider'),
                      cloud_version=post.get('cloud_version'),
                      cloud_region=post.get('region'),
                      cloud_tenant=post.get('tenant',
                                            post.get('cloud_username')))


def post_instanceskeys(session, post):
    from tribble.operations import fabrics
    pub, pri = fabrics.KeyGen().build_ssh_key()
    return InstancesKeys(ssh_user=post.get('ssh_user'),
                         ssh_key_pri=pri,
                         ssh_key_pub=pub,
                         key_name=post.get('key_name'))


def post_zones(session, skm, con, ssh, post):
    from tribble.operations import utils
    return Zones(schematic_id=skm.id,
                 schematic_runlist=post.get('run_list'),
                 schematic_script=post.get('schematic_script'),
                 zone_name=post.get('zone_name', utils.rand_string(length=20)),
                 security_groups=post.get('security_groups'),
                 inject_files=post.get('inject_files'),
                 cloud_networks=post.get('cloud_networks'),
                 cloud_init=post.get('cloud_init'),
                 size_id=post.get('flavor'),
                 image_id=post.get('image_ref'),
                 name_convention=post.get('name_convention'),
                 quantity=post.get('quantity'),
                 credential_id=ssh.id)


def put_zone(session, zon, put, zput):
    """
    Put an update to the system for a zone
    """
    zon.quantity = zput.get('quantity', zon.quantity)
    zon.image_id = zput.get('image_ref', zon.image_id)
    zon.name_convention = zput.get('name_convention', zon.name_convention)
    zon.security_groups = put.get('security_groups', zon.security_groups)
    zon.inject_files = put.get('inject_files', zon.inject_files)
    zon.cloud_networks = put.get('cloud_networks', zon.cloud_networks)
    zon.cloud_init = put.get('cloud_init', zon.cloud_init)
    zon.quantity = zput.get('quantity', zon.quantity)
    zon.schematic_runlist = zput.get('run_list', zon.schematic_runlist)
    zon.schematic_script = zput.get('schematic_script', zon.schematic_script)
    zon.zone_name = zput.get('zone_name', zon.zone_name)
    zon.size_id = zput.get('flavor', zon.size_id)
    session.add(zon)
    session.flush()
    return session


def put_configmanager(session, con, put):
    """
    put an update to the system for a set of config management
    """
    con.config_env = put.get('chef_env', con.config_env)
    con.config_key = put.get('chef_key', con.config_key)
    con.config_server = put.get('chef_server', con.config_server)
    con.config_username = put.get('chef_username', con.config_username)
    con.config_clientname = put.get('validation_client_name',
                                    con.config_clientname)
    con.config_validation_key = put.get('validation_key',
                                        con.config_validation_key)
    session.add(con)
    session.flush()
    return session
