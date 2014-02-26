# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import logging


from libcloud.compute.providers import get_driver
from libcloud import security

import tribble
from tribble.common import system_config
from tribble.engine import cloud_application_map as cam


LOG = logging.getLogger('tribble-engine')
CONFIG = system_config.ConfigureationSetup()


def connection_engine(packet):
    """
    Authenticates a user with the Cloud System they are attempting to operate
    with. If authentication is successful, then the system will allow the user
    to deploy through the application to the provider.
    """

    provider = packet.get('cloud_provider')

    if provider is not None:
        cloud_provider = cam.APP_MAP.get(provider.upper())

        if cloud_provider is None:
            raise tribble.CantContinue('no provider found')

        required_args = cloud_provider['required_args']
        if 'NO_CHOICE' in cloud_provider:
            driver = get_driver(cloud_provider['NO_CHOICE'])
        else:
            region = cloud_provider['CHOICES'].get('cloud_region')
            if region is None:
                raise tribble.CantContinue('no driver found for %s' % region)
            driver = get_driver(region)

        specs = {}
        for item, value in required_args.items():
            if 'get' in value:
                specs[item] = packet.get(value['get'], value.get('default'))
            elif 'is' in value:
                specs[item] = value['is']

            if value.get('required') is True and specs[item] is None:
                raise tribble.CantContinue(
                    '%s is a requied value but was set as None' % item
                )

            if 'make' in value:
                if value['make'] == 'upper':
                    specs[item] = specs[item].upper()
                elif value['make'] == 'lower':
                    specs[item] = specs[item].lower()

        LOG.debug(specs)
        default_config = CONFIG.config_args()
        security.CA_CERTS_PATH.append(default_config.get('ca_cert_pem'))
        return driver(
            packet.get('cloud_username'),
            packet.get('cloud_key'),
            **specs
        )
