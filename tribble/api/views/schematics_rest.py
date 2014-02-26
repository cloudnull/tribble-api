# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import traceback
import logging

from flask import Blueprint
from flask import request

from tribble.common import system_config

from tribble.common.db import db_proc
from tribble.api.application import DB
from tribble.api import utils


mod = Blueprint('schematics', __name__)
LOG = logging.getLogger('tribble-api')
CONFIG = system_config.ConfigureationSetup()
DEFAULT = CONFIG.config_args()


def _zone_builder(session, schematic, con, payload):
    build_zones = []
    for zone in payload['zones']:
        zone = utils.encoder(obj=zone)
        LOG.debug(zone)
        _ssh_user = zone.get('ssh_user')
        pub = zone.get('ssh_key_pub')
        key_name = zone.get('key_name')

        ssh = db_proc.post_instanceskeys(
            pub=pub,
            sshu=_ssh_user,
            key_name=key_name
        )
        db_proc.add_item(session=session, item=ssh)

        zone = db_proc.post_zones(skm=schematic, zon=zone, ssh=ssh)
        db_proc.add_item(session=session, item=zone)

        packet = utils.build_cell(
            job='build',
            schematic=schematic,
            zone=zone,
            sshkey=ssh,
            config=con
        )
        build_zones.append(packet)
    return build_zones


@mod.route('/v1/schematics', methods=['GET'])
def schematics_get():
    """get method."""

    user_id = utils.auth_mech(DB, rdata=request.headers)
    if not user_id:
        return utils.return_msg(msg='missing information', status=400)

    schematics = db_proc.get_schematics(uid=user_id)
    if not schematics:
        return utils.return_msg(msg='no schematic(s) found', status=404)

    try:
        schematics_list = [
            utils.build_schematic_list(schematic)
            for schematic in schematics if schematic
        ]
    except Exception:
        LOG.error(traceback.format_exc())
        return utils.return_msg(msg='unexpected error', status=500)
    else:
        if not schematics_list:
            return utils.return_msg(msg='no schematic(s) found', status=404)
        else:
            return utils.return_msg(msg=schematics_list, status=200)


@mod.route('/v1/schematics/<sid>', methods=['GET'])
def schematic_get(sid=None):
    if not sid:
        return utils.return_msg(msg='missing information', status=400)

    user_id = utils.auth_mech(DB, rdata=request.headers)
    if not user_id:
        return utils.return_msg(msg='missing information', status=400)

    schematic = db_proc.get_schematic_id(sid=sid, uid=user_id)
    if not schematic:
        return utils.return_msg(msg='no schematic found', status=404)
    else:
        _schematic = utils.pop_ts(temp=schematic.__dict__)
        return utils.return_msg(msg=_schematic, status=200)


@mod.route('/v1/schematics/<sid>', methods=['DELETE'])
def schematic_delete(sid=None):
    """Delete a Schematic."""

    if not sid:
        return utils.return_msg(msg='missing information', status=400)

    user_id = utils.auth_mech(DB, rdata=request.headers)
    if not user_id:
        return utils.return_msg(msg='missing information', status=400)

    schematic = db_proc.get_schematic_id(sid=sid, uid=user_id)
    if not schematic:
        return utils.return_msg(msg='no schematic found', status=404)

    try:
        zones = db_proc.get_zones(skm=schematic)
        if zones:
            zone_ids = [zone.id for zone in zones]
            build_response = ('can not delete the schematic, you have an'
                              ' active zone(s): %s' % zone_ids)
            return utils.return_msg(msg=build_response, status=405)

        sess = DB.session
        db_proc.delete_item(session=sess, item=schematic)
    except Exception:
        LOG.error(traceback.format_exc())
        return utils.return_msg(msg='unexpected error', status=500)
    else:
        # TODO(kevin) USE KOMBU
        # QUEUE.put(cell)
        db_proc.commit_session(session=sess)
        return utils.return_msg(msg='deletes received', status=203)


@mod.route('/v1/schematics/<sid>', methods=['PUT'])
def schematic_put(sid=None):
    """Update a schematic.

    if a zone is in the put data add the zone to the schematic.
    The addition of a zone on a put will not build the zone automatically.
    """

    if not sid:
        return utils.return_msg(msg='missing information', status=400)

    auth = utils.auth_mech(
        models=DB, hdata=request.data, rdata=request.headers
    )
    if not auth:
        return utils.return_msg(
            msg='Authentication or Data Type Failure',
            status=401
        )
    else:
        user_id, payload = auth

    schematic = db_proc.get_schematic_id(sid=sid, uid=user_id)
    if not schematic:
        return utils.return_msg(msg='no schematic found', status=404)
    
    if not all([user_id, payload]):
        build_response = 'missing information %s %s' % (user_id, payload)
        return utils.return_msg(msg=build_response, status=400)

    try:
        sess = DB.session
        con = db_proc.get_configmanager(skm=schematic)
        db_proc.put_schematic_id(session=sess, skm=schematic, put=payload)
        db_proc.put_configmanager(session=sess, con=con, put=payload)
        if 'zones' in payload:
            _zone_builder(
                session=sess, schematic=schematic, con=con, payload=payload
            )
    except Exception:
        LOG.error(traceback.format_exc())
        return utils.return_msg(msg='Unexpected Error', status=500)
    else:
        db_proc.commit_session(session=sess)
        return utils.return_msg(msg='Updates Recieved', status=201)


@mod.route('/v1/schematics', methods=['POST'])
def schematic_post():
    """Post a Schematic, if a zone is present in the POST, then post a zone."""

    auth = utils.auth_mech(
        models=DB, hdata=request.data, rdata=request.headers
    )
    if not auth:
        return utils.return_msg(
            msg='Authentication or Data Type Failure',
            status=401
        )
    else:
        user_id, payload = auth

    if not all([user_id, payload]):
        build_response = 'missing information %s %s' % (user_id, payload)
        return utils.return_msg(msg=build_response, status=400)

    try:
        sess = DB.session
        con = db_proc.post_configmanager(post=payload)
        db_proc.add_item(session=sess, item=con)
        schematic = db_proc.post_schematic(
            con=con,
            uid=user_id,
            post=payload
        )
        db_proc.add_item(session=sess, item=schematic)
        if 'zones' in payload:
            build_zones = _zone_builder(
                session=sess, schematic=schematic, con=con, payload=payload
            )
            # TODO(kevin) USE KOMBU
            # QUEUE.put(build_zones)

    except Exception:
        LOG.error(traceback.format_exc())
        return utils.return_msg(msg='Unexpected Error', status=500)
    else:
        db_proc.commit_session(session=sess)
        build_response = ('Application requests have been recieved and'
                          ' Schematic %s has been built' % schematic.id)
        return utils.return_msg(msg=build_response, status=200)
