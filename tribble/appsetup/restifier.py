from tribble.webapp import schematics_rest, zones_rest
from tribble.webapp import redeploy_rest, instances_rest
from tribble.appsetup.start import LOG


def routes(api):
    """
    Load all available routes.
    """
    LOG.info('Routes Loading')
    uri = [(schematics_rest.SchematicsRest,
            '/v1/schematics'),
           (schematics_rest.SchematicsRest,
            '/v1/schematics/<_sid>'),
           (zones_rest.ZonesRest,
            '/v1/schematics/<_sid>/zones'),
           (zones_rest.ZonesRest,
            '/v1/schematics/<_sid>/zones/<_zid>'),
           (instances_rest.InstancesRest,
            '/v1/schematics/<_sid>/zones/<_zid>/instances/<_iid>'),
           (redeploy_rest.RedeployRestRdp,
            '/v1/schematics/<_sid>/redeploy'),
           (redeploy_rest.RedeployRestRdp,
            '/v1/schematics/<_sid>/zones/<_zid>/redeploy'),
           (redeploy_rest.ResetStateRestRdp,
            '/v1/schematics/<_sid>/zones/<_zid>/resetstate')]

    for endpoint in uri:
        LOG.debug(endpoint)
        met, uri = endpoint
        api.add_resource(met, uri)
