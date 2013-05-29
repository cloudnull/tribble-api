import traceback
from flask import request
from sqlalchemy import and_
from flask.ext.restful import Resource
from tribble.db.models import CloudAuth, Schematics
from tribble.db.models import Instances, InstancesKeys, Zones
from tribble.appsetup.start import _DB, LOG, QUEUE
from tribble.operations import utils
from tribble.webapp import pop_ts, parse_dict_list, auth_mech


class SchematicsRedeploy(Resource):
    def post(self, _sid=None):
        """
        Post for redeployment of a Cluster
        """
        return {'response': "Data Recieved"}, 200


class ZonesRedeploy(Resource):
    def post(self, _sid=None, _zid=None):
        """
        Post for redeployment of a Zone
        """
        return {'response': "Data Recieved"}, 200
