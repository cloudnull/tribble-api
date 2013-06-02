from sqlalchemy import and_
from tribble.operations import utils
from tribble.db.models import CloudAuth, Schematics, ConfigManager
from tribble.db.models import Instances, InstancesKeys, Zones


def post_zones(skm, zon, ssh):
    return Zones(schematic_id=skm.id,
                 schematic_runlist=zon.get('schematic_runlist'),
                 schematic_script=zon.get('schematic_script'),
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


def post_instanceskeys(pri, pub, sshu, key_data):
    return InstancesKeys(ssh_user=sshu,
                         ssh_key_pri=pri,
                         ssh_key_pub=pub,
                         key_name=key_data.get('key_name'))


def post_schematic(session, con, uid, post):
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
    return ConfigManager(
        config_key=post.get('config_key'),
        config_server=post.get('config_server'),
        config_username=post.get('config_username'),
        config_clientname=post.get('config_clientname'),
        config_validation_key=post.get('config_validation_key'))


def put_zone(session, zon, put, zput):
    zon.quantity = zput.get('quantity', zon.quantity)
    zon.image_id = zput.get('image_id', zon.image_id)
    zon.name_convention = zput.get('name_convention', zon.name_convention)
    zon.security_groups = put.get('security_groups', zon.security_groups)
    zon.inject_files = put.get('inject_files', zon.inject_files)
    zon.cloud_networks = put.get('cloud_networks', zon.cloud_networks)
    zon.cloud_init = put.get('cloud_init', zon.cloud_init)
    zon.quantity = zput.get('quantity', zon.quantity)
    zon.schematic_runlist = zput.get('schematic_runlist', zon.schematic_runlist)
    zon.schematic_script = zput.get('schematic_script', zon.schematic_script)
    zon.zone_name = zput.get('zone_name', utils.rand_string(length=20))
    zon.size_id = zput.get('size_id', zon.size_id)
    session.add(zon)
    session.flush()
    return session


def put_configmanager(session, con, skm, put):
    con.config_env = put.get('config_env', skm.config_env)
    con.config_key = put.get('config_key', skm.config_key)
    con.config_server = put.get('config_server', skm.config_server)
    con.config_username = put.get('config_username', skm.config_username)
    con.config_clientname = put.get('config_clientname',
                                    con.config_validation_clientname)
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


def put_instance(ins, put):
    return Instances(instance_id=str(ins.uuid),
                     public_ip=str(ins.public_ips),
                     private_ip=str(ins.private_ips),
                     server_name=str(ins.name),
                     zone_id=put.get('zone_id'))


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
    session.add(item)
    session.flush()
    return session


def commit_session(session):
    return session.commit()
