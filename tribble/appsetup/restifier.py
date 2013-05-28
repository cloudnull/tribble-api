from tribble.webapp import schematics_rest, zones_rest
from tribble.appsetup.start import LOG


def routes(api):
    LOG.info('Routes Loading')
    api.add_resource(schematics_rest.SchematicsRest, '/v1/schematics')
    api.add_resource(schematics_rest.SchematicsRest, '/v1/schematics/')
    api.add_resource(schematics_rest.SchematicsRest, '/v1/schematics/<_id>')
    api.add_resource(zones_rest.ZonesRest, '/v1/schematics/<_sid>/zones')
    api.add_resource(zones_rest.ZonesRest, '/v1/schematics/<_sid>/zones/')
    api.add_resource(zones_rest.ZonesRest, '/v1/schematics/<_sid>/zones/<_zid>')
