import traceback
from flask import request
from flask.ext.restful import Resource
from tribble.appsetup.start import _DB, LOG, QUEUE, STATS
from tribble.operations import utils
from tribble.purveyors import db_proc
from tribble.webapp import pop_ts, parse_dict_list, auth_mech, build_cell


class ZonesRest(Resource):
    def get(self, _sid=None, _zid=None):
        """
        get method
        """
        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'Missing Information'}, 400
        try:
            if _sid:
                _skm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
            else:
                return {'response': 'No Schematic Specified'}, 400

            if not _skm:
                return {'response': 'No Schematic found'}, 404
            else:
                retskmss = []
                if _zid:
                    zon = db_proc.get_zones_by_id(skm=_skm, zid=_zid)
                    if zon:
                        zon = [zon]
                else:
                    zon = db_proc.get_zones(skm=_skm)
                if not zon:
                    return {'response': 'No Zone found'}, 404
                else:
                    for zone in zon:
                        dzone = pop_ts(zone.__dict__)
                        ints = db_proc.get_instances(zon=zone)
                        if ints:
                            _di = dzone['instances'] = []
                            for inst in ints:
                                _di.append(pop_ts(inst.__dict__))
                            dzone['num_instances'] = len(_di)
                        retskmss.append(dzone)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': retskmss}, 200

    def delete(self, _sid=None, _zid=None):
        """
        Delete a Zone
        """
        if not _sid:
            return {'response': 'Missing Information'}, 400

        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'You are not authorized'}, 401
        try:
            _skm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
            if not _skm:
                return {'response': 'No Schematic Found'}, 404
            _zon = db_proc.get_zones_by_id(skm=_skm, zid=_zid)
            if _zon.zone_state == 'BUILDING':
                return {'response': ("Zone Delete can not be"
                                     " performed because Zone %s has a"
                                     " Pending Status" % _zon.id)}, 200
            if not _zon:
                return {'response': 'No Zone Found'}, 404
            else:
                _con = db_proc.get_configmanager(skm=_skm)
                ints = db_proc.get_instances(zon=_zon)
                jobs = []
                cell = build_cell(job='zone_delete',
                                  schematic=_skm,
                                  zone=_zon,
                                  config=_con)
                cell['uuids'] = [ins.instance_id for ins in ints]
                jobs.append(cell)
                QUEUE.put(jobs)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': "Deletes Recieved"}, 203

    def put(self, _sid=None, _zid=None):
        """
        Update a Zone
        """
        if not _sid:
            return {'response': 'No Schematic specified'}, 400
        if not _zid:
            return {'response': 'No Zone specified'}, 400

        auth = auth_mech(hdata=request.data,
                         rdata=request.headers)
        if not auth:
            return {'response': 'Authentication or Data Type Failure'}, 401
        else:
            user_id, _hd = auth
        try:
            if not all([user_id, _hd]):
                return {'response': ('Missing Information %s %s'
                                     % (user_id, _hd))}, 400
            else:
                _skm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
            if _skm:
                _zon = db_proc.get_zones_by_id(skm=_skm, zid=_zid)
                if _zon:
                    sess = _DB.session
                    sess = db_proc.put_zone(session=sess,
                                            zon=_zon,
                                            put=_hd)
                else:
                    return {'response': 'No Zone Found'}, 404
            else:
                return {'response': 'No Schematic Found'}, 404
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            db_proc.commit_session(session=sess)
            return {'response': "Updates Recieved"}, 201

    def post(self, _sid=None, _zid=None):
        """
        Post a Zone
        """
        if _zid:
            return {'response': 'Failure, Method does not take arguments'}, 400
        if not _sid:
            return {'response': 'No Schematic specified'}, 400
        auth = auth_mech(hdata=request.data,
                         rdata=request.headers)
        if not auth:
            return {'response': 'Authentication or Data Type Failure'}, 401
        else:
            user_id, _hd = auth
        try:
            if not all([user_id, _hd]):
                return {'response': ('Missing Information %s %s'
                                     % (user_id, _hd))}, 400
            else:
                LOG.info(_hd)
                _skm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
                if not _skm:
                    return {'response': 'No Schematic Found'}, 404
                else:
                    sess = _DB.session
            if 'zones' in _hd:
                jobs = []
                _con = db_proc.get_configmanager(skm=_skm)
                for _zn in _hd['zones']:
                    key_data = _zn['instances_keys']
                    _ssh_user = key_data.get('ssh_user')
                    pub = key_data.get('ssh_key_pub')
                    _ssh = db_proc.post_instanceskeys(pub=pub,
                                                      sshu=_ssh_user,
                                                      key_data=key_data)
                    sess = db_proc.add_item(session=sess, item=_ssh)

                    _zon = db_proc.post_zones(skm=_skm,
                                              zon=_zn,
                                              ssh=_ssh)
                    sess = db_proc.add_item(session=sess, item=_zon)

                    packet = build_cell(job='build',
                                        schematic=_skm,
                                        zone=_zon,
                                        sshkey=_ssh,
                                        config=_con)
                    jobs.append(packet)
                    LOG.debug(packet)
                QUEUE.put(jobs)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            db_proc.commit_session(session=sess)
            STATS.gauge('Zones', 1, delta=True)
            return {'response': ('Application requests have been recieved'
                                 ' for Schematic %s'
                                 % _sid)}, 200
