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

from libcloud.compute import providers
from libcloud import security

import tribble
from tribble.common.db import zone_status
from tribble.common import system_config
from tribble.engine import engine_maps as cam
from tribble.engine import utils


LOG = logging.getLogger('tribble-engine')
CONFIG = system_config.ConfigurationSetup()


class UserData(utils.EngineParser):
    """Return user data as a dict for building cloud instances.

    @inherits :class: ``utils.EngineParser.__init__``
    :param packet: ``dict``
    :param user_init:  ``dict``
    :param conn: ``object``
    :return: ``dict``
    """
    def __init__(self, packet, user_init, conn):
        utils.EngineParser.__init__(self, packet)

        self.user_init = user_init
        self.conn = conn
        self.zone_status = zone_status.ZoneState(cell=self.packet)

    def _get_security_groups(self, *args):
        """Return a comma separated list of security groups.

        :param args:
        :return: ``dict``
        """
        sec_groups = self.packet.get('security_groups')
        try:
            sgns = ''.join(sec_groups.split()).split(',')
            all_sg = self.conn.ex_list_security_groups()
            sgns = [sg for sg in all_sg if sg.name in sgns]
        except Exception as exp:
            LOG.error(exp)
            self.zone_status.error(error_msg=exp)
        else:
            return sgns

    def run(self):
        """Run the methods.

        :return: ``dict``
        """
        return self._run(init_items=self.user_init)


class ConnectionEngine(utils.EngineParser):
    """Authenticates a user with a Cloud System.

    If authentication is successful, then the system will allow the user
    to deploy through the application to the provider.

    @inherits :class: ``utils.EngineParser.__init__``
    :param packet: ``dict``
    """
    def __init__(self, packet):
        utils.EngineParser.__init__(self, packet)

        self.provider = packet.get('cloud_provider')
        if self.provider is not None:
            self.cloud_provider = cam.CLOUD_APP_MAP.get(self.provider.upper())
            if self.cloud_provider is None:
                raise tribble.CantContinue('no provider found')
        else:
            raise tribble.CantContinue('no provider provided')

        self.required_args = self.cloud_provider['required_args']
        self.user_init_args = self.cloud_provider['user_init']

    def _choices(self):
        """Return a driver from the loaded application maps.

        :return: ``object``
        """
        provider_regions = self.cloud_provider.get('CHOICES')
        if 'only' in provider_regions:
            provider_region = provider_regions['only']
        else:
            provider_region = provider_regions.get('cloud_region')

        if provider_region is None:
            msg = 'No Provider Found for driver "%s"' % self.cloud_provider
            raise tribble.CantContinue(msg)

        return providers.get_driver(provider_region)

    def run(self):
        """Run the methods.

        :return: ``tuple``
        """
        driver = self._choices()
        self._run(init_items=self.required_args)

        LOG.debug(self.specs)
        default_config = CONFIG.config_args()
        security.CA_CERTS_PATH.append(default_config.get('ca_cert_pem'))

        driver = driver(
            self.packet.get('cloud_username'),
            self.packet.get('cloud_key'),
            **self.specs
        )

        _user_data = UserData(
            packet=self.packet, user_init=self.user_init_args, conn=driver
        )
        user_data = _user_data.run()

        deployment = self.cloud_provider['deployment_methods']

        return driver, user_data, deployment
