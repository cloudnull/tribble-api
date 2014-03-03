# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import logging
import traceback
import json
from base64 import b64encode as b64e
from sys import getsizeof

from flask import jsonify
from flask import request

from tribble.common.db import db_proc


LOG = logging.getLogger('tribble-api')


def return_msg(msg, status=200):
    return jsonify({'response': msg}), status


def parse_dict_list(objlist):
    return [pop_ts(obj.__dict__) for obj in objlist if obj and obj.__dict__]


def auth_mech(rdata, hdata=None):

    LOG.debug(rdata)
    user_query = db_proc.get_user_id(user_name=rdata['x-user'])

    LOG.debug(user_query)
    if not user_query:
        return False
    else:
        try:
            user_id = user_query.id
            if hdata:
                try:
                    djson = json.loads(hdata)
                except Exception:
                    LOG.error(traceback.format_exc())
                    return False
                else:
                    return user_id, djson
            else:
                return user_id
        except Exception:
            LOG.error(traceback.format_exc())


def max_size(obj):
    """
    The Max allowable Size of a object can only be 10KB
    """

    b64obj = b64e(obj)
    objsize = getsizeof(b64obj) / 1024
    if objsize > 12:
        LOG.info('File was REJECTED for being too larger')
        return None
    else:
        return b64obj


def encoder(obj):
    """
    Encode Script Type Objects into Base64 for Database Storage
    """

    if 'config_script' in obj:
        obj['config_script'] = max_size(obj=obj['config_script'])

    if 'cloud_init' in obj:
        obj['cloud_init'] = max_size(obj=obj['cloud_init'])

    if 'inject_files' in obj:
        obj['inject_files'] = max_size(obj=obj['inject_files'])

    return obj


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


def build_schematic_cell(schematic):
    cell = build_cell(
        job='schematic_delete',
        schematic=schematic,
        config=db_proc.get_configmanager
    )
    LOG.debug('PROCESS CELL => %s' % cell)
    return cell


def build_schematic_list(schematic):
    dict_schematic = pop_ts(temp=schematic.__dict__)
    zones = db_proc.get_zones(skm=schematic)
    dict_schematic['num_zones'] = len(zones)
    config_manager = db_proc.get_configmanager(skm=schematic)
    dict_schematic['config_manager'] = pop_ts(temp=config_manager.__dict__)
    return dict_schematic


def build_cell(job, schematic=None, zone=None, sshkey=None, config=None):
    """
    Craft the packet that we need to perform actions
    """

    packet = {
        'cloud_key': schematic.cloud_key,
        'cloud_username': schematic.cloud_username,
        'cloud_provider': schematic.cloud_provider,
        'job': job
    }

    if config is not None:
        if config.id:
            packet['config_id'] = str(config.id)
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

    if schematic is not None:
        if schematic.auth_id:
            packet['auth_id'] = str(schematic.auth_id)
        if schematic.cloud_tenant:
            packet['cloud_tenant'] = schematic.cloud_tenant
        if schematic.cloud_url:
            packet['cloud_url'] = schematic.cloud_url
        if schematic.cloud_version:
            packet['cloud_version'] = schematic.cloud_version
        if schematic.cloud_provider:
            packet['cloud_provider'] = schematic.cloud_provider
        if schematic.id:
            packet['schematic_id'] = str(schematic.id)

    if sshkey is not None:
        if sshkey.id:
            packet['credential_id'] = str(sshkey.id)
        if sshkey.ssh_user:
            packet['ssh_username'] = sshkey.ssh_user
        if sshkey.ssh_key_pub:
            packet['ssh_key_pub'] = sshkey.ssh_key_pub
        if sshkey.key_name:
            packet['key_name'] = sshkey.key_name

    if zone is not None:
        if zone.cloud_region:
            packet['cloud_region'] = zone.cloud_region
        if zone.quantity:
            packet['quantity'] = zone.quantity
        if zone.name_convention:
            packet['name_convention'] = zone.name_convention
        if zone.image_id:
            packet['image_id'] = str(zone.image_id)
        if zone.size_id:
            packet['size_id'] = str(zone.size_id)
        if zone.id:
            packet['zone_id'] = str(zone.id)
        if zone.zone_msg:
            packet['zone_msg'] = zone.zone_msg
        if zone.zone_state:
            packet['zone_state'] = zone.zone_state
        if zone.config_runlist:
            packet['config_runlist'] = zone.config_runlist
        if zone.config_script:
            packet['config_script'] = b64e(zone.config_script)
        if zone.config_env:
            packet['config_env'] = zone.config_env
        if zone.cloud_networks:
            packet['cloud_networks'] = zone.cloud_networks
        if zone.security_groups:
            packet['security_groups'] = zone.security_groups
        if zone.inject_files:
            packet['inject_files'] = b64e(zone.inject_files)
        if zone.cloud_init:
            packet['cloud_init'] = b64e(zone.cloud_init)

    LOG.debug('Sent Packet for Work ==> \n\n%s\n\n' % packet)
    return packet


def zone_data_handler(sid, check_for_zone=False):
    if not sid:
        return False, 'No Schematic specified', 400

    auth = auth_mech(hdata=request.data, rdata=request.headers)
    if not auth:
        return False, 'Authentication or Data Type Failure', 401
    else:
        user_id, payload = auth

    if not all([user_id, payload]):
        return False, 'Missing Information %s %s' % (user_id, payload), 400
    else:
        payload = encoder(obj=payload)
        LOG.debug(payload)

    schematic = db_proc.get_schematic_id(sid=sid, uid=user_id)
    if not schematic:
        return False, 'no schematic found', 404

    if check_for_zone is True and 'zones' not in payload:
        return False, 'Missing Information %s %s' % (user_id, payload), 400

    return True, schematic, payload, user_id


def zone_basic_handler(sid, zid=None):
    if not sid:
        return False, 'No Schematic Specified', 400

    user_id = auth_mech(rdata=request.headers)
    if not user_id:
        return False, 'no user id found', 400

    schematic = db_proc.get_schematic_id(sid=sid, uid=user_id)
    if not schematic:
        return False, 'no schematic found', 404

    if zid is not None:
        zone = db_proc.get_zones_by_id(skm=schematic, zid=zid)
        if not zone:
            return False, 'no zones found', 404
        elif zone.zone_state == 'BUILDING':
            build_response = (
                'Zone Delete can not be performed because Zone "%s" has a'
                ' Pending Status' % zone.id
            )
            return False, build_response, 200
        else:
            return True, schematic, zone, user_id
    else:
        zones = db_proc.get_zones(skm=schematic)
        if not zones:
            return False, 'no zones found', 404
        else:
            return True, schematic, zones, user_id
