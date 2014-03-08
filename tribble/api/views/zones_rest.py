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

import flask

from tribble.api import application
from tribble.api import utils
from tribble.common.db import db_proc
from tribble.common.db import zone_status
from tribble.common import rpc
from tribble.common import system_config


mod = flask.Blueprint('zones', __name__)
LOG = logging.getLogger('tribble-api')
CONFIG = system_config.ConfigurationSetup()
DEFAULT = CONFIG.config_args()
DB = application.DB


@mod.route('/v1/schematics/<sid>/zones', methods=['GET'])
def zones_get(sid):
    """Return a list of zones.

    Method is accessible with GET /v1/schematics/<sid>/zones

    :param sid: ``str`` # schematic ID
    :return json, status: ``tuple``
    """
    parsed_data = utils.zone_basic_handler(sid=sid)
    if parsed_data[0] is False:
        return utils.return_msg(msg=parsed_data[1], status=parsed_data[2])
    else:
        _success, schematic, zones, user_id = parsed_data
        LOG.debug('%s %s %s %s', _success, schematic, zones, user_id)

    try:
        return_zones = []
        for zone in zones:
            dzone = utils.pop_ts(zone.__dict__)
            instances = db_proc.get_instances(zon=zone)
            if instances:
                dzone['instance_quantity'] = len(instances)

            return_zones.append(dzone)
    except Exception:
        LOG.error(traceback.format_exc())
        return utils.return_msg(msg='Unexpected Error', status=500)
    else:
        return utils.return_msg(msg=return_zones, status=200)


@mod.route('/v1/schematics/<sid>/zones/<zid>', methods=['GET'])
def zone_get(sid, zid):
    """Return a zone.

    Method is accessible with GET /v1/schematics/<sid>/zones/<zid>

    :param sid: ``str`` # schematic ID
    :param zid: ``str`` # Zone ID
    :return json, status: ``tuple``
    """
    parsed_data = utils.zone_basic_handler(sid=sid, zid=zid)
    if parsed_data[0] is False:
        return utils.return_msg(msg=parsed_data[1], status=parsed_data[2])
    else:
        _success, schematic, zone, user_id = parsed_data
        _zone = utils.pop_ts(temp=zone.__dict__)
        instances = db_proc.get_instances(zon=zone)
        if instances:
            _zone['instances'] = [
                utils.pop_ts(temp=instance.__dict__) for instance in instances
            ]
        LOG.debug('%s %s %s %s', _success, schematic, zone, user_id)
        return utils.return_msg(msg=_zone, status=200)


@mod.route('/v1/schematics/<sid>/zones/<zid>', methods=['DELETE'])
def zone_delete(sid=None, zid=None):
    """Delete a Zone.

    Method is accessible with DELETE /v1/schematics/<sid>/zones/<zid>

    :param sid: ``str`` # schematic ID
    :param zid: ``str`` # Zone ID
    :return json, status: ``tuple``
    """

    parsed_data = utils.zone_basic_handler(sid=sid, zid=zid)
    if parsed_data[0] is False:
        return utils.return_msg(msg=parsed_data[1], status=parsed_data[2])
    else:
        _success, schematic, zone, user_id = parsed_data
        if zone.zone_state == 'BUILDING':
            build_response = (
                'Zone Delete can not be performed because Zone "%s" has a'
                ' Pending Status' % zone.id
            )
            return utils.return_msg(msg=build_response, status=200)

        LOG.debug('%s %s %s %s', _success, schematic, zone, user_id)
        try:
            config = db_proc.get_configmanager(skm=schematic)
            instances = db_proc.get_instances(zon=zone)
            packet = utils.build_cell(
                job='zone_delete',
                schematic=schematic,
                zone=zone,
                config=config
            )
            packet['uuids'] = [instance.instance_id for instance in instances]
            rpc.default_publisher(message=packet)

            sess = DB.session
            zone_status.ZoneState(cell=packet).delete()
        except Exception:
            LOG.error(traceback.format_exc())
            return utils.return_msg(msg='unexpected error', status=500)
        else:
            db_proc.commit_session(session=sess)
            return utils.return_msg(msg='deletes received', status=203)


@mod.route('/v1/schematics/<sid>/zones/<zid>/purge', methods=['DELETE'])
def zone_purge(sid=None, zid=None):
    """purge a Zone.

    This is used to remove all indication of a zone without attempting to
    disconnect or otherwise clean up the zone or any of its may be attached
    instances.

    Method is accessible with DELETE /v1/schematics/<sid>/zones/<zid>/purge

    :param sid: ``str`` # schematic ID
    :param zid: ``str`` # Zone ID
    :return json, status: ``tuple``
    """
    parsed_data = utils.zone_basic_handler(sid=sid, zid=zid)
    if parsed_data[0] is False:
        return utils.return_msg(msg=parsed_data[1], status=parsed_data[2])
    else:
        _success, schematic, zone, user_id = parsed_data
        LOG.debug('%s %s %s %s', _success, schematic, zone, user_id)
        try:
            sess = DB.session
            db_proc.delete_item(session=sess, item=zone)
        except Exception:
            LOG.error(traceback.format_exc())
            return utils.return_msg(msg='unexpected error', status=500)
        else:
            db_proc.commit_session(session=sess)
            return utils.return_msg(
                msg='zone %s was purged' % zone.id, status=203
            )


@mod.route('/v1/schematics/<sid>/zones/<zid>', methods=['PUT'])
def zone_put(sid=None, zid=None):
    """Update a Zone.

    Method is accessible with PUT /v1/schematics/<sid>/zones/<zid>

    :param sid: ``str`` # schematic ID
    :param zid: ``str`` # Zone ID
    :return json, status: ``tuple``
    """
    parsed_data = utils.zone_data_handler(sid=sid)
    if parsed_data[0] is False:
        return utils.return_msg(msg=parsed_data[1], status=parsed_data[2])
    else:
        _success, schematic, payload, user_id = parsed_data
        LOG.debug('%s %s %s %s', _success, schematic, payload, user_id)

    zone = db_proc.get_zones_by_id(skm=schematic, zid=zid)
    if not zone:
        return utils.return_msg(msg='no zones found', status=404)

    try:
        sess = DB.session
        sess = db_proc.put_zone(
            session=sess,
            zon=zone,
            put=payload
        )
    except Exception:
        LOG.error(traceback.format_exc())
        return utils.return_msg(msg='unexpected error', status=500)
    else:
        db_proc.commit_session(session=sess)
        return utils.return_msg(msg='updates received', status=201)


@mod.route('/v1/schematics/<sid>/zones', methods=['POST'])
def zone_post(sid=None):
    """Post a Zone.

    Method is accessible with POST /v1/schematics/<sid>/zones

    :param sid: ``str`` # schematic ID
    :return json, status: ``tuple``
    """
    parsed_data = utils.zone_data_handler(sid=sid, check_for_zone=True)
    if parsed_data[0] is False:
        return utils.return_msg(msg=parsed_data[1], status=parsed_data[2])
    else:
        _success, schematic, payload, user_id = parsed_data
        LOG.debug('%s %s %s %s', _success, schematic, payload, user_id)

    config = db_proc.get_configmanager(skm=schematic)

    try:
        sess = DB.session
        for _zn in payload['zones']:
            ssh_user = _zn.get('ssh_user')
            pub = _zn.get('ssh_key_pub')
            pri = _zn.get('ssh_key_pri')
            key_name = _zn.get('key_name')
            ssh_key = db_proc.post_instanceskeys(
                pub=pub,
                pri=pri,
                sshu=ssh_user,
                key_name=key_name
            )
            db_proc.add_item(session=sess, item=ssh_key)

            zone = db_proc.post_zones(
                skm=schematic,
                zon=_zn,
                ssh=ssh_key
            )
            db_proc.add_item(session=sess, item=zone)

            packet = utils.build_cell(
                job='build',
                schematic=schematic,
                zone=zone,
                sshkey=ssh_key,
                config=config
            )
            rpc.default_publisher(message=packet)

    except Exception:
        LOG.error(traceback.format_exc())
        return utils.return_msg(msg='Unexpected Error', status=500)
    else:
        db_proc.commit_session(session=sess)
        msg = 'Application requests have been recieved for Schematic %s' % sid
        return utils.return_msg(msg=msg, status=200)


@mod.route('/v1/schematics/<sid>/zones/<zid>/redeploy', methods=['POST'])
def redeploy_zone(sid=None, zid=None):
    """Redploy a zone.

    This method will interate over an existing zone and ensure that all things
    known in the zone are built and in an active state.

    Method is accessible with POST /v1/schematics/<sid>/zones

    :param sid: ``str`` # schematic ID
    :param zid: ``str`` # Zone ID
    :return json, status: ``tuple``
    """
    parsed_data = utils.zone_basic_handler(sid=sid, zid=zid)
    if parsed_data[0] is False:
        return utils.return_msg(msg=parsed_data[1], status=parsed_data[2])
    else:
        _success, schematic, zone, user_id = parsed_data
        LOG.debug('%s %s %s %s', _success, schematic, zone, user_id)

    config = db_proc.get_configmanager(skm=schematic)
    key = db_proc.get_instanceskeys(zon=zone)
    ints = db_proc.get_instances(zon=zone)
    base_qty = int(zone.quantity)
    numr_qty = len(ints)

    if base_qty > numr_qty:
        difference = base_qty - numr_qty
        packet = utils.build_cell(
            job='redeploy_build',
            schematic=schematic,
            zone=zone,
            sshkey=key,
            config=config
        )
        packet['quantity'] = difference
        LOG.debug(packet)
        rpc.default_publisher(message=packet)
        msg = 'Building %s Instances for Zone %s' % (difference, zone.id)
        return utils.return_msg(msg=msg, status=200)
    elif base_qty < numr_qty:
        difference = numr_qty - base_qty
        packet = utils.build_cell(
            job='redeploy_delete',
            schematic=schematic,
            zone=zone,
            sshkey=key,
            config=config
        )
        instances = [ins.instance_id for ins in ints]
        remove_instances = instances[:difference]
        packet['uuids'] = remove_instances
        LOG.debug(packet)
        remove_ids = [
            ins for ins in ints
            if ins.instance_id in remove_instances
        ]

        try:
            sess = DB.session
            for instance_id in remove_ids:
                db_proc.delete_item(session=sess, item=instance_id)
        except Exception:
            LOG.error(traceback.format_exc())
            return utils.return_msg(msg='Unexpected Error', status=500)
        else:
            rpc.default_publisher(message=packet)
            db_proc.commit_session(session=sess)
            msg = 'Removing %s Instances for Zone %s' % (difference, zone.id)
            return utils.return_msg(msg=msg, status=200)
    else:
        return utils.return_msg(msg='nothing to do', status=200)


@mod.route('/v1/schematics/<sid>/zones/<zid>/resetstate', methods=['POST'])
def reset_zone_state(sid=None, zid=None):
    r"""Reset the state of a zone to active.

    This method will reset the state of an existing zone no matter the current
    state. The new state after invoking this method will be set to
    "ACTIVE RESET"

    Method is accessible with POST /v1/schematics/<sid>/zones

    :param sid: ``str`` # schematic ID
    :param zid: ``str`` # Zone ID
    :return json, status: ``tuple``
    """
    parsed_data = utils.zone_basic_handler(sid=sid, zid=zid)
    if parsed_data[0] is False:
        return utils.return_msg(msg=parsed_data[1], status=parsed_data[2])
    else:
        _success, schematic, zone, user_id = parsed_data
        LOG.debug('%s %s %s %s', _success, schematic, zone, user_id)

    cell = {'zone_state': 'ACTIVE RESET'}
    try:
        sess = DB.session
        db_proc.put_zone(session=sess, zon=zone, put=cell)
    except Exception:
        LOG.error(traceback.format_exc())
        return utils.return_msg(msg='unexpected error', status=500)
    else:
        db_proc.commit_session(session=sess)
        return utils.return_msg(
            msg='Zone State for %s has been Reset' % zid, status=200
        )
