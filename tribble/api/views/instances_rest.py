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

from tribble.api import utils
from tribble.common.db import db_proc
from tribble.common import rpc
from tribble.common import system_config


mod = flask.Blueprint('isntances', __name__)
LOG = logging.getLogger('tribble-api')
CONFIG = system_config.ConfigurationSetup()
DEFAULT = CONFIG.config_args()


@mod.route('/v1/schematics/<sid>/zones/<zid>/instances/<iid>',
           methods=['delete'])
def instance_delete(sid=None, zid=None, iid=None):
    """Delete an Instance from a Zone.

    :param sid: ``str`` # schematic ID
    :param zid: ``str`` # Zone ID
    :param iid: ``str`` # Instance ID
    :return json, status: ``tuple``
    """

    if not all([sid, zid, iid]):
        check_all = [check for check in sid, zid, iid if not check]
        return utils.return_msg(
            msg='missing Information %s' % check_all, status=400
        )

    user_id = utils.auth_mech(rdata=flask.request.headers)
    if not user_id:
        return utils.return_msg(msg='missing information', status=400)

    schematic = db_proc.get_schematic_id(sid=sid, uid=user_id)
    if not schematic:
        return utils.return_msg(msg='no schematic found', status=404)

    zone = db_proc.get_zones_by_id(skm=schematic, zid=zid)
    if not zone:
        return utils.return_msg(msg='No Zone Found', status=404)
    elif zone.zone_state == 'BUILDING':
        build_response = ("Instance Delete can not be performed because Zone"
                          " %s has a Pending Status" % zone.id)
        return utils.return_msg(msg=build_response, status=200)

    instances = db_proc.get_instances(zon=zone)
    instance_id = [
        instance.instance_id for instance in instances
        if instance.instance_id == iid
    ]
    if not instance_id:
        return utils.return_msg(msg='No Instance Found', status=404)

    try:
        config = db_proc.get_configmanager(skm=schematic)
        cell = utils.build_cell(
            job='instance_delete',
            schematic=schematic,
            zone=zone,
            config=config
        )
        cell['uuids'] = instance_id

    except Exception:
        LOG.error(traceback.format_exc())
        return utils.return_msg(msg='Unexpected Error', status=500)
    else:
        rpc.default_publisher(message=cell)
        return utils.return_msg(msg='Deletes Recieved', status=203)
