from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud import security


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

    if provider.upper() == 'OPENSTACK':
        driver = get_driver(Provider.OPENSTACK)
        conn = driver(packet.get('cloud_username'),
                      packet.get('cloud_key'),
                      ex_force_auth_url=packet.get('cloud_url'),
                      ex_force_auth_version='2.0_password')
    elif packet.get('cloud_region'):
        _region = packet.get('cloud_region').upper()
        if _region in endpoints:
            driver = get_driver(endpoints[_region])
            conn = driver(packet.get('cloud_username'),
                          packet.get('cloud_key'))
        else:
            raise CantContinue('You provided an unsupported region')
    else:
        raise CantContinue('We are not able to continue at this point')
    return conn
