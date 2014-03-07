# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
"""Building a plugin

When building a plugin simply create a python module and place it in the
plugins directory.

in __init__.py add a constant dict named CONFIG_APP_MAP

Example:

CONFIG_APP_MAP = {
    'SCRIPT': {
        'reconfig': ``str`` or ``func`` or None,
        'build': ``str`` or ``func`` or None,
        'redeploy_build': ``str`` or ``func`` or None,
        'instance_delete': ``str`` or ``func`` or None,
        'required_args': {
            'node_name': {
                'get': 'node_name',
                'required': True
            },
            'config_key': {
                'get': 'config_key'
            },
            'config_env': {
                'get': 'config_env'
            },
            'config_server': {
                'get': 'config_server'
            },
            'config_validation_key': {
                'get': 'config_validation_key'
            },
            'config_clientname': {
                'get': 'config_clientname'
            },
            'config_runlist': {
                'get': 'config_runlist'
            }
        }
    }
}

- available methods for the "required_args" key are:
  "get"
  "is"
  "action"
  "required"
  "comma_split"
  "make"
"""
