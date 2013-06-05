import traceback
from flask import request
from flask.ext.restful import Resource
from tribble.appsetup.start import LOG, QUEUE, _DB
from tribble.purveyors import db_proc, db_narciss
from tribble.webapp import pop_ts, auth_mech, build_cell


class Instances(Resource):
    def post(self, _sid=None, _zid=None):
        """
        Insert into instances table
        """
        if not _sid:
            return {'response': 'No Schematic specified'}, 400
        auth = auth_mech(hdata=request.data,
                         rdata=request.headers)
        if not auth:
            return {'response': 'Authentication or Data Type Failure'}, 401
        else:
            user_id, _thd = auth
            _hd = _thd['instances']
        try:
            if not all([user_id, _hd]):
                return {'response': ('Missing Information %s %s'
                                     % (user_id, _hd))}, 400
            sess = _DB.session
            for ins in _hd:
                sess = db_proc.add_item(session=sess,
                                        item=db_narciss.post_instance(ins=ins,
                                                                      put=_hd))
                LOG.info('Instance posted ID:%s NAME:%s'
                         % (ins.get('uuid'), ins.get('server_name')))
            db_proc.commit_session(session=sess)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {"response": "instances sucessfully created"}, 201


    def get(self, _sid=None, _zid=None):
        """
        Get all instances that belong to blue_print
        """
        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'Missing Information'}, 400
        try:
            if _sid:
                nskm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
            else:
                return {'response': 'No BluePrint Specified'}, 400
            if not nskm:
                return {'response': 'No BluePrint found'}, 404
            else:
                if _zid:
                    nzons = [db_proc.get_zones_by_id(skm=nskm, zid=_zid)]
                else:
                    nzons = db_proc.get_zones(skm=nskm)

                instances = []
                for nzon in nzons:
                    nints = db_proc.get_instances(zon=nzon)
                    for ins in nints:
                        instances.append(pop_ts(temp=ins.__dict__))
                if not instances:
                    return {"repsonse": "No Instances Found"}
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'instances': instances}


class ServerMaps(Resource):
    def get(self, _sid=None, _zid=None):
        """
        Get all server_maps that belong to a blueprint ID
        """
        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'Missing Information'}, 400
        try:
            if _sid:
                nskm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
            else:
                return {'response': 'No Schematic Specified'}, 400
            if not nskm:
                return {'response': 'No Schematic found'}, 404
            if _zid:
                nzons = [db_proc.get_zones_by_id(skm=nskm, zid=_zid)]
            else:
                nzons = db_proc.get_zones(skm=nskm)
            if not nzons:
                return {'response': 'No Zone found'}, 404
            else:
                narciss_sms = []
                for nzon in nzons:
                    ncon = db_proc.get_configmanager(skm=nskm)
                    nkey = db_proc.get_instanceskeys(zon=nzon)
                    narciss_smaps = {'blue_print_id': nskm.id,
                                     'chef_env': ncon.config_env,
                                     'flavor': nzon.size_id,
                                     'id': nzon.id,
                                     'image_ref': nzon.image_id,
                                     'name_convention': nzon.name_convention,
                                     'quantity': nzon.quantity,
                                     'run_list': nzon.schematic_runlist,
                                     'ssh_user': nkey.ssh_user}
                    narciss_sms.append(narciss_smaps)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'server_maps': narciss_sms}, 200

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
            user_id, _thd = auth
            _hd = _thd['server_map']
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
                    _con = db_proc.get_configmanager(skm=_skm)
                    sess = db_narciss.put_configmanager(session=sess,
                                                        con=_con,
                                                        put=_hd)
                    _ssh = db_proc.get_instanceskeys(zon=_zon)
                    sess = db_proc.put_instanceskeys(session=sess,
                                                     ssh=_ssh,
                                                     put=_hd)
                    sess = db_narciss.put_zone(session=sess,
                                               zon=_zon,
                                               put=_hd,
                                               zput=_zon)
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


class BluePrints(Resource):
    def get(self, _sid=None):
        """
        Look up schematics from Schematic ID and auth ID and return it as a
        Narciss Blueprint
        """
        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'Missing Information'}, 400
        try:
            if _sid:
                nskms = [db_proc.get_schematic_id(sid=_sid, uid=user_id)]
            else:
                nskms = db_proc.get_schematics(uid=user_id)
            if not nskms:
                return {'response': 'No Schematics found'}, 404
            retskms = []
            for nskm in nskms:
                ncon = db_proc.get_configmanager(skm=nskm)
                narciss_bp = {'api_key': nskm.cloud_key,
                              'auth_url': nskm.cloud_url,
                              'chef_key': ncon.config_key,
                              'chef_server': ncon.config_server,
                              'chef_username': ncon.config_username,
                              'cloud_provider': nskm.cloud_provider,
                              'id': nskm.id,
                              'region': nskm.cloud_region,
                              'tenant': nskm.cloud_tenant,
                              'user_name': nskm.cloud_username,
                              'validation_client_name': ncon.config_clientname,
                              'validation_key': ncon.config_validation_key}
                retskms.append(narciss_bp)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            if not _sid is None:
                return {'blue_prints': retskms[0]}
            else:
                return {'blue_prints': retskms}

    def delete(self, _sid):
        """
        Delete a bluePrint and all assosiated Server Maps
        """
        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'Missing Information'}, 400
        else:
            from tribble.webapp.schematics_rest import SchematicsRest
            return SchematicsRest().delete(_sid)

    def post(self):
        """
        create a blueprint
        Store if monitoring is turned on or off, set it to off on blueprint
        create, client will. Set to 1 if it's enabled to prevent race condition
        of monitor deleting bootstrapped instances

        UN-Used Variables From Narciss :
        blue_print_id,
        ##Get http_check_port is critical value
        _bpv['monitoring']['http_check_critical'],
        ##Get http_check_port value
        _bpv['monitoring']['http_check'],
        ##nic to monitor (public||private)
        _bpv['interface'],
        ##Get monitor enabled value
        0,
        ##Get ping monitor value
        _bpv['monitoring']['ping_true'],
        ##Determine if ping is critical
        _bpv['monitoring']['ping_critical'],
        ##Determine if port monitor enabled
        _bpv['monitoring']['port'],
        ##Determine if port is critical
        _bpv['monitoring']['port_critical'],
        """
        auth = auth_mech(hdata=request.data,
                         rdata=request.headers)
        if not auth:
            return {'response':
                'Failure on Authentication and or Validation'}, 401
        else:
            user_id, _thd = auth
            _hd = _thd['blue_print']
        try:
            if not all([user_id, _hd]):
                return {'response': 'Missing Information, Not Acceptable'}, 406
            LOG.debug('NARCISS POST RECIEVED ==> %s' % _hd)
            sess = _DB.session
            ncon = db_narciss.post_configmanager(session=sess, post=_hd)
            sess = db_proc.add_item(session=sess, item=ncon)
            nskm = db_narciss.post_schematic(session=sess,
                                             con=ncon,
                                             uid=user_id,
                                             post=_hd)
            sess = db_proc.add_item(session=sess, item=nskm)
            if _hd.get('server_map'):
                for _zn in _hd['server_map']:
                    nssh = db_narciss.post_instanceskeys(session=sess, post=_hd)
                    sess = db_proc.add_item(session=sess, item=nssh)

                    nzon = db_narciss.post_zones(skm=nskm,
                                                 zon=_zn,
                                                 ssh=nssh)
                    sess = db_proc.add_item(session=sess, item=nzon)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            db_proc.commit_session(session=sess)
            return {'response': ('BluePrint requests have been recieved'
                                 ' and %s has been built' % nskm.id)}, 201
