# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import datetime

from sqlalchemy import and_

from tribble.engine import utils
from tribble.common.db.models import CloudAuth
from tribble.common.db.models import Schematics
from tribble.common.db.models import ConfigManager
from tribble.common.db.models import Instances
from tribble.common.db.models import InstancesKeys
from tribble.common.db.models import Zones


def post_user(admin, user, encrypted):
    """Post a new user and return the SQLAlchemy object.

    :param admin: ``int``
    :param user: ``str``
    :param encrypted ``str``
    """
    return CloudAuth(
        user_type=admin,
        dcuser=user,
        created_at=datetime.datetime.utcnow(),
        updated_at=0,
        dcsecret=encrypted
    )


def post_zones(skm, zon, ssh):
    """Post a new zone and return the SQLAlchemy object.

    :param skm: ``object`` Schematic
    :param zon: ``object`` Zone
    :param ssh ``object`` SSH
    :return: Zone: ``object``
    """
    return Zones(
        schematic_id=skm.id,
        config_runlist=zon.get('config_runlist'),
        cloud_region=zon.get('cloud_region'),
        config_script=zon.get('config_script'),
        config_env=zon.get('config_env'),
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
        credential_id=ssh.id
    )


def post_instanceskeys(pub, pri, sshu, key_name):
    """post a new set of keys to an instance and return the SQLAlchemy object.

    :param pub: ``str`` Public Key
    :param pri: ``str`` Private Key
    :param sshu ``str`` SSH User
    :param key_name: ``object``
    """
    return InstancesKeys(
        ssh_user=sshu,
        ssh_key_pub=pub,
        ssh_key_pri=pri,
        key_name=key_name
    )


def post_schematic(con, uid, post):
    """post a new row for a schematic.
    :param con: ``object``
    :param uid: ``str``
    :param post: ``dict``
    :return: ``object``
    """
    return Schematics(
        auth_id=uid,
        config_id=con.id,
        cloud_key=post.get('cloud_key'),
        cloud_url=post.get('cloud_url'),
        name=post.get('name'),
        cloud_username=post.get('cloud_username'),
        cloud_provider=post.get('cloud_provider'),
        cloud_version=post.get('cloud_version'),
        cloud_tenant=post.get('cloud_tenant', post.get('cloud_username'))
    )


def post_configmanager(post):
    """post a new row for configuration management.

    :param post: ``dict``
    :return: ``object``
    """
    return ConfigManager(
        config_type=post.get('config_type'),
        config_key=post.get('config_key'),
        config_server=post.get('config_server'),
        config_username=post.get('config_username'),
        config_clientname=post.get('config_clientname'),
        config_validation_key=post.get('config_validation_key')
    )


def post_instance(ins, put):
    """Post a new instance.

    :param ins: ``object`` Instance
    :param put: ``dict``
    :return: ``object``
    """
    return Instances(
        instance_id=str(ins.id),
        public_ip=str(ins.public_ips),
        private_ip=str(ins.private_ips),
        server_name=str(ins.name),
        zone_id=put.get('zone_id')
    )


def put_instance(session, inst, put):
    """Post information on an Instance and return the open SQLAlchemy session.

    :param session: ``object``
    :param inst: ``object``
    :param put: ``dict``
    :return: ``object``
    """
    inst.public_ip = put.get('public_ip', inst.public_ip)
    inst.private_ip = put.get('private_ip', inst.private_ip)
    inst.server_name = put.get('server_name', inst.server_name)
    session.flush()
    return session


def put_zone(session, zon, put):
    """Put an update to a zone and return the open SQLAlchemy session.

    :param session: ``object``
    :param zon: ``object``
    :param put: ``dict``
    :return: ``object``
    """
    zon.image_id = put.get('image_id', zon.image_id)
    zon.name_convention = put.get('name_convention', zon.name_convention)
    zon.cloud_region = put.get('cloud_region', zon.cloud_region)
    zon.security_groups = put.get('security_groups', zon.security_groups)
    zon.inject_files = put.get('inject_files', zon.inject_files)
    zon.cloud_networks = put.get('cloud_networks', zon.cloud_networks)
    zon.cloud_init = put.get('cloud_init', zon.cloud_init)
    zon.quantity = put.get('quantity', zon.quantity)
    zon.config_runlist = put.get('config_runlist', zon.config_runlist)
    zon.config_script = put.get('config_script', zon.config_script)
    zon.config_env = put.get('config_env', zon.config_env)
    zon.zone_state = put.get('zone_state', zon.zone_state)
    zon.zone_msg = put.get('zone_msg', zon.zone_msg)
    zon.zone_name = put.get('zone_name', zon.zone_name)
    zon.size_id = put.get('size_id', zon.size_id)
    session.flush()
    return session


def put_configmanager(session, con, put):
    """put an update to the system for a set of config management.

    :param session: ``object``
    :param con: ``object``
    :param put: ``dict``
    :return: ``object``
    """
    con.config_type = put.get('config_type', con.config_type)
    con.config_key = put.get('config_key', con.config_key)
    con.config_server = put.get('config_server', con.config_server)
    con.config_username = put.get('config_username', con.config_username)
    con.config_clientname = put.get(
        'config_clientname',
        con.config_clientname
    )
    con.config_validation_key = put.get(
        'config_validation_key',
        con.config_validation_key
    )
    session.flush()
    return session


def put_schematic_id(session, skm, put):
    """Put an update to the system for a provided schematic.

    :param session: ``object``
    :param skm: ``object``
    :param put: ``dict``
    :return: ``object``
    """
    skm.cloud_key = put.get('cloud_key', skm.cloud_key)
    skm.cloud_provider = put.get('cloud_provider', skm.cloud_provider)
    skm.cloud_version = put.get('cloud_version', skm.cloud_version)
    skm.cloud_tenant = put.get('cloud_tenant', skm.cloud_tenant)
    skm.cloud_url = put.get('cloud_url', skm.cloud_url)
    skm.cloud_username = put.get('cloud_username', skm.cloud_username)
    skm.name = put.get('name', skm.name)
    session.flush()
    return session


def put_instanceskeys(session, ssh, put):
    """Post information on an Instance.

    :param session: ``object``
    :param ssh: ``object``
    :param put: ``dict``
    :return: ``object``
    """
    ssh.ssh_user = put.get('ssh_user', ssh.ssh_user)
    ssh.ssh_key_pri = put.get('ssh_key_pri', ssh.ssh_key_pri)
    ssh.ssh_key_pub = put.get('ssh_key_pub', ssh.ssh_key_pub)
    ssh.key_name = put.get('key_name', ssh.key_name)
    session.flush()
    return session


def get_users():
    """Return all users.

    :return: ``object``
    """
    return CloudAuth.query.order_by(CloudAuth.dcuser)


def get_user_id(user_name):
    """Return a user name by ID.

    :param user_name: ``str``
    :return: ``object``
    """
    return CloudAuth.query.filter(CloudAuth.dcuser == user_name).first()


def get_schematic_id(sid, uid):
    """Return schematics from Schematic ID and auth ID and return it.

    :param sid: ``str``
    :param uid: ``str``
    :return: ``object``
    """
    return Schematics.query.filter(
        Schematics.auth_id == uid, Schematics.id == sid
    ).first()


def get_schematics(uid):
    """Return all schematics and return them as a list.

    :param uid: ``str``
    :return: ``object``
    """
    return Schematics.query.filter(Schematics.auth_id == uid).all()


def get_zones(skm):
    """Return all zones from a provided Schematic.
    
    :param skm: ``object``
    :return: ``object``
    """
    return Zones.query.filter(Zones.schematic_id == skm.id).all()


def get_zones_by_id(skm, zid):
    """Return all zones from a provided Schematic.

    :param skm: ``object``
    :param zid: ``str``
    :return: ``object``
    """
    return Zones.query.filter(
        Zones.schematic_id == skm.id,
        Zones.id == zid
    ).first()


def get_zones_by_ids(skm, zon_ids):
    """Return Zones by IDs.

    :param skm: ``object``
    :param zon_ids: ``list``
    :return: ``object``
    """
    return Zones.query.filter(
        and_(
            Zones.schematic_id == skm.id, Zones.id.in_(zon_ids)
        )
    ).all()


def get_configmanager(skm):
    """Return configuration management from a provided schematic.
    
    :param skm: ``skm``
    :return: ``object``
    """
    return ConfigManager.query.filter(
        ConfigManager.id == skm.config_id
    ).first()


def get_instances(zon):
    """Return all instances for a zone and return them as a list.

    :param zon: ``object``
    :return: ``object``
    """
    return Instances.query.filter(Instances.zone_id == zon.id).all()


def get_instance_id(zon, iid):
    """Return an instance from a zone and the Instance ID.

    :param zon: ``object``
    :param iid: ``object``
    :return: ``object``
    """
    return Instances.query.filter(
        Instances.zone_id == zon.id, Instances.id == iid
    ).first()


def get_instance_ids(zon, ids):
    """Return a list of instances from a zone by a list of ID's.

    :param zon: ``object``
    :param ids: ``list``
    :return: ``object``
    """
    return Instances.query.filter(
        and_(
            Instances.zone_id == zon.id, Instances.instance_id.in_(ids)
        )
    ).all()


def get_instanceskeys(zon):
    """Return credential keys for a zone.

    :param zon: ``object``
    :return: ``object``
    """
    return InstancesKeys.query.filter(
        InstancesKeys.id == zon.credential_id
    ).first()


def delete_item(session, item):
    """Delete and Flush an Item then return the session.

    :param session: ``object``
    :param item: ``object``
    :return: ``object``
    """
    session.delete(item)
    session.flush()
    return session


def add_item(session, item):
    """Add something to a session and return the session.

    :param session: ``object``
    :param item: ``object``
    :return: ``object``
    """
    session.add(item)
    session.flush()
    return session


def commit_session(session):
    """Commit a session and return the session..

    :param session: ``object``
    :return: ``object``
    """
    return session.commit()
