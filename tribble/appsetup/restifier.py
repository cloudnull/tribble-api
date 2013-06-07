from tribble.webapp import schematics_rest, zones_rest, redeploy_rest
from tribble.webapp import narciss_rest
from tribble.appsetup.start import LOG


def routes(api):
    """
    Load all available routes.
    """
    LOG.info('Routes Loading')
    uri = {'ss': (schematics_rest.SchematicsRest, '/v1/schematics'),
           'ssi': (schematics_rest.SchematicsRest, '/v1/schematics/<_sid>'),
           'ssizs': (zones_rest.ZonesRest, '/v1/schematics/<_sid>/zones'),
           'ssizsi': (zones_rest.ZonesRest,
                      '/v1/schematics/<_sid>/zones/<_zid>'),
           'ssir': (redeploy_rest.RedeployRestRdp,
                    '/v1/schematics/<_sid>/redeploy'),
           'ssizsir': (redeploy_rest.RedeployRestRdp,
                       '/v1/schematics/<_sid>/zones/<_zid>/redeploy')}

    for endpoint in uri.values():
        LOG.debug(endpoint)
        met, uri = endpoint
        api.add_resource(met, uri)

    api.add_resource(narciss_rest.BluePrints,
                     '/v1/blue_prints')
    api.add_resource(narciss_rest.BluePrints,
                     '/v1/blue_prints/<_sid>')
    api.add_resource(narciss_rest.ServerMaps,
                     '/v1/blue_prints/<_sid>/server_maps')
    api.add_resource(narciss_rest.ServerMaps,
                     '/v1/blue_prints/<_sid>/server_maps/<_zid>')
    api.add_resource(narciss_rest.Instances,
                     '/v1/blue_prints/<_sid>/server_maps/<_zid>/instances')
    api.add_resource(narciss_rest.Instances,
                     '/v1/blue_prints/<_sid>/instances')
