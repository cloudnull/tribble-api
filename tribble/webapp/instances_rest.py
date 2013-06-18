import traceback
from flask import request
from flask.ext.restful import Resource
from tribble.appsetup.start import LOG, QUEUE, _DB
from tribble.purveyors import db_proc
from tribble.webapp import pop_ts, auth_mech, build_cell


class InstancesRest(Resource):
    def delete(self, _sid=None, _zid=None, _iid=None):
        """
        delete method
        """
        if not all([_sid, _zid, _iid]):
            return {'response': 'Missing Information'}, 400

        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'You are not authorized'}, 401
        try:
            _skm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
            if not _skm:
                return {'response': 'No Schematic Found'}, 404
            _zon = db_proc.get_zones_by_id(skm=_skm, zid=_zid)
            if not _zon:
                return {'response': 'No Zone Found'}, 404
            if _zon.zone_state == 'BUILDING':
                return {'response': ("Instance Delete can not be"
                                     " performed because Zone %s has a"
                                     " Pending Status" % _zon.id)}, 200
            if not _zon:
                return {'response': 'No Zone Found'}, 404
            else:
                _con = db_proc.get_configmanager(skm=_skm)
                ints = db_proc.get_instances(zon=_zon)
                ins = [ins.instance_id for ins in ints
                       if ins.instance_id == _iid]
                if not ins:
                    return {'response': 'No Instance Found'}, 404
                jobs = []
                cell = build_cell(job='instance_delete',
                                  schematic=_skm,
                                  zone=_zon,
                                  config=_con)
                cell['uuids'] = ins
                jobs.append(cell)
                QUEUE.put(jobs)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': "Deletes Recieved"}, 203
