# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from uuid import uuid4 as uuid

from sqlalchemy.orm import relation

from tribble.api.application import DB


class CloudAuth(DB.Model):
    __tablename__ = 'cloudauth'
    user_type = DB.Column(
        'user_type',
        DB.VARCHAR(length=10),
        default=0,
        nullable=False
    )
    dcuser = DB.Column(
        'dcuser',
        DB.VARCHAR(length=25),
        unique=True
    )
    dcsecret = DB.Column(
        'dcsecret',
        DB.TEXT(length=4000)
    )
    created_at = DB.Column(
        'created_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    updated_at = DB.Column(
        'updated_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    id = DB.Column(
        'id',
        DB.VARCHAR(length=200),
        default=uuid,
        primary_key=True,
        nullable=False
    )

    def __init__(self, user_type, dcuser, dcsecret, created_at, updated_at):
        """
        This table represents the users that are allowed to post / use the
        system. Note that the "secret" field is plain text. It is up to the
        user to place encrypted passwords into the system, else they will be
        stored in plane text.
        """
        self.user_type = user_type
        self.dcuser = dcuser
        self.dcsecret = dcsecret
        self.created_at = created_at
        self.updated_at = updated_at


class InstancesKeys(DB.Model):
    __tablename__ = 'instances_keys'
    ssh_user = DB.Column(
        'ssh_user',
        DB.VARCHAR(length=20)
    )
    ssh_key_pub = DB.Column(
        'ssh_key_pub',
        DB.TEXT(),
        nullable=True
    )
    ssh_key_pri = DB.Column(
        'ssh_key_pri',
        DB.TEXT(),
        nullable=True
    )
    key_name = DB.Column(
        'key_name',
        DB.VARCHAR(length=50),
        nullable=True
    )
    created_at = DB.Column(
        'created_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    updated_at = DB.Column(
        'updated_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    id = DB.Column(
        'id',
        DB.VARCHAR(length=200),
        default=uuid,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    def __init__(self, ssh_user, ssh_key_pub, ssh_key_pri, key_name):
        """The Keys are used to interface with an instance.

        This is used for instance bootstrap and or interfacing with an
        instance,
        """

        self.ssh_key_pri = ssh_key_pri
        self.ssh_key_pub = ssh_key_pub
        self.ssh_user = ssh_user
        self.key_name = key_name


class ConfigManager(DB.Model):
    __tablename__ = 'config_manager'
    config_key = DB.Column(
        'config_key',
        DB.TEXT(),
        nullable=True
    )
    config_server = DB.Column(
        'config_server',
        DB.VARCHAR(length=200),
        nullable=True
    )
    config_type = DB.Column(
        'config_type',
        DB.VARCHAR(length=30)
    )
    config_username = DB.Column(
        'config_username',
        DB.VARCHAR(length=150),
        nullable=True
    )
    config_clientname = DB.Column(
        'config_clientname',
        DB.VARCHAR(length=150),
        nullable=True
    )
    config_validation_key = DB.Column(
        'config_validation_key',
        DB.TEXT(),
        nullable=True
    )
    created_at = DB.Column(
        'created_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    updated_at = DB.Column(
        'updated_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    id = DB.Column(
        'id',
        DB.VARCHAR(length=200),
        default=uuid,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    def __init__(self, config_key, config_type, config_server,
                 config_username, config_clientname, config_validation_key):
        """All Config Management is stored here."""

        self.config_key = config_key
        self.config_type = config_type
        self.config_server = config_server
        self.config_username = config_username
        self.config_clientname = config_clientname
        self.config_validation_key = config_validation_key


class Schematics(DB.Model):
    __tablename__ = 'schematics'
    auth_id = DB.Column(
        'auth_id',
        DB.VARCHAR(length=200),
        DB.ForeignKey('cloudauth.id'),
        nullable=False
    )
    schematic_cloud_auth_constraint = relation(
        'CloudAuth',
        primaryjoin='Schematics.auth_id==CloudAuth.id'
    )
    config_id = DB.Column(
        'config_id',
        DB.VARCHAR(length=200),
        DB.ForeignKey('config_manager.id'),
        nullable=True
    )
    schematic_config_manager_constraint = relation(
        'ConfigManager',
        primaryjoin='Schematics.config_id==ConfigManager.id'
    )
    cloud_key = DB.Column(
        'cloud_key',
        DB.VARCHAR(length=150),
        nullable=True
    )
    cloud_url = DB.Column(
        'cloud_url',
        DB.VARCHAR(length=150),
        nullable=True
    )
    cloud_provider = DB.Column(
        'cloud_provider',
        DB.VARCHAR(length=30),
        nullable=False
    )
    cloud_version = DB.Column(
        'cloud_version',
        DB.VARCHAR(length=10),
        nullable=True
    )
    cloud_username = DB.Column(
        'cloud_username',
        DB.VARCHAR(length=150),
        nullable=False
    )
    cloud_tenant = DB.Column(
        'cloud_tenant',
        DB.VARCHAR(length=100),
        nullable=True
    )
    name = DB.Column(
        'name',
        DB.VARCHAR(length=100),
        nullable=True
    )
    created_at = DB.Column(
        'created_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    updated_at = DB.Column(
        'updated_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    id = DB.Column(
        'id',
        DB.VARCHAR(length=200),
        default=uuid,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    def __init__(self, config_id, cloud_key, cloud_url, cloud_username,
                 cloud_provider, cloud_version, cloud_tenant, auth_id, name):
        """
        Schematics provide for the configuration which would peratine to a
        built Zone.
        """

        self.config_id = config_id
        self.auth_id = auth_id
        self.name = name
        self.cloud_key = cloud_key
        self.cloud_url = cloud_url
        self.cloud_provider = cloud_provider
        self.cloud_version = cloud_version
        self.cloud_tenant = cloud_tenant
        self.cloud_username = cloud_username


class Zones(DB.Model):
    __tablename__ = 'zones'
    schematic_id = DB.Column(
        'schematic_id',
        DB.VARCHAR(length=200),
        DB.ForeignKey('schematics.id'),
        nullable=False
    )
    schematic_constraint = relation(
        'Schematics',
        primaryjoin='Zones.schematic_id==Schematics.id'
    )
    cloud_region = DB.Column(
        'cloud_region',
        DB.VARCHAR(length=30),
        nullable=True
    )
    config_runlist = DB.Column(
        'config_runlist',
        DB.TEXT(),
        nullable=True
    )
    config_env = DB.Column(
        'config_env',
        DB.VARCHAR(length=30)
    )
    config_script = DB.Column(
        'config_script',
        DB.TEXT(),
        nullable=True
    )
    security_groups = DB.Column(
        'security_groups',
        DB.TEXT(length=200),
        nullable=True
    )
    inject_files = DB.Column(
        'inject_files',
        DB.BLOB(),
        nullable=True
    )
    cloud_networks = DB.Column(
        'cloud_networks',
        DB.TEXT(length=200),
        nullable=True
    )
    cloud_init = DB.Column(
        'cloud_init',
        DB.TEXT(length=4000),
        nullable=True
    )
    zone_msg = DB.Column(
        'zone_msg',
        DB.VARCHAR(length=250),
        nullable=False
    )
    zone_state = DB.Column(
        'zone_state',
        DB.VARCHAR(length=15),
        nullable=False
    )
    zone_name = DB.Column(
        'zone_name',
        DB.VARCHAR(length=200),
        nullable=False
    )
    size_id = DB.Column(
        'size_id',
        DB.VARCHAR(length=150),
        nullable=False
    )
    image_id = DB.Column(
        'image_id',
        DB.VARCHAR(length=150),
        nullable=False
    )
    name_convention = DB.Column(
        'name_convention',
        DB.VARCHAR(length=30),
        nullable=False
    )
    quantity = DB.Column(
        'quantity',
        DB.INTEGER(),
        nullable=False
    )
    credential_id = DB.Column(
        'credential_id',
        DB.VARCHAR(length=200),
        DB.ForeignKey('instances_keys.id'),
        nullable=False
    )
    zone_constraint = relation(
        'InstancesKeys',
        primaryjoin='Zones.credential_id==InstancesKeys.id'
    )
    created_at = DB.Column(
        'created_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    updated_at = DB.Column(
        'updated_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    id = DB.Column(
        'id',
        DB.VARCHAR(length=200),
        default=uuid,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    def __init__(self, cloud_region, security_groups, inject_files,
                 cloud_networks, cloud_init, schematic_id, config_runlist,
                 config_script, config_env, zone_msg, zone_state, zone_name,
                 size_id, image_id, name_convention, quantity, credential_id):
        """
        Zones provide a specific setup for a collection of instances.
        """

        self.cloud_region = cloud_region
        self.security_groups = security_groups
        self.inject_files = inject_files
        self.cloud_networks = cloud_networks
        self.cloud_init = cloud_init
        self.config_runlist = config_runlist
        self.schematic_id = schematic_id
        self.config_script = config_script
        self.config_env = config_env
        self.zone_msg = zone_msg
        self.zone_state = zone_state
        self.zone_name = zone_name
        self.size_id = size_id
        self.image_id = image_id
        self.name_convention = name_convention
        self.quantity = quantity
        self.credential_id = credential_id


class Instances(DB.Model):
    __tablename__ = 'instances'
    zone_id = DB.Column(
        'zone_id',
        DB.VARCHAR(length=200),
        DB.ForeignKey('zones.id')
    )
    zone_constraint = relation(
        'Zones',
        primaryjoin='Instances.zone_id==Zones.id'
    )
    instance_id = DB.Column(
        'instance_id',
        DB.VARCHAR(length=200)
    )
    public_ip = DB.Column(
        'public_ip',
        DB.VARCHAR(length=200)
    )
    private_ip = DB.Column(
        'private_ip',
        DB.VARCHAR(length=200)
    )
    server_name = DB.Column(
        'server_name',
        DB.VARCHAR(length=200)
    )
    created_at = DB.Column(
        'created_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    updated_at = DB.Column(
        'updated_at',
        DB.TIMESTAMP(),
        nullable=False
    )
    id = DB.Column(
        'id',
        DB.VARCHAR(length=200),
        default=uuid,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    def __init__(self, instance_id, public_ip, private_ip,
                 server_name, zone_id):
        """
        Table for all created instances. If an instance is created it is
        recorded in this table and will pertain to a specified Zone.
        """

        self.zone_id = zone_id
        self.public_ip = public_ip
        self.private_ip = private_ip
        self.instance_id = instance_id
        self.server_name = server_name
