import traceback
from flask import request
from flask.ext.restful import Resource
from tribble.appsetup.start import LOG, QUEUE, _DB
from tribble.purveyors import db_proc
from tribble.webapp import pop_ts, auth_mech, build_cell


class SchematicsRest(Resource):
    def get(self, _sid=None):
        """
        get method
        """
        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'Missing Information'}, 400
        try:
            if _sid:
                skms = [db_proc.get_schematic_id(sid=_sid, uid=user_id)]
            else:
                skms = db_proc.get_schematics(uid=user_id)
            if not skms:
                return {'response': 'No Schematic(s) Found'}, 404
            retskms = []
            for _skm in skms:
                if _skm:
                    dskm = pop_ts(temp=_skm.__dict__)
                    zon = db_proc.get_zones(skm=_skm)
                    if zon:
                        _dz = dskm['num_zones'] = len(zon)
                    con = db_proc.get_configmanager(skm=_skm)
                    if con:
                        dskm['config_manager'] = pop_ts(temp=con.__dict__)
                        _con = dskm['config_manager']
                        if _con.get('config_key'):
                            _con['config_key'] = 'KEY FOUND'
                        if _con.get('config_validation_key'):
                            _con['config_validation_key'] = 'KEY FOUND'
                    if dskm:
                        retskms.append(dskm)
            if not retskms:
                return {'response': 'No Schematic(s) Found'}, 404
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': retskms}, 200

    def delete(self, _sid=None):
        """
        Delete a Cluster
        """
        if not _sid:
            return {'response': 'Missing Information'}, 400

        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'Missing Information'}, 400
        try:
            _skm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
            if not _skm:
                return {'response': 'No Schematic Found'}, 404
            _con = db_proc.get_configmanager(skm=_skm)
            _zons = db_proc.get_zones(skm=_skm)
            sess = _DB.session
            if _zons:
                jobs = []
                for zone in _zons:
                    ints = db_proc.get_instances(zon=zone)
                    if ints:
                        for ins in ints:
                            sess = db_proc.delete_item(session=sess, item=ins)
                        cell = build_cell(job='delete',
                                          schematic=_skm,
                                          zone=zone,
                                          config=_con)
                        cell['uuids'] = [ins.instance_id for ins in ints]
                        jobs.append(cell)
                    sess = db_proc.delete_item(session=sess, item=zone)
                    key = db_proc.get_instanceskeys(zon=zone)
                    sess = db_proc.delete_item(session=sess, item=key)
                QUEUE.put(jobs)
            sess = db_proc.delete_item(session=sess, item=_skm)
            sess = db_proc.delete_item(session=sess, item=_con)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            db_proc.commit_session(session=sess)
            return {'response': "Deletes Recieved"}, 203

    def put(self, _sid):
        """
        Update Cluster
        """
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
                return {'response': 'Request Not Valid'}, 400
            else:
                _skm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
                if not _skm:
                    return {'response': 'No Schematic Found'}, 404
                else:
                    _con = db_proc.get_configmanager(skm=_skm)
                    _zons = db_proc.get_zones(skm=_skm)
                    sess = _DB.session
                sess = db_proc.put_schematic_id(session=sess,
                                                skm=_skm,
                                                put=_hd)
                sess = db_proc.put_configmanager(session=sess,
                                                 con=_con,
                                                 put=_hd)
                if _zons:
                    for _zon in _zons:
                        sess = db_proc.put_zone(session=sess,
                                                zon=_zon,
                                                put=_hd)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            db_proc.commit_session(session=sess)
            return {'response': "Updates Recieved"}, 201

    def post(self):
        """
        Post a Schematic, if a zone is present in the POST, then post a zone.
        """
        auth = auth_mech(hdata=request.data,
                         rdata=request.headers)
        if not auth:
            return {'response':
                'Failure on Authentication and or Validation'}, 401
        else:
            user_id, _hd = auth
        try:
            if not all([user_id, _hd]):
                return {'response':
                    'Missing Information, Not Acceptable'}, 406
            LOG.info(_hd)
            sess = _DB.session
            con = db_proc.post_configmanager(session=sess, post=_hd)
            sess = db_proc.add_item(session=sess, item=con)

            skm = db_proc.post_schematic(session=sess,
                                         con=con,
                                         uid=user_id,
                                         post=_hd)
            sess = db_proc.add_item(session=sess, item=skm)

            if 'zones' in _hd:
                jobs = []
                for _zn in _hd['zones']:
                    key_data = _zn['instances_keys']
                    _ssh_user = key_data.get('ssh_user')
                    pub = key_data.get('ssh_key_pub')
                    ssh = db_proc.post_instanceskeys(pub=pub,
                                                     sshu=_ssh_user,
                                                     key_data=key_data)
                    sess = db_proc.add_item(session=sess, item=ssh)
                    zon = db_proc.post_zones(skm=skm,
                                             zon=_zn,
                                             ssh=ssh)
                    sess = db_proc.add_item(session=sess, item=zon)
                    packet = build_cell(job='build',
                                        schematic=skm,
                                        zone=zon,
                                        sshkey=ssh,
                                        config=con)
                    jobs.append(packet)
                LOG.debug('JOB TO DO ==> %s' % jobs)
                QUEUE.put(jobs)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            db_proc.commit_session(session=sess)
            return {'response': ('Application requests have been recieved'
                                 ' and Schematic %s has been built'
                                 % skm.id)}, 200
