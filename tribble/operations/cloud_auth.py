from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud import security
from tribble.appsetup.start import LOG


class CantContinue(Exception):
    pass


def apiauth(packet):
    """
    Authenticates a user with the Cloud System they are attempting to operate
    with. If authentication is successful, then the system will allow the user
    to deploy through the application to the provider.
    """
    security.CA_CERTS_PATH.append('dist/cacert.pem')

    endpoints = {'ORD': Provider.RACKSPACE_NOVA_ORD,
                 'DFW': Provider.RACKSPACE_NOVA_DFW,
                 'LON': Provider.RACKSPACE_NOVA_LON,
                 'AP_NORTHEAST': Provider.EC2_AP_NORTHEAST,
                 'AP_SOUTHEAST': Provider.EC2_AP_SOUTHEAST,
                 'EU_WEST': Provider.EC2_EU_WEST,
                 'US_EAST': Provider.EC2_US_EAST,
                 'US_WEST': Provider.EC2_US_WEST}

    provider = packet.get('provider')
    try:
        if provider.upper() == 'OPENSTACK':
            driver = get_driver(Provider.OPENSTACK)
            specs = {'ex_force_auth_url': packet.get('cloud_url'),
                     'ex_force_auth_version': packet.get('cloud_version',
                                                         '2.0_password')}
        elif provider.upper() == 'VMWARE':
            driver = get_driver(Provider.VCLOUD)
            specs = {'host': packet.get('cloud_url'),
                     'api_version': packet.get('cloud_version', '1.5')}
        elif packet.get('cloud_region') in Provider.__dict__:
            _region = packet.get('cloud_region').upper()
            driver = get_driver(endpoints[_region])
            specs = {'ex_force_auth_url': packet.get('cloud_url'),
                     'ex_force_auth_version': packet.get('cloud_version')}
        else:
            raise CantContinue('We are not able to continue at this point')
    except Exception, exp:
        LOG.info(exp)
        raise CantContinue('System has haulted on specified Request')
    else:
        LOG.debug(specs)
        conn = driver(packet.get('cloud_username'),
                      packet.get('cloud_key'),
                      **specs)
        return conn
