from sqlalchemy import and_
from tribble.db.models import Schematics, ConfigManager
from tribble.db.models import Instances, InstancesKeys, Zones


def post_zones(skm, zon, ssh):
    """
    post a new row for a zone
    """
    from tribble.operations import utils
    return Zones(schematic_id=skm.id,
                 schematic_runlist=zon.get('schematic_runlist'),
                 schematic_script=zon.get('schematic_script'),
                 zone_state=zon.get('zone_state', 'BUILT'),
                 zone_msg=zon.get('zone_msg', 'Nothing to Report'),
                 zone_name=zon.get('zone_name', utils.rand_string(length=20)),
                 security_groups=zon.get('security_groups'),
                 inject_files=zon.get('inject_files'),
                 cloud_networks=zon.get('cloud_networks'),
                 cloud_init=zon.get('cloud_init'),
                 size_id=zon.get('size_id'),
                 image_id=zon.get('image_id'),
                 name_convention=zon.get('name_convention'),
                 quantity=zon.get('quantity'),
                 credential_id=ssh.id)


def post_instanceskeys(pub, sshu, key_data):
    """
    post a new row for a set of keys to an instance
    """
    return InstancesKeys(ssh_user=sshu,
                         ssh_key_pub=pub,
                         key_name=key_data.get('key_name'))


def post_schematic(session, con, uid, post):
    """
    post a new row for a schematic
    """
    return Schematics(auth_id=uid,
                      config_id=con.id,
                      cloud_key=post.get('cloud_key'),
                      cloud_url=post.get('cloud_url'),
                      cloud_username=post.get('cloud_username'),
                      cloud_provider=post.get('cloud_provider'),
                      cloud_version=post.get('cloud_version'),
                      cloud_region=post.get('cloud_region'),
                      cloud_tenant=post.get('cloud_tenant',
                                            post.get('cloud_username')))


def post_configmanager(session, post):
    """
    post a new row for configuration management
    """
    return ConfigManager(
        config_type=post.get('config_type'),
        config_env=post.get('config_env'),
        config_key=post.get('config_key'),
        config_server=post.get('config_server'),
        config_username=post.get('config_username'),
        config_clientname=post.get('config_clientname'),
        config_validation_key=post.get('config_validation_key'))


def post_instance(ins, put):
    """
    Post information on an Instnace
    """
    return Instances(instance_id=str(ins.id),
                     public_ip=str(ins.public_ips),
                     private_ip=str(ins.private_ips),
                     server_name=str(ins.name),
                     zone_id=put.get('zone_id'))


def put_instance(session, inst, put):
    """
    Post information on an Instnace
    """
    inst.public_ip = put.get('public_ip', inst.public_ip)
    inst.private_ip = put.get('private_ip', inst.private_ip)
    inst.server_name = put.get('server_name', inst.server_name)
    session.add(inst)
    session.flush()
    return session


def put_zone(session, zon, put):
    """
    Put an update to the system for a zone
    """
    zon.image_id = put.get('image_id', zon.image_id)
    zon.name_convention = put.get('name_convention', zon.name_convention)
    zon.security_groups = put.get('security_groups', zon.security_groups)
    zon.inject_files = put.get('inject_files', zon.inject_files)
    zon.cloud_networks = put.get('cloud_networks', zon.cloud_networks)
    zon.cloud_init = put.get('cloud_init', zon.cloud_init)
    zon.quantity = put.get('quantity', zon.quantity)
    zon.schematic_runlist = put.get('schematic_runlist', zon.schematic_runlist)
    zon.schematic_script = put.get('schematic_script', zon.schematic_script)
    zon.zone_state = put.get('zone_state', zon.zone_state)
    zon.zone_msg = put.get('zone_msg', zon.zone_msg)
    zon.zone_name = put.get('zone_name', zon.zone_name)
    zon.size_id = put.get('size_id', zon.size_id)
    session.add(zon)
    session.flush()
    return session


def put_configmanager(session, con, put):
    """
    put an update to the system for a set of config management
    """
    con.config_type = put.get('config_type', con.config_type)
    con.config_env = put.get('config_env', con.config_env)
    con.config_key = put.get('config_key', con.config_key)
    con.config_server = put.get('config_server', con.config_server)
    con.config_username = put.get('config_username', con.config_username)
    con.config_clientname = put.get('config_clientname',
                                    con.config_clientname)
    con.config_validation_key = put.get('config_validation_key',
                                        con.config_validation_key)
    session.add(con)
    session.flush()
    return session


def put_schematic_id(session, skm, put):
    """
    Put an update to the system for a provided schematic
    """
    skm.cloud_key = put.get('cloud_key', skm.cloud_key)
    skm.cloud_provider = put.get('cloud_provider', skm.cloud_provider)
    skm.cloud_version = put.get('cloud_version', skm.cloud_version)
    skm.cloud_region = put.get('cloud_region', skm.cloud_region)
    skm.cloud_tenant = put.get('cloud_tenant', skm.cloud_tenant)
    skm.cloud_url = put.get('cloud_url', skm.cloud_url)
    skm.cloud_username = put.get('cloud_username', skm.cloud_username)
    session.add(skm)
    session.flush()
    return session


def put_instanceskeys(session, ssh, put):
    """
    Post information on an Instnace
    """
    ssh.ssh_user = put.get('ssh_user', ssh.ssh_user)
    ssh.ssh_key_pri = put.get('ssh_key_pri', ssh.ssh_key_pri)
    ssh.ssh_key_pub = put.get('private_ip', ssh.ssh_key_pub)
    ssh.key_name = put.get('key_name', ssh.key_name)
    session.add(ssh)
    session.flush()
    return session


def get_schematic_id(sid, uid):
    """
    Look up schematics from Schematic ID and auth ID and return it
    """
    return Schematics.query.filter(Schematics.auth_id == uid,
                                   Schematics.id == sid).first()


def get_schematics(uid):
    """
    Look up all schematics and return them as a list
    """
    return Schematics.query.filter(Schematics.auth_id == uid).all()


def get_zones(skm):
    """
    Look all zones from a provided Schematic
    """
    return Zones.query.filter(Zones.schematic_id == skm.id).all()


def get_zones_by_id(skm, zid):
    """
    Look all zones from a provided Schematic
    """
    return Zones.query.filter(Zones.schematic_id == skm.id,
                              Zones.id == zid).first()


def get_zones_by_ids(skm, zon_ids):
    """
    Look up Zones by IDs
    """
    return Zones.query.filter(and_(Zones.schematic_id == skm.id,
                                   Zones.id.in_(zon_ids))).all()


def get_configmanager(skm):
    """
    Look up a specific configuration management row from a provided schematic
    """
    return ConfigManager.query.filter(ConfigManager.id == skm.config_id).first()


def get_instances(zon):
    """
    Look up all instances for a zone and return them as a list
    """
    return Instances.query.filter(Instances.zone_id == zon.id).all()


def get_instance_id(zon, iid):
    """
    Look up an instance from a zone and the Instance ID
    """
    return Instances.query.filter(Instances.zone_id == zon.id,
                                  Instances.id == iid).first()


def get_instance_ids(zon, ids):
    """
    Look up a bunch of instances from a zone by a list of ID's
    """
    return Instances.query.filter(and_(Instances.zone_id == zon.id,
                                       Instances.instance_id.in_(ids))).all()


def get_instanceskeys(zon):
    """
    Look up keys for a zone and return them
    """
    return InstancesKeys.query.filter(
        InstancesKeys.id == zon.credential_id).first()


def delete_item(session, item):
    """
    Delete and Flush an Item
    """
    session.delete(item)
    session.flush()
    return session


def add_item(session, item):
    """
    Add something to a session and return the session
    """
    session.add(item)
    session.flush()
    return session


def commit_session(session):
    """
    Commit an active session
    """
    return session.commit()
