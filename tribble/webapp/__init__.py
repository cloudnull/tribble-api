

def pop_ts(temp):
    """
    From a dictionary that has been result provided by SQLA remove the time
    stamps from the provided data set. This is to assist when processing raw
    data through Queues, "datetime.datetime is not pickleble.
    """
    poper = ['_sa_instance_state', 'heal_at', 'created_at', 'updated_at']
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


def build_cell(job, schematic=None, zone=None,
               sshkey=None, config=None):
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
        if config.config_env:
            packet['config_env'] = config.config_env

    if not schematic is None:
        if schematic.cloud_tenant:
            packet['cloud_tenant'] = schematic.cloud_tenant
        if schematic.cloud_url:
            packet['cloud_url'] = schematic.cloud_url
        if schematic.cloud_version:
            packet['cloud_version'] = schematic.cloud_version
        if schematic.cloud_provider:
            packet['cloud_provider'] = schematic.cloud_provider
        if schematic.id:
            packet['id'] = schematic.id

    if not sshkey is None:
        if sshkey.id:
            packet['credential_id'] = sshkey.id
        if sshkey.ssh_user:
            packet['ssh_username'] = sshkey.ssh_user
        if sshkey.ssh_key_pri:
            packet['ssh_key_pri'] = sshkey.ssh_key_pri
        if sshkey.ssh_key_pub:
            packet['ssh_key_pub'] = sshkey.ssh_key_pub
        if sshkey.key_name:
            packet['key_name'] = sshkey.key_name

    if not zone is None:
        if zone.quantity:
            packet['quantity'] = zone.quantity
        if zone.name_convention:
            packet['name'] = zone.name_convention
        if zone.image_id:
            packet['image'] = zone.image_id
        if zone.size_id:
            packet['size'] = zone.size_id
        if zone.id:
            packet['zone_id'] = zone.id
        if zone.schematic_runlist:
            packet['schematic_runlist'] = zone.schematic_runlist
        if zone.schematic_script:
            packet['schematic_script'] = zone.schematic_script
        if zone.cloud_networks:
            packet['cloud_networks'] = zone.networks
        if zone.security_groups:
            packet['security_groups'] = zone.security_groups
        if zone.inject_files:
            packet['inject_files'] = zone.inject_files
        if zone.cloud_init:
            packet['cloud_init'] = zone.cloud_init

    LOG.debug('Sent Packet for Work ==> \n\n%s\n\n' % packet)
    return packet


def blueprint_validation(jtv):
    """
    Takes json to validate, the validation map will be a list of keys
    that should Be present
    """
    import json
    from flask import jsonify
    from tribble.appsetup.start import LOG

    blue_print = json.loads(jtv)
    LOG.warn(jtv)
    if not 'blue_print' in blue_print:
        error_json = {"error_text": "no blue_print tag detected in json"}
        return jsonify(error_json), 400

    if not 'server_map' in blue_print['blue_print']:
        error_json = {"error_text": "no server_map tag detected in json"}
        return jsonify(error_json), 400

    for server_map in blue_print['blue_print']['server_map']:
        chk = {'name_convention': "You must specify a name convention",
               'quantity': "You must specify a quantity of nodes to build",
               'image_ref': "Please specify an image reference",
               'flavor': "Please specify a valid flavor"}

        for _chk in chk.keys():
            if not _chk in server_map:
                LOG.warn(chk[_chk])
                return jsonify(error_text=chk[_chk]), 400

        if not type(server_map['quantity']) is int:
            not_int = "Please specify quantity as a whole number"
            LOG.warn(not_int)
            return jsonify(error_text=(not_int)), 400
    LOG.debug('Narciss BluePrint for Work ==> \n\n%s\n\n' % blue_print)
    return blue_print
