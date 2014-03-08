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

from tribble.api import application
from tribble.common.db import db_proc

DB = application.DB
LOG = logging.getLogger('tribble-common')


class ZoneState(object):
    """Perform a status update on a given Zone.

    :param cell: ``dict``
    """

    def __init__(self, cell):
        self.cell = cell
        self.schematic = db_proc.get_schematic_id(
            sid=self.cell['schematic_id'], uid=self.cell['auth_id']
        )
        if self.cell.get('zone_id'):
            self.zone = db_proc.get_zones_by_id(
                skm=self.schematic, zid=self.cell['zone_id']
            )

    def error(self, error_msg):
        """Set zone state to Error.

        :param error_msg: ``str``
        """
        self.cell['zone_state'] = 'ERROR'
        self.cell['zone_msg'] = error_msg
        self.state_update()

    def reconfig(self):
        """Set zone state to Reconfiguring."""
        self.cell['zone_state'] = 'RECONFIGURING'
        self.state_update()

    def pending(self, pending_msg='Waiting for Active Instances'):
        """Set zone state to Building.

        :param pending_msg: ``str``
        """
        self.cell['zone_state'] = 'PENDING'
        self.cell['zone_msg'] = pending_msg
        self.state_update()

    def build(self, build_msg='Under Construction'):
        """Set zone state to Building.

        :param build_msg: ``str``
        """
        self.cell['zone_state'] = 'BUILDING'
        self.cell['zone_msg'] = build_msg
        self.state_update()

    def active(self):
        """Set zone state to Active."""
        ints = db_proc.get_instances(zon=self.zone)
        if int(self.zone.quantity) == len(ints):
            self.cell['zone_state'] = 'ACTIVE'
            self.cell['zone_msg'] = 'Zone is Active'
        else:
            self.cell['zone_state'] = 'DEGRADED'
        self.state_update()

    def delete(self):
        """Set zone state to Deleting."""
        self.cell['zone_state'] = 'DELETING'
        self.state_update()

    def delete_schematic_resource(self):
        """Perform a Schematic delete.

        This will delete a provided Schematic as well as it's configuration
        management row.
        """
        try:
            sess = DB.session
            config = db_proc.get_configmanager(skm=self.schematic)
            db_proc.delete_item(session=sess, item=self.schematic)
            db_proc.delete_item(session=sess, item=config)
        except AttributeError as exp:
            msg = 'Issues while removing Schematic => %s', exp
            LOG.info(msg)
            self.cell['zone_state'] = 'DELETE FAILED'
            self.cell['zone_msg'] = msg
            self.state_update()
        else:
            db_proc.commit_session(session=sess)

    def delete_zone_resource(self):
        """Perform a zone resource delete.

        This will delete a zone as well as it's keys.
        """
        try:
            instances = db_proc.get_instances(zon=self.zone)
            if instances:
                self.cell['zone_state'] = 'DELETE FAILED'
                self.cell['zone_msg'] = (
                    'Found Instance when they should have all been deleted'
                )
                self.state_update()
            else:
                sess = DB.session
                key = db_proc.get_instanceskeys(zon=self.zone)
                db_proc.delete_item(session=sess, item=self.zone)
                db_proc.delete_item(session=sess, item=key)
                db_proc.commit_session(session=sess)
        except AttributeError as exp:
            LOG.error('No Zone To Delete as No Zone was Found ==> %s', exp)

    def state_update(self):
        """Perform a state update."""
        try:
            sess = DB.session
            db_proc.put_zone(session=sess, zon=self.zone, put=self.cell)
        except Exception:
            LOG.error(traceback.format_exc())
        else:
            db_proc.commit_session(session=sess)
