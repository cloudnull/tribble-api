import traceback
from flask import request
from flask.ext.restful import Resource
from tribble.db.models import CloudAuth, Schematics
from tribble.db.models import Instances, InstancesKeys, Zones
from tribble.appsetup.start import _DB, LOG, QUEUE
from tribble.operations import utils
from tribble.webapp import pop_ts, parse_dict_list, auth_mech


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
                skmss = Schematics.query.filter(
                    Schematics.auth_id == user_id,
                    Schematics.id == _sid).first()
            else:
                return {'response': 'No Schematic Specified'}, 400

            if not skmss:
                return {'response': 'No Schematic found'}, 404
            else:
                retskmss = []
                if _zid:
                    zon = Zones.query.filter(
                        Zones.schematic_id == skmss.id,
                        Zones.id == _zid).all()
                else:
                    zon = Zones.query.filter(
                        Zones.schematic_id == skmss.id).all()
                if not zon:
                    return {'response': 'No Zone found'}, 404
                else:
                    for zone in zon:
                        dzone = pop_ts(zone.__dict__)
                        insts = Instances.query.filter(
                            Instances.zone_id == zone.id).all()
                        if insts:
                            _di = dzone['instances'] = []
                            for inst in insts:
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
            _skms = Schematics.query.filter(
                Schematics.auth_id == user_id).filter(
                Schematics.id == _sid).first()
            if not _skms:
                return {'response': 'No Schematic Found'}, 404
            zon = Zones.query.filter(
                Zones.schematic_id == _skms.id,
                Zones.id == _zid).first()
            if not zon:
                return {'response': 'No Zone Found'}, 404
            else:
                insts = Instances.query.filter(
                    Instances.zone_id == _zid).all()
                if insts:
                    for ins in insts:
                        _DB.session.delete(ins)
                        _DB.session.flush()
                    cell = {'id': _skms.id,
                            'cloud_key': _skms.cloud_key,
                            'cloud_username': _skms.cloud_username,
                            'cloud_region': _skms.cloud_region,
                            'provider': _skms.cloud_provider,
                            'uuids': [ins.instance_id for ins in insts],
                            'job': 'delete'}
                    QUEUE.put(cell)
                key = InstancesKeys.query.filter(
                    InstancesKeys.id == zon.credential_id).first()
                _DB.session.delete(zon)
                _DB.session.flush()
                _DB.session.delete(key)
                _DB.session.flush()
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            _DB.session.commit()
            return {'response': "Deletes Recieved"}, 203

    def put(self, _sid=None, _zid=None):
        """
        Update a Zone
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
                return {'response': ('Missing Information %s %s'
                                     % (user_id, _hd))}, 400
            else:
                skmss = Schematics.query.filter(
                    Schematics.auth_id == user_id).filter(
                    Schematics.id == _sid).first()
            if skmss:
                if _zid:
                    zon = Zones.query.filter(
                        Zones.schematic_id == skmss.id,
                        Zones.id == _zid).first()
                    if zon:
                        zon.quantity = _hd.get('quantity', zon.quantity)
                        zon.image_id = _hd.get('image_id', zon.image_id)
                        zon.name_convention = _hd.get('name_convention',
                                                      zon.name_convention)
                        zon.quantity = _hd.get('quantity', zon.quantity)
                        zon.schematic_runlist = _hd.get('schematic_runlist',
                                                        zon.schematic_runlist)
                        zon.schematic_script = _hd.get('schematic_script',
                                                       zon.schematic_script)
                        zon.zone_name = _hd.get('zone_name',
                                                 utils.rand_string(length=20))
                        zon.size_id = _hd.get('size_id', zon.size_id)
                        _DB.session.add(zon)
                        _DB.session.flush()
                        _DB.session.commit()
                    else:
                        return {'response': 'No Zone Found'}, 404
                else:
                    return {'response': 'No Zone specified'}, 400
            else:
                return {'response': 'No Schematic Found'}, 404
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': "Updates Recieved"}, 201

    def post(self, _sid=None):
        """
        Post a Zone
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
                return {'response': ('Missing Information %s %s'
                                     % (user_id, _hd))}, 400
            else:
                LOG.info(_hd)
                skms = Schematics.query.filter(
                    Schematics.auth_id == user_id).filter(
                    Schematics.id == _sid).first()
            if not skms:
                return {'response': 'No Schematic Found'}, 404
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

                    zon = Zones(schematic_id=_sid,
                                schematic_runlist=_zn.get('schematic_runlist'),
                                schematic_script=_zn.get('schematic_script'),
                                zone_name=_zn.get('zone_name',
                                                  utils.rand_string(length=20)),
                                size_id=_zn.get('size_id'),
                                image_id=_zn.get('image_id'),
                                name_convention=_zn.get('name_convention'),
                                quantity=_zn.get('quantity'),
                                credential_id=ssh.id)
                    _DB.session.add(zon)
                    _DB.session.flush()

                    packet = {'cloud_key': skms.cloud_key,
                              'cloud_username': skms.cloud_username,
                              'cloud_region': skms.cloud_region,
                              'cloud_provider': skms.cloud_provider,
                              'cloud_tenant': skms.cloud_tenant,
                              'quantity': zon.quantity,
                              'name': zon.name_convention,
                              'image': zon.image_id,
                              'size': zon.size_id,
                              'zone_id': zon.id,
                              'credential_id': ssh.id,
                              'ssh_username': ssh.ssh_user,
                              'ssh_key_pri': ssh.ssh_key_pri,
                              'ssh_key_pub': ssh.ssh_key_pub,
                              'key_name': ssh.key_name,
                              'job': 'build'}

                    if skms.cloud_url:
                        packet['cloud_url'] = skms.cloud_url
                    if skms.cloud_version:
                        packet['cloud_version'] = skms.cloud_version
                    if zon.schematic_runlist:
                        packet['schematic_runlist'] = zon.schematic_runlist
                    if zon.schematic_script:
                        packet['schematic_script'] = zon.schematic_script

                    LOG.debug(packet)
                    QUEUE.put(packet)
            _DB.session.commit()
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': ('Application requests have been recieved'
                                 ' for Schematic %s'
                                 % _sid)}, 200
