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
                skms = Schematics.query.filter(
                    Schematics.auth_id == user_id,
                    Schematics.id == _sid).first()
            else:
                return {'response': 'No Schematic Specified'}, 400

            if not skms:
                return {'response': 'No Schematic found'}, 404
            else:
                retskms = []
                if _zid:
                    zon = Zones.query.filter(
                        Zones.schematic_id == skms.id,
                        Zones.id == _zid).all()
                else:
                    zon = Zones.query.filter(
                        Zones.schematic_id == skms.id).all()
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
                        retskms.append(dzone)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': retskms}, 200

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
            _skm = Schematics.query.filter(
                Schematics.auth_id == user_id).filter(
                Schematics.id == _sid).first()
            if not _skm:
                return {'response': 'No Schematic Found'}, 404
            zon = Zones.query.filter(
                Zones.schematic_id == _skm.id).first()
            if not zon:
                return {'response': 'No Zone Found'}, 404
            else:
                insts = Instances.query.filter(
                    Instances.zone_id == zon.id).all()
                if insts:
                    for ins in insts:
                        _DB.session.delete(ins)
                        _DB.session.flush()
                    cell = {'id': _skm.id,
                            'cloud_key': _skm.cloud_key,
                            'cloud_username': _skm.cloud_username,
                            'cloud_region': _skm.cloud_region,
                            'provider': _skm.cloud_provider,
                            'uuids': [ins.instance_id for ins in insts],
                            'job': 'delete'}
                    QUEUE.put(cell)
                _DB.session.delete(zon)
                _DB.session.flush()
                key = InstancesKeys.query.filter(
                    InstancesKeys.id == zon.credential_id).first()
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
            return {'response': 'Missing Information'}, 400

        auth = auth_mech(hdata=request.data,
                         rdata=request.headers)
        if not auth:
            return {'response': 'Missing Information'}, 400
        else:
            user_id, _hd = auth
        try:
            if not all([user_id, _hd]):
                return {'response': 'Missing Information'}, 400
            else:
                skms = Schematics.query.filter(
                    Schematics.auth_id == user_id).filter(
                    Schematics.id == _sid).first()
            if skms:
                if _zid:
                    zon = Zones.query.filter(
                        Zones.schematic_id == skms.id,
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

    def post(self, _sid=None, _zid=None):
        """
        Post a Zone
        """
        return {'response': "Deletes Recieved"}, 200