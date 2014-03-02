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


CLOUD_APP_MAP = {
    'RACKSPACE': {
        'deployment_methods': [
            'ssh_deploy'
        ],
        'user_init': {
            'networks': {
                'get': 'cloud_networks',
                'make': 'comma_split'
            },
            'ex_files': {
                'get': 'inject_files',
                'make': 'comma_split'
            },
            'ex_userdata': {
                'action': 'get_user_data'
            }
        },
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
        },
        'CHOICES': {
            Provider.RACKSPACE
        }
    },
    'VMWARE': {
        'deployment_methods': [
            'ssh_deploy'
        ],
        'required_args': {
            'host': {
                'get': 'cloud_url'
            },
            'api_version': {
                'get': 'cloud_version',
                'default': '1.5'
            }
        },
        'CHOICES': {
            Provider.VCLOUD
        }
    },
    'OPENSTACK': {
        'deployment_methods': [
            'cloud_init',
            'ssh_deploy'
        ],
        'user_init': {
            'ex_keyname': {
                'get': 'key_name'
            },
            'ssh_key': {
                'get': 'ssh_key_pri'
            },
            'ex_userdata': {
                'action': 'get_user_data'
            },
            'ssh_username': {
                'get': 'ssh_username'
            },
            'ex_securitygroup': {
                'get': 'security_groups',
                'action': 'get_security_groups',
                'default': []
            },
            'networks': {
                'get': 'cloud_networks',
                'make': 'comma_split'
            },
            'ex_files': {
                'get': 'inject_files',
                'make': 'comma_split'
            }
        },
        'required_args': {
            'ex_force_auth_url': {
                'get': 'cloud_url'
            },
            'ex_force_auth_version': {
                'get': 'cloud_version',
                'default': '2.0_password'
            },
            'ex_tenant_name': {
                'get': 'cloud_tenant'
            }
        },
        'CHOICES': {
            Provider.OPENSTACK
        }
    },
    'AMAZON': {
        'deployment_methods': [
            'cloud_init',
            'ssh_deploy'
        ],
        'user_init': {
            'ex_security_groups': {
                'get': 'security_groups',
                'action': 'get_security_group_names'
            },
            'ex_keyname': {
                'get': 'key_name'
            },
            'ssh_key': {
                'get': 'ssh_key_pri'
            },
            'ex_userdata': {
                'action': 'get_user_data'
            },
            'ssh_username': {
                'get': 'ssh_username'
            }
        },
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


JOBS_MAP = {
    'build': {
        'enter_state': 'build',
        'exit_state': 'active',
        'jobs': [
            'api_setup'
        ]
    },
    'redeploy_build': {
        'enter_state': 'build',
        'exit_state': 'active',
        'jobs': [
            'api_setup'
        ]
    },
    'schematic_delete': {
        'enter_state': 'delete',
        'exit_state': 'delete_schematic_resource',
        'jobs': [
            'vm_destroyer'
        ]
    },
    'redeploy_delete': {
        'enter_state': 'delete',
        'exit_state': 'delete_resource',
        'jobs': [
            'vm_destroyer'
        ]
    },
    'zone_delete': {
        'enter_state': 'delete',
        'exit_state': 'delete_resource',
        'job': [
            'vm_destroyer'
        ]
    },
    'instance_delete': {
        'enter_state': 'delete',
        'exit_state': 'delete_resource',
        'jobs': [
            'vm_destroyer'
        ]
    },
    'reconfig': {
        'enter_state': 'delete',
        'exit_state': 'delete_resource',
    }
}