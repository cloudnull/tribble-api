# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
"""Creating the application map and the jobs map.

The application map and the jobs map are simple dicts.

To add "providers" to the application map simply start with a key app in all
capital letters. required sub keys are "deployment_methods", "user_init",
"required_args" and "CHOICES". Here are the available options for all of the
arguments.

deployment_methods = list
- This list contains nothing but strings.
user_init = dict
- This dictionary contains all of the arguments required to make the driver go.
- available methods, by default, are:
  "get"
  "is"
  "action"
  "required"
  "comma_split"
  "make"
required_args = dict
- available methods, by default, are:
  "get"
  "is"
  "action"
  "required"
  "comma_split"
  "make"
CHOICES = dict
- Choices has a special verb, if the cloud types.Provider only has one
  "types.Provider" then the verb to use would be "only". If the cloud
  "types.Provider" has more than one "types.Provider" each "types.Provider"
  is KEY:value with the KEY in all capital letters.


The jobs map contains all of the available application methods. The top level
key is the job name. Once a job has been set, the job has three available
methods.  "enter_state", "exit_state", "jobs".
enter_state = str
exit_state = str
jobs = list
"""


from libcloud.compute import types


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
            'ssh_key': {
                'get': 'ssh_key_pri'
            }
        },
        'required_args': {
            'ex_force_auth_url': {
                'get': 'cloud_url',
            },
            'ex_force_auth_version': {
                'get': 'cloud_version',
                'default': '2.0'
            },
            'region': {
                'get': 'cloud_region',
                'make': 'lower',
                'required': True
            }
        },
        'CHOICES': {
            'only': types.Provider.RACKSPACE
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
            'only': types.Provider.VCLOUD
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
            'only': types.Provider.OPENSTACK
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
            'ssh_username': {
                'get': 'ssh_username'
            }
        },
        'CHOICES': {
            'AP_NORTHEAST': types.Provider.EC2_AP_NORTHEAST,
            'AP_SOUTHEAST': types.Provider.EC2_AP_SOUTHEAST,
            'AP_SOUTHEAST2': types.Provider.EC2_AP_SOUTHEAST2,
            'EU_WEST': types.Provider.EC2_EU_WEST,
            'US_EAST': types.Provider.EC2_US_EAST,
            'US_WEST': types.Provider.EC2_US_WEST,
            'US_WEST_OREGON': types.Provider.EC2_US_WEST_OREGON,
            'SA_EAST': types.Provider.EC2_SA_EAST
        }
    }
}


JOBS_MAP = {
    'build': {
        'enter_state': 'build',
        'exit_state': 'active',
        'jobs': [
            'vm_constructor'
        ]
    },
    'redeploy_build': {
        'enter_state': 'build',
        'exit_state': 'active',
        'jobs': [
            'vm_constructor'
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
