from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud import security
from tribble.appsetup.start import LOG, STATS


class CantContinue(Exception):
    pass


def apiauth(packet):
    """
    Authenticates a user with the Cloud System they are attempting to operate
    with. If authentication is successful, then the system will allow the user
    to deploy through the application to the provider.
    """
    security.CA_CERTS_PATH.append('dist/cacert.pem')

    endpoints = {'AP_NORTHEAST': Provider.EC2_AP_NORTHEAST,
                 'AP_SOUTHEAST': Provider.EC2_AP_SOUTHEAST,
                 'EU_WEST': Provider.EC2_EU_WEST,
                 'US_EAST': Provider.EC2_US_EAST,
                 'US_WEST': Provider.EC2_US_WEST}

    provider = packet.get('cloud_provider', Provider.DUMMY)
    try:
        if provider.upper() == 'OPENSTACK':
            STATS.incr('Provider_Openstack')
            driver = get_driver(Provider.OPENSTACK)
            specs = {'ex_force_auth_url': packet.get('cloud_url'),
                     'ex_force_auth_version': packet.get('cloud_version',
                                                         '2.0_password'),
                     'ex_tenant_name': packet.get('cloud_username')}
        elif provider.upper() == 'RACKSPACE':
            STATS.incr('Provider_Rackspace')
            driver = get_driver(Provider.RACKSPACE)
            specs = {'ex_force_auth_url': packet.get('cloud_url'),
                     'ex_force_auth_version': packet.get('cloud_version'),
                     'datacenter': packet.get('cloud_region').lower()}
        elif provider.upper() == 'VMWARE':
            STATS.incr('Provider_VMWARE')
            driver = get_driver(Provider.VCLOUD)
            specs = {'host': packet.get('cloud_url'),
                     'api_version': packet.get('cloud_version', '1.5')}
        elif provider.upper() == 'AMAZON':
            STATS.incr('Provider_Amazon')
            if packet.get('cloud_region').upper() in endpoints:
                region = packet.get('cloud_region')
                driver = get_driver(endpoints[region.upper()])
                specs = {'ex_force_auth_url': packet.get('cloud_url'),
                         'ex_force_auth_version': packet.get('cloud_version')}
            else:
                raise CantContinue('No Region Found.')
        elif packet.get('cloud_provider') in Provider.__dict__:
            region = packet.get('cloud_region').upper()
            _provider = Provider.__dict__[packet.get('cloud_provider')]
            driver = get_driver(_provider)
            specs = {'ex_force_auth_url': packet.get('cloud_url'),
                     'ex_force_auth_version': packet.get('cloud_version')}
        else:
            driver = get_driver(provider)
            specs = {'ex_force_auth_url': packet.get('cloud_url'),
                     'ex_force_auth_version': packet.get('cloud_version')}
    except Exception, exp:
        LOG.info(exp)
        raise CantContinue('System has haulted on specified Request')
    else:
        LOG.debug(specs)
        conn = driver(packet.get('cloud_username'),
                      packet.get('cloud_key'),
                      **specs)
        return conn
