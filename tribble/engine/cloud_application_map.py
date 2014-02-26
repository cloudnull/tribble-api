# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver


APP_MAP = {
    'RACKSPACE': {
        'NO_CHOICE': Provider.RACKSPACE,
        'required_args': {
            'ex_force_auth_url': {
                'get': 'cloud_url',
                'required': True
            },
            'ex_force_auth_version': {
                'get': 'cloud_version',
                'default': '2.0_password'
            },
            'datacenter': {
                'get': 'cloud_region',
                'make': 'lower',
                'required': True
            }
        }
    },
    'VMWARE': {
        'NO_CHOICE': Provider.VCLOUD,
        'required_args': {
            'host': {
                'get': 'cloud_url'
            },
            'api_version': {
                'get': 'cloud_version',
                'default': '1.5'
            }
        }
    },
    'OPENSTACK': {
        'NO_CHOICE': Provider.OPENSTACK,
        'required_args': {
            'ex_force_auth_url': {
                'get': 'cloud_url',
            },
            'ex_force_auth_version': {
                'get': 'cloud_version',
                'default': '2.0_password'
            },
            'ex_tenant_name': {
                'get': 'cloud_tenant',
            }
        }
    },
    'AMAZON': {
        'CHOICES': {
            'AP_NORTHEAST': Provider.EC2_AP_NORTHEAST,
            'AP_SOUTHEAST': Provider.EC2_AP_SOUTHEAST,
            'AP_SOUTHEAST2': Provider.EC2_AP_SOUTHEAST2,
            'EU_WEST': Provider.EC2_EU_WEST,
            'US_EAST': Provider.EC2_US_EAST,
            'US_WEST': Provider.EC2_US_WEST,
            'US_WEST_OREGON': Provider.EC2_US_WEST_OREGON,
            'SA_EAST': Provider.EC2_SA_EAST
        }
    }
}
