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
from tribble.common.db import zone_status
from tribble.engine import utils
from tribble.common import system_config
from tribble.engine import config_manager
from tribble.engine import engine_maps as cam


LOG = logging.getLogger('tribble-engine')
CONFIG = system_config.ConfigureationSetup()


class UserData(utils.EngineParser):
    def __init__(self, packet, user_init, conn):
        utils.EngineParser.__init__(self, packet)

        self.user_init = user_init
        self.conn = conn
        self.zone_status = zone_status.ZoneState(cell=self.packet)

    def _get_user_data(self):
        return config_manager.ConfigManager(packet=self.packet)

    def _get_security_groups(self):
        sec_groups = self.specs.get('security_groups')
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
        for item, value in self.user_init.items():
            action = getattr(self, '_%s' % value)
            if action is not None:
                action(item, value)

        return self.specs


class ConnectionEngine(utils.EngineParser):
    def __init__(self, packet):
        """Authenticates a user with a Cloud System.

        If authentication is successful, then the system will allow the user
        to deploy through the application to the provider.
        """
        utils.EngineParser.__init__(self, packet)

        self.provider = packet.get('cloud_provider')
        if self.provider is not None:
            self.cloud_provider = cam.CLOUD_APP_MAP.get(self.provider.upper())
            if self.cloud_provider is None:
                raise tribble.CantContinue('no provider found')
        else:
            raise tribble.CantContinue('no provider provided')

        self.required_args = self.cloud_provider['required_args']

    def _choices(self):
        region = self.cloud_provider.get('cloud_region')
        if region is None:
            msg = 'No Region Found for driver %s' % region
            raise tribble.CantContinue(msg)

        return get_driver(region)

    def run(self):
        driver = self._choices()

        for item, value in self.required_args.items():
            action = getattr(self, '_%s' % value)
            if action is not None:
                action(item, value)

        LOG.debug(self.specs)
        default_config = CONFIG.config_args()
        security.CA_CERTS_PATH.append(default_config.get('ca_cert_pem'))

        driver = driver(
            self.packet.get('cloud_username'),
            self.packet.get('cloud_key'),
            **self.specs
        )

        user_data = UserData(
            packet=self.specs, user_init=self.cloud_provider, conn=driver
        )

        deployment = self.cloud_provider['deployment_methods']

        return driver, user_data.run(), deployment
