import traceback
from flask import request
from flask.ext.restful import Resource
from tribble.appsetup.start import LOG, QUEUE, _DB
from tribble.purveyors import db_proc
from tribble.webapp import pop_ts, auth_mech, build_cell


class ResetStateRestRdp(Resource):
    def post(self, _sid=None, _zid=None):
        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'Missing Information'}, 400
        try:
            if not _sid:
                return {'response': 'No Schematic specified'}, 400
            else:
                skm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
                if not skm:
                    return {'response': 'No Schematic Found'}, 404

            if not _zid:
                return {'response': 'No Zone ID provided'}, 404
            else:
                zon = db_proc.get_zones_by_id(skm=skm, zid=_zid)
                if not zon:
                    return {'response': 'No Zone Found'}, 404

            cell = {'zone_state': 'ACTIVE RESET'}
            try:
                sess = _DB.session
                db_proc.put_zone(session=sess,
                                 zon=zon,
                                 put=cell)
            except Exception:
                LOG.error(traceback.format_exc())
            else:
                db_proc.commit_session(session=sess)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': ('Zone State for %s'
                                 ' has been Reset' % _zid)}, 200


class RedeployRestRdp(Resource):
    def post(self, _sid=None, _zid=None):
        user_id = auth_mech(rdata=request.headers)
        if not user_id:
            return {'response': 'Missing Information'}, 400
        try:
            if not _sid:
                return {'response': 'No Schematic specified'}, 400
            else:
                skm = db_proc.get_schematic_id(sid=_sid, uid=user_id)
            if not skm:
                return {'response': 'No Schematic Found'}, 404

            if _zid:
                zons = [db_proc.get_zones_by_id(skm=skm, zid=_zid)]
            else:
                zons = db_proc.get_zones(skm=skm)
            if not zons:
                return {'response': 'No Zone Found'}, 404

            con = db_proc.get_configmanager(skm=skm)

            jobs = []
            retskms = []
            for zon in zons:
                key = db_proc.get_instanceskeys(zon=zon)
                ints = db_proc.get_instances(zon=zon)
                base_qty = int(zon.quantity)
                numr_qty = len(ints)

                if base_qty > numr_qty:
                    difference = (base_qty - numr_qty)
                    packet = build_cell(job='redeploy_build',
                                        schematic=skm,
                                        zone=zon,
                                        sshkey=key,
                                        config=con)
                    packet['quantity'] = difference
                    LOG.debug(packet)
                    jobs.append(packet)
                    msg = ('Building %s Instances for Zone %s'
                           % (difference, zon.id))
                    retskms.append(msg)
                elif base_qty < numr_qty:
                    difference = (numr_qty - base_qty)
                    packet = build_cell(job='redeploy_delete',
                                        schematic=skm,
                                        zone=zon,
                                        sshkey=key,
                                        config=con)
                    aints = [ins.instance_id for ins in ints]
                    remos = aints[:difference]
                    packet['uuids'] = remos
                    rems = [ins for ins in ints if ins.instance_id in remos]
                    sess = _DB.session
                    for ins in rems:
                        sess = db_proc.delete_item(session=sess, item=ins)
                    db_proc.commit_session(session=sess)

                    LOG.debug(packet)
                    jobs.append(packet)
                    msg = ('Removing %s Instances for Zone %s'
                           % (difference, zon.id))
                    retskms.append(msg)

                    for ins in remos:
                        aints.pop(aints.index(ins))
                    ints = [ins for ins in ints if ins.instance_id in aints]

                if con.config_type:
                    if ints:
                        packet = build_cell(job='reconfig',
                                            schematic=skm,
                                            zone=zon,
                                            sshkey=key,
                                            config=con)
                        num_inst = len(ints)
                        packet['quantity'] = num_inst
                        packet['db_instances'] = ints
                        LOG.debug(packet)
                        jobs.append(packet)
                        msg = ('Reconfiguring %s Instances for Zone %s'
                               % (num_inst, zon.id))
                        retskms.append(msg)
            if jobs:
                QUEUE.put(jobs)
        except Exception:
            LOG.error(traceback.format_exc())
            return {'response': 'Unexpected Error'}, 500
        else:
            return {'response': retskms}, 200
