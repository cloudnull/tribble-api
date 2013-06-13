def pop_ts(temp):
    """
    From a dictionary that has been result provided by SQLA remove the time
    stamps from the provided data set. This is to assist when processing raw
    data through Queues, "datetime.datetime is not pickleble.
    """
    poper = ['_sa_instance_state', 'created_at', 'updated_at']
    for _ts in poper:
        if _ts in temp:
            temp.pop(_ts)
    return temp


def parse_dict_list(objlist):
    return [pop_ts(obj.__dict__) for obj in objlist if obj and obj.__dict__]


def not_found(message=None, error=None):
    from flask import jsonify
    if message:
        msg = {"error_text": message}
    else:
        msg = {"error_text": "Resource not found"}

    if error:
        return jsonify(msg), error
    else:
        return jsonify(msg), 404


def auth_mech(rdata, hdata=None):
    from tribble.db.models import CloudAuth
    from tribble.appsetup.start import LOG
    from json import loads
    import traceback
    LOG.debug(rdata)
    obj = CloudAuth.query.filter(
        CloudAuth.dcuser == rdata['x-user']).first()
    if not obj:
        return False
    try:
        user_id = obj.id
        if hdata:
            LOG.debug(hdata)
            try:
                djson = loads(hdata)
            except Exception, exp:
                LOG.error(traceback.format_exc())
                return False
            return user_id, djson
        else:
            return user_id
    except Exception:
        LOG.error(traceback.format_exc())


def build_cell(job, schematic=None, zone=None, sshkey=None, config=None):
    """
    Craft the packet that we need to perform actions
    """
    from tribble.appsetup.start import LOG
    packet = {'cloud_key': schematic.cloud_key,
              'cloud_username': schematic.cloud_username,
              'cloud_region': schematic.cloud_region,
              'cloud_provider': schematic.cloud_provider,
              'job': job}

    if not config is None:
        if config.id:
            packet['config_id'] = config.id
        if config.config_key:
            packet['config_key'] = config.config_key
        if config.config_server:
            packet['config_server'] = config.config_server
        if config.config_validation_key:
            packet['config_validation_key'] = config.config_validation_key
        if config.config_username:
            packet['config_username'] = config.config_username
        if config.config_clientname:
            packet['config_clientname'] = config.config_clientname
        if config.config_type:
            packet['config_type'] = config.config_type

    if not schematic is None:
        if schematic.auth_id:
            packet['auth_id'] = schematic.auth_id
        if schematic.cloud_tenant:
            packet['cloud_tenant'] = schematic.cloud_tenant
        if schematic.cloud_url:
            packet['cloud_url'] = schematic.cloud_url
        if schematic.cloud_version:
            packet['cloud_version'] = schematic.cloud_version
        if schematic.cloud_provider:
            packet['cloud_provider'] = schematic.cloud_provider
        if schematic.id:
            packet['schematic_id'] = schematic.id

    if not sshkey is None:
        if sshkey.id:
            packet['credential_id'] = sshkey.id
        if sshkey.ssh_user:
            packet['ssh_username'] = sshkey.ssh_user
        if sshkey.ssh_key_pub:
            packet['ssh_key_pub'] = sshkey.ssh_key_pub
        if sshkey.key_name:
            packet['key_name'] = sshkey.key_name

    if not zone is None:
        if zone.quantity:
            packet['quantity'] = zone.quantity
        if zone.name_convention:
            packet['name_convention'] = zone.name_convention
        if zone.image_id:
            packet['image_id'] = zone.image_id
        if zone.size_id:
            packet['size_id'] = zone.size_id
        if zone.id:
            packet['zone_id'] = zone.id
        if zone.zone_msg:
            packet['zone_msg'] = zone.zone_msg
        if zone.zone_state:
            packet['zone_state'] = zone.zone_state
        if zone.config_runlist:
            packet['config_runlist'] = zone.config_runlist
        if zone.config_script:
            packet['config_script'] = zone.config_script
        if zone.config_env:
            packet['config_env'] = zone.config_env
        if zone.cloud_networks:
            packet['cloud_networks'] = zone.cloud_networks
        if zone.security_groups:
            packet['security_groups'] = zone.security_groups
        if zone.inject_files:
            packet['inject_files'] = zone.inject_files
        if zone.cloud_init:
            packet['cloud_init'] = zone.cloud_init

    LOG.debug('Sent Packet for Work ==> \n\n%s\n\n' % packet)
    return packet
