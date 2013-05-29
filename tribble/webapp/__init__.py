def pop_ts(temp):
    """
    From a dictionary that has been result provided by SQLA remove the time
    stamps from the provided data set. This is to assist when processing raw
    data through Queues, "datetime.datetime is not pickleble.
    """
    poper = ['_sa_instance_state', 'heal_at', 'created_at', 'updated_at']
    for _ts in poper:
        if _ts in temp:
            temp.pop(_ts)
    return temp


def parse_dict_list(objlist):
    return [pop_ts(obj.__dict__) for obj in objlist if obj and obj.__dict__]


def not_found(message=None, error=None):
    from flask import jsonify
    if message:
        msg = {"error_text": message}
    else:
        msg = {"error_text": "Resource not found"}

    if error:
        return jsonify(msg), error
    else:
        return jsonify(msg), 404


def auth_mech(rdata, hdata=None):
    from tribble.db.models import CloudAuth
    from tribble.appsetup.start import LOG
    from json import loads
    import traceback
    LOG.debug(rdata)
    obj = CloudAuth.query.filter(
        CloudAuth.dcuser == rdata['x-user']).first()
    if not obj:
        return False
    try:
        user_id = obj.id
        if hdata:
            LOG.debug(hdata)
            try:
                djson = loads(hdata)
            except Exception, exp:
                LOG.error(traceback.format_exc())
                return False
            return user_id, djson
        else:
            return user_id
    except Exception:
        LOG.error(traceback.format_exc())
