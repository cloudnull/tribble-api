import traceback
from tribble.purveyors import db_proc as db
from tribble.appsetup.start import LOG, _DB


class ZoneState(object):
    def __init__(self, cell):
        self.cell = cell
        schematic = db.get_schematic_id(sid=self.cell['schematic_id'],
                                        uid=self.cell['auth_id'])
        self.zone = db.get_zones_by_id(skm=schematic,
                                       zid=self.cell['zone_id'])

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
        pass
        #self.state_update()

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
