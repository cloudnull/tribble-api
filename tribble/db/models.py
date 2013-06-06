from sqlalchemy.orm import relation
from uuid import uuid4 as uuid
from tribble.appsetup.start import _DB


class CloudAuth(_DB.Model):
    __tablename__ = 'cloudauth'
    dcuser = _DB.Column('dcuser',
                        _DB.VARCHAR(length=20),
                        unique=True)
    dcsecret = _DB.Column('dcsecret',
                          _DB.TEXT(length=4000))
    created_at = _DB.Column('created_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    updated_at = _DB.Column('updated_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    id = _DB.Column('id',
                    _DB.VARCHAR(length=200),
                    default=uuid,
                    primary_key=True,
                    nullable=False)

    def __init__(self, dcuser, dcsecret, created_at, updated_at):
        """
        This table represents the users that are allowed to post / use the
        system. Note that the "secret" field is plain text. It is up to the user
        to place encrypted passwords into the system, else they will be stored
        in plane text.
        """
        self.dcuser = dcuser
        self.dcsecret = dcsecret
        self.created_at = created_at
        self.updated_at = updated_at


class InstancesKeys(_DB.Model):
    __tablename__ = 'instances_keys'
    ssh_user = _DB.Column('ssh_user',
                          _DB.VARCHAR(length=20))
    ssh_key_pri = _DB.Column('ssh_key_pri',
                             _DB.TEXT(length=4000),
                             nullable=True)
    ssh_key_pub = _DB.Column('ssh_key_pub',
                             _DB.TEXT(length=4000),
                             nullable=True)
    key_name = _DB.Column('key_name',
                          _DB.VARCHAR(length=50),
                          nullable=True)
    created_at = _DB.Column('created_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    updated_at = _DB.Column('updated_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    id = _DB.Column('id',
                    _DB.VARCHAR(length=200),
                    default=uuid,
                    primary_key=True,
                    nullable=False,
                    autoincrement=True)

    def __init__(self, ssh_user, ssh_key_pri, ssh_key_pub, key_name):
        """
        The Keys are used to interface with an instance. This is used for
        instance bootstrap and or interfacing with an instance,
        """
        self.ssh_user = ssh_user
        self.ssh_key_pri = ssh_key_pri
        self.ssh_key_pub = ssh_key_pub
        self.key_name = key_name


class ConfigManager(_DB.Model):
    __tablename__ = 'config_manager'
    config_key = _DB.Column('config_key',
                            _DB.TEXT(),
                            nullable=True)
    config_server = _DB.Column('config_server',
                               _DB.VARCHAR(length=200),
                               nullable=True)
    config_type = _DB.Column('config_type',
                             _DB.VARCHAR(length=30))
    config_env = _DB.Column('config_env',
                            _DB.VARCHAR(length=30))
    config_username = _DB.Column('config_username',
                                 _DB.VARCHAR(length=150),
                                 nullable=True)
    config_clientname = _DB.Column('config_clientname',
                                   _DB.VARCHAR(length=150),
                                   nullable=True)
    config_validation_key = _DB.Column('config_validation_key',
                                       _DB.TEXT(),
                                       nullable=True)
    created_at = _DB.Column('created_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    updated_at = _DB.Column('updated_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    id = _DB.Column('id',
                    _DB.VARCHAR(length=200),
                    default=uuid,
                    primary_key=True,
                    nullable=False,
                    autoincrement=True)

    def __init__(self, config_key, config_env, config_type, config_server,
                 config_username, config_clientname, config_validation_key):
        """
        All Config Management is stored here.
        """
        self.config_key = config_key
        self.config_env = config_env
        self.config_type = config_type
        self.config_server = config_server
        self.config_username = config_username
        self.config_clientname = config_clientname
        self.config_validation_key = config_validation_key


class Schematics(_DB.Model):
    __tablename__ = 'schematics'
    auth_id = _DB.Column('auth_id',
                         _DB.VARCHAR(length=200),
                         _DB.ForeignKey('cloudauth.id'),
                         nullable=False)
    schematic_constraint = relation(
        'CloudAuth', primaryjoin='Schematics.auth_id==CloudAuth.id')
    config_id = _DB.Column('config_id',
                           _DB.VARCHAR(length=200),
                           _DB.ForeignKey('config_manager.id'),
                           nullable=True)
    schematic_constraint = relation(
        'ConfigManager', primaryjoin='Schematics.config_id==ConfigManager.id')
    cloud_key = _DB.Column('cloud_key',
                           _DB.VARCHAR(length=150),
                           nullable=True)
    cloud_url = _DB.Column('cloud_url',
                           _DB.VARCHAR(length=150),
                           nullable=True)
    cloud_provider = _DB.Column('cloud_provider',
                                _DB.VARCHAR(length=30),
                                nullable=False)
    cloud_version = _DB.Column('cloud_version',
                               _DB.VARCHAR(length=10),
                               nullable=True)
    cloud_region = _DB.Column('cloud_region',
                              _DB.VARCHAR(length=30),
                              nullable=True)
    cloud_username = _DB.Column('cloud_username',
                                _DB.VARCHAR(length=150),
                                nullable=False)
    cloud_tenant = _DB.Column('cloud_tenant',
                              _DB.VARCHAR(length=100),
                              nullable=True)
    created_at = _DB.Column('created_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    updated_at = _DB.Column('updated_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    id = _DB.Column('id',
                    _DB.VARCHAR(length=200),
                    default=uuid,
                    primary_key=True,
                    nullable=False,
                    autoincrement=True)

    def __init__(self, config_id, cloud_key, cloud_url, cloud_username,
                 cloud_provider, cloud_version, cloud_region, cloud_tenant,
                 auth_id):
        """
        Schematics provide for the configuration which would peratine to a
        built Zone.
        """
        self.config_id = config_id
        self.auth_id = auth_id
        self.cloud_key = cloud_key
        self.cloud_url = cloud_url
        self.cloud_provider = cloud_provider
        self.cloud_version = cloud_version
        self.cloud_region = cloud_region
        self.cloud_tenant = cloud_tenant
        self.cloud_username = cloud_username


class Zones(_DB.Model):
    __tablename__ = 'zones'
    schematic_id = _DB.Column('schematic_id',
                              _DB.VARCHAR(length=200),
                              _DB.ForeignKey('schematics.id'),
                              nullable=False)
    schematic_constraint = relation(
        'Schematics', primaryjoin='Zones.schematic_id==Schematics.id')
    schematic_runlist = _DB.Column('schematic_runlist',
                                   _DB.TEXT(),
                                   nullable=True)
    schematic_script = _DB.Column('schematic_script',
                                  _DB.TEXT(),
                                  nullable=True)
    security_groups = _DB.Column('security_groups',
                                 _DB.TEXT(length=200),
                                 nullable=True)
    inject_files = _DB.Column('inject_files',
                              _DB.BLOB(),
                              nullable=True)
    cloud_networks = _DB.Column('cloud_networks',
                                _DB.TEXT(length=200),
                                nullable=True)
    cloud_init = _DB.Column('cloud_init',
                            _DB.TEXT(length=4000),
                            nullable=True)
    zone_name = _DB.Column('zone_name',
                           _DB.VARCHAR(length=200),
                           nullable=False)
    size_id = _DB.Column('size_id',
                         _DB.INTEGER(),
                         nullable=False)
    image_id = _DB.Column('image_id',
                          _DB.VARCHAR(length=50),
                          nullable=False)
    name_convention = _DB.Column('name_convention',
                                 _DB.VARCHAR(length=30),
                                 nullable=False)
    quantity = _DB.Column('quantity',
                          _DB.INTEGER(),
                          nullable=False)
    credential_id = _DB.Column('credential_id',
                               _DB.VARCHAR(length=200),
                               _DB.ForeignKey('instances_keys.id'),
                               nullable=False)
    schematic_constraint = relation(
        'InstancesKeys', primaryjoin='Zones.credential_id==InstancesKeys.id')
    created_at = _DB.Column('created_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    updated_at = _DB.Column('updated_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    id = _DB.Column('id',
                    _DB.VARCHAR(length=200),
                    default=uuid,
                    primary_key=True,
                    nullable=False,
                    autoincrement=True)

    def __init__(self, security_groups, inject_files, cloud_networks,
                 cloud_init, schematic_id, schematic_runlist, schematic_script,
                 zone_name, size_id, image_id, name_convention, quantity,
                 credential_id):
        """
        Zones provide a specific setup for a collection of instances.
        """
        self.security_groups = security_groups
        self.inject_files = inject_files
        self.cloud_networks = cloud_networks
        self.cloud_init = cloud_init
        self.schematic_runlist = schematic_runlist
        self.schematic_id = schematic_id
        self.schematic_script = schematic_script
        self.zone_name = zone_name
        self.size_id = size_id
        self.image_id = image_id
        self.name_convention = name_convention
        self.quantity = quantity
        self.credential_id = credential_id


class Instances(_DB.Model):
    __tablename__ = 'instances'
    zone_id = _DB.Column('zone_id',
                         _DB.VARCHAR(length=200),
                         _DB.ForeignKey('zones.id'))
    zone_constraint = relation(
        'Zones', primaryjoin='Instances.zone_id==Zones.id')
    instance_id = _DB.Column('instance_id',
                             _DB.VARCHAR(length=200))
    public_ip = _DB.Column('public_ip',
                           _DB.VARCHAR(length=200))
    private_ip = _DB.Column('private_ip',
                            _DB.VARCHAR(length=200))
    server_name = _DB.Column('server_name',
                             _DB.VARCHAR(length=200))
    created_at = _DB.Column('created_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    updated_at = _DB.Column('updated_at',
                            _DB.TIMESTAMP(),
                            nullable=False)
    id = _DB.Column('id',
                    _DB.VARCHAR(length=200),
                    default=uuid,
                    primary_key=True,
                    nullable=False,
                    autoincrement=True)

    def __init__(self, instance_id, public_ip, private_ip,
                 server_name, zone_id):
        """
        Table for all created instances. If an instance is created it is
        recorded in this table and will pertain to a specified Zone.
        """
        self.instance_id = instance_id
        self.public_ip = public_ip
        self.private_ip = private_ip
        self.server_name = server_name
        self.zone_id = zone_id
