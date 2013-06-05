def input_cloudinit(nucleus):
    run_list = nucleus.get('schematic_runlist').split(',')
    return {'chef':
        {'run_list': [str(key) for key in run_list],
         'install_type': 'omnibus',
         'server_url': '%(config_server)s',
         'node_name': '%(node_name)s',
         'environment': '%(config_env)s',
         'omnibus_url': 'https://www.opscode.com/chef/install.sh',
         'force_install': True,
         'validation_name': '%(config_clientname)s',
         'validation_key': '%(config_validation_key)s',
         'output': {'all': '| tee -a /var/log/cloud-init-output.log'}
            }
        }
