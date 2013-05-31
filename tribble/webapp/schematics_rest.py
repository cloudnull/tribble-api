import traceback
from flask import request
from sqlalchemy import and_
from flask.ext.restful import Resource
from tribble.db.models import CloudAuth, Schematics, ConfigManager
from tribble.db.models import Instances, InstancesKeys, Zones
from tribble.appsetup.start import _DB, LOG, QUEUE
from tribble.operations import utils
from tribble.webapp import pop_ts, parse_dict_list, auth_mech, build_cell


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
                skms = Schematics.query.filter(
                    Schematics.auth_id == user_id,
                    Schematics.id == _sid).all()
            else:
                skms = Schematics.query.filter(
                    Schematics.auth_id == user_id).all()
            if not skms:
                return {'response': 'No Schematics found'}, 400
            retskms = []
            for _skm in skms:
                if _skm:
                    dskm = pop_ts(_skm.__dict__)
                    zon = Zones.query.filter(
                        Zones.schematic_id == _skm.id).all()
                    if zon:
                        _dz = dskm['num_zones'] = len(zon)
                    con = ConfigManager.query.filter(
                        ConfigManager.id == _skm.config_id).first()
                    if con:
                        dskm['config_manager'] = pop_ts(con.__dict__)
                retskms.append(dskm)
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
            _skm = Schematics.query.filter(
                Schematics.auth_id == user_id).filter(
                Schematics.id == _sid).first()
            if not _skm:
                return {'response': 'No Schematic Found'}, 404
            _cons = ConfigManager.query.filter(
                ConfigManager.id == _skm.config_id).first()
            zon = Zones.query.filter(
                Zones.schematic_id == _skm.id).all()
            if zon:
                for zone in zon:
                    insts = Instances.query.filter(
                        Instances.zone_id == zone.id).all()
                    if insts:
                        for ins in insts:
                            _DB.session.delete(ins)
                            _DB.session.flush()
                        cell = build_cell(job='delete',
                                          schematic=_skm,
                                          zone=zone)
                        cell['uuids'] = [ins.instance_id for ins in insts]
                        QUEUE.put(cell)
                    _DB.session.delete(zone)
                    _DB.session.flush()
                    key = InstancesKeys.query.filter(
                        InstancesKeys.id == zone.credential_id).first()
                    _DB.session.delete(key)
            _DB.session.delete(_skm)
            _DB.session.flush()
            _DB.session.delete(_cons)
            _DB.session.flush()
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            _DB.session.commit()
            return {'response': "Deletes Recieved"}, 203

    def put(self, _sid):
        """
        Update Cluster
        """
        if not _sid:
            return {'response': 'Missing Information'}, 400

        auth = auth_mech(hdata=request.data,
                         rdata=request.headers)
        if not auth:
            return {'response': 'Missing Information'}, 400
        else:
            user_id, _hd = auth
        try:
            if not all([user_id, _hd]):
                return {'response': 'Request Not Valid'}, 400
            else:
                _skm = Schematics.query.filter(
                    Schematics.auth_id == user_id).filter(
                    Schematics.id == _sid).first()

            if _skm:
                _skm.cloud_key = _hd.get('cloud_key', _skm.cloud_key)
                _skm.cloud_provider = _hd.get('cloud_provider',
                                               _skm.cloud_provider)
                _skm.cloud_version = _hd.get('cloud_version',
                                             _skm.cloud_version)
                _skm.cloud_region = _hd.get('cloud_region',
                                             _skm.cloud_region)
                _skm.cloud_tenant = _hd.get('cloud_tenant',
                                             _skm.cloud_tenant)
                _skm.cloud_url = _hd.get('cloud_url', _skm.cloud_url)
                _skm.cloud_username = _hd.get('cloud_username',
                                               _skm.cloud_username)
                _DB.session.add(_skm)
                _DB.session.flush()

                _con = ConfigManager.query.filter(
                        ConfigManager.id == _skm.config_id).first()
                if _con:
                    _con.config_env = _hd.get('config_env', _skm.config_env)
                    _con.config_key = _hd.get('config_key', _skm.config_key)
                    _con.config_server = _hd.get('config_server',
                                                  _skm.config_server)
                    _con.config_username = _hd.get('config_username',
                                                    _skm.config_username)
                    _con.config_clientname = _hd.get(
                        'config_clientname', _con.config_validation_clientname)
                    _con.config_validation_key = _hd.get(
                        'config_validation_key',
                        _con.config_validation_key)
                    _DB.session.add(_con)
                    _DB.session.flush()

                if 'zones' in _hd:
                    zone_ids = [_zn['id'] for _zn in _hd['zones']
                                if 'id' in _zn]
                    zon = Zones.query.filter(
                        and_(Zones.schematic_id == _skm.id,
                             Zones.id.in_(zone_ids))).all()
                    for _zon in zon:
                        for zone in _hd['zones']:
                            if zone['id'] == _zon.id:
                                _dz = zone
                                _zon.quantity = _dz.get(
                                    'quantity',
                                    _zon.quantity)
                                _zon.image_id = _dz.get(
                                    'image_id', _zon.image_id)
                                _zon.name_convention = _dz.get(
                                    'name_convention',
                                    _zon.name_convention)
                                _zon.security_groups = _hd.get(
                                    'security_groups'),
                                _zon.inject_files = _hd.get(
                                    'inject_files'),
                                _zon.cloud_networks = _hd.get(
                                    'cloud_networks'),
                                _zon.cloud_init = _hd.get(
                                    'cloud_init'),
                                _zon.quantity = _dz.get(
                                    'quantity', _zon.quantity)
                                _zon.schematic_runlist = _dz.get(
                                    'schematic_runlist',
                                    _zon.schematic_runlist)
                                _zon.schematic_script = _dz.get(
                                    'schematic_script',
                                    _zon.schematic_script)
                                _zon.zone_name = _dz.get(
                                    'zone_name',
                                    utils.rand_string(length=20))
                                _zon.size_id = _dz.get(
                                    'size_id',
                                    _zon.size_id)
                                _DB.session.add(_zon)
                                _DB.session.flush()
                _DB.session.commit()
            else:
                return {'response': 'No Schematic Found'}, 400
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': "Updates Recieved"}, 201

    def post(self):
        """
        Post a Cluster
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
            con = ConfigManager(config_key=_hd.get('config_key'),
                                config_server=_hd.get('config_server'),
                                config_username=_hd.get('config_username'),
                                config_clientname=_hd.get('config_clientname'),
                                config_validation_key=_hd.get(
                                    'config_validation_key'))
            _DB.session.add(con)
            _DB.session.flush()

            skm = Schematics(auth_id=user_id,
                             config_id=con.id,
                             cloud_key=_hd.get('cloud_key'),
                             cloud_url=_hd.get('cloud_url'),
                             cloud_username=_hd.get('cloud_username'),
                             cloud_provider=_hd.get('cloud_provider'),
                             cloud_version=_hd.get('cloud_version'),
                             cloud_region=_hd.get('cloud_region'),
                             cloud_tenant=_hd.get('cloud_tenant',
                                                  _hd.get('cloud_username')))
            _DB.session.add(skm)
            _DB.session.flush()

            if 'zones' in _hd:
                for _zn in _hd['zones']:
                    key_data = _zn['instances_keys']
                    _ssh_user = key_data.get('ssh_user')
                    pri = key_data.get('ssh_key_pri')
                    pub = key_data.get('ssh_key_pub')
                    if not pri:
                        from tribble.operations import fabrics
                        pub, pri = fabrics.KeyGen().build_ssh_key()
                    ssh = InstancesKeys(ssh_user=_ssh_user,
                                        ssh_key_pri=pri,
                                        ssh_key_pub=pub,
                                        key_name=key_data.get('key_name'))
                    _DB.session.add(ssh)
                    _DB.session.flush()

                    zon = Zones(schematic_id=skm.id,
                                schematic_runlist=_zn.get('schematic_runlist'),
                                schematic_script=_zn.get('schematic_script'),
                                zone_name=_zn.get('zone_name',
                                                  utils.rand_string(length=20)),
                                security_groups=_zn.get('security_groups'),
                                inject_files=_zn.get('inject_files'),
                                cloud_networks=_zn.get('cloud_networks'),
                                cloud_init=_zn.get('cloud_init'),
                                size_id=_zn.get('size_id'),
                                image_id=_zn.get('image_id'),
                                name_convention=_zn.get('name_convention'),
                                quantity=_zn.get('quantity'),
                                credential_id=ssh.id)
                    _DB.session.add(zon)
                    _DB.session.flush()

                    packet = build_cell(job='build',
                                        schematic=skm,
                                        zone=zon,
                                        sshkey=ssh,
                                        config=con)
                    LOG.debug(packet)
                    QUEUE.put(packet)
            _DB.session.commit()
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': ('Application requests have been recieved'
                                 ' and Schematic %s has been built'
                                 % skm.id)}, 200
