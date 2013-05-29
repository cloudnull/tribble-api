from tribble.webapp import schematics_rest, zones_rest, redeploy_rest
from tribble.appsetup.start import LOG


def routes(api):
    """
    Load all available routes.
    """
    LOG.info('Routes Loading')
    uri = {'s': (schematics_rest.SchematicsRest, '/v1/schematics'),
           'ss': (schematics_rest.SchematicsRest, '/v1/schematics/'),
           'ssi': (schematics_rest.SchematicsRest, '/v1/schematics/<_sid>'),
           'ssiz': (zones_rest.ZonesRest, '/v1/schematics/<_sid>/zones'),
           'ssizs': (zones_rest.ZonesRest, '/v1/schematics/<_sid>/zones/'),
           'ssizsi': (zones_rest.ZonesRest,
                      '/v1/schematics/<_sid>/zones/<_zid>'),
           'ssir': (redeploy_rest.SchematicsRedeploy,
                    '/v1/schematics/<_sid>/redeploy'),
           'ssizsir': (redeploy_rest.SchematicsRedeploy,
                       '/v1/schematics/<_sid>/zones/<_zid>/redeploy')}

    for endpoint in uri.keys():
        method, uri = uri[endpoint]
        api.add_resource(method, uri)
