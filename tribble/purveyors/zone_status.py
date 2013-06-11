import traceback
from tribble.purveyors import db_proc as db
from tribble.appsetup.start import LOG, _DB


class ZoneState(object):
    def __init__(self, cell):
        self.cell = cell
        self.schematic = db.get_schematic_id(sid=self.cell['schematic_id'],
                                        uid=self.cell['auth_id'])
        if self.cell.get('zone_id'):
            self.zone = db.get_zones_by_id(skm=self.schematic,
                                           zid=self.cell['zone_id'])

    def _reconfig(self):
        self.cell['zone_state'] = 'RECONFIGURING'
        self.state_update()

    def _build(self):
        self.cell['zone_state'] = 'BUILDING'
        self.state_update()

    def _active(self):
        ints = db.get_instances(zon=self.zone)
        if int(self.zone.quantity) == len(ints):
            self.cell['zone_state'] = 'ACTIVE'
        else:
            self.cell['zone_state'] = 'DEGRADED'
        self.state_update()

    def _delete(self):
        self.cell['zone_state'] = 'DELETING'
        self.state_update()

    def _delete_resource(self, skm=False):
        sess = _DB.session
        try:
            ints = db.get_instances(zon=self.zone)
            if not len(ints) == 0:
                self.cell['zone_state'] = 'DELETE FAILED'
                self.cell['zone_msg'] = ('Found Instance when they should'
                                         ' have all been deleted')
                self.state_update()
            sess = db.delete_item(session=sess, item=self.zone)
            key = db.get_instanceskeys(zon=self.zone)
            sess = db.delete_item(session=sess, item=key)
        except AttributeError, exp:
            LOG.info('No Zone To Delete as No Zone was Found ==> %s' % exp)

        if skm:
            _con = db.get_configmanager(skm=self.schematic)
            sess = db.delete_item(session=sess, item=self.schematic)
            sess = db.delete_item(session=sess, item=_con)
        db.commit_session(session=sess)

    def state_update(self):
        try:
            sess = _DB.session
            db.put_zone(session=sess,
                        zon=self.zone,
                        put=self.cell)
        except Exception:
            LOG.error(traceback.format_exc())
        else:
            db.commit_session(session=sess)
