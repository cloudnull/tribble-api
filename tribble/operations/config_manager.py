import traceback
from tribble.appsetup.start import LOG


def check_configmanager(nucleus, ssh=False):
    try:
        LOG.info('Looking for config management')
        config_type = nucleus.get('config_type', 'NONE').upper()
        if config_type == 'CHEF_SERVER':
            LOG.info('Chef Server has been set for config management')
            if all([nucleus.get('config_key'),
                    nucleus.get('config_server'),
                    nucleus.get('config_validation_key'),
                    nucleus.get('config_clientname'),
                    nucleus.get('schematic_runlist')]):
                LOG.info('Chef Server is confirmed as the config management')
                return init_chefserver(nucleus=nucleus, ssh=ssh)
            else:
                return nucleus.get('cloud_init')
        else:
            return nucleus.get('cloud_init')
    except Exception:
        LOG.error(traceback.format_exc())


def init_chefserver(nucleus, ssh=False):
    from tribble.purveyors import chef_server
    chef = chef_server.Strapper(nucleus=nucleus, logger=LOG)
    chef_init = chef.chef_cloudinit()
    script = nucleus.get('schematic_script')
    if (script and not ssh):
        _op = {'op_script': str(script),
               'op_script_loc': '/tmp/schematic_script.sh'}
        sop = ('try:\n'
               '    OP_SCRIPT = \"\"\"%(op_script)s\"\"\"\n'
               '    open(\'%(op_script_loc)s\', \'w\').write(OP_SCRIPT)\n'
               '    subprocess.call([\'/bin/bash\', \'%(op_script_loc)s\'])\n'
               'except Exception:\n'
               '    print("Error When Running User Script")\n')
        chef_init = chef_init + sop % _op
    return chef_init


def chef_update_instances(nucleus):
    from tribble.operations import cheferizer
    node_list = nucleus.get('db_instances')
    if node_list:
        for dim in node_list:
            cheferizer.ChefMe(nucleus=nucleus,
                              name=dim.server_name.lower(),
                              function='chefer_setup',
                              logger=LOG)
