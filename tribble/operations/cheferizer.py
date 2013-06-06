import traceback
import chef.exceptions as chefexp
import chef
from StringIO import StringIO


class ChefSearchError(Exception):
    pass


class ChefMe(object):
    def __init__(self, nucleus, name, function, logger):
        self.run_list = nucleus.get('run_list')
        self.env = nucleus.get('config_env')
        self.url = nucleus.get('config_server')
        self.user = nucleus.get('config_username')
        self.temp_f = StringIO('%s' % nucleus.get('config_key'))
        self.logger = logger
        try:
            # Running CHEF Function
            if function == 'chefer_setup':
                self.chefer_setup(node_name=name)

            if function == 'chefer_node_remove':
                self.chefer_remover(node_name=name, node=True)

            if function == 'chefer_client_remove':
                self.chefer_remover(node_name=name, client=True)

            if function == 'chefer_remove_all':
                self.chefer_remover(node_name=name, node=True)
                self.chefer_remover(node_name=name)
        except Exception, exp:
            self.logger.warn('Fatal ERROR Happened with Cheferizing'
                             'the node %s ==> %s' % (name, exp))
            self.logger.error(traceback.format_exc())

    def chefer_setup(self, node_name):
        # Prep the Chef API
        with chef.ChefAPI(self.url, self.temp_f, self.user):
            # Search for the node
            chef_s = chef.Search('node', q='name:*%s*' % node_name)
            if chef_s:
                chef_n = chef_s[0]['name']
                if chef_n:
                    name = str(chef_n)
            else:
                name = node_name
            self.logger.info('Running Chef setup on %s' % name)
            # Load the node
            n_s = chef.Node(name)

            # Append the Runlist/Roles
            for _rl in self.run_list:
                n_s.run_list.append(_rl)

            # Add the environment variables
            n_s.chef_environment = self.env

            # Save the instance in Chef
            n_s.save()

    def chefer_remover(self, node_name, node=False):
        try:
            with chef.ChefAPI(self.url, self.temp_f, self.user):
                if node:
                    self.logger.info('Removing "%s" from CHEF Nodes'
                                     % node_name)
                    chef_s = chef.Search('node', q='name:*%s*' % node_name)
                else:
                    self.logger.info('Removing "%s" from CHEF Clients'
                                     % node_name)
                    chef_s = chef.Search('client', q='name:*%s*' % node_name)

                if chef_s:
                    if chef_s[0]:
                        if 'name' in chef_s[0]:
                            chef_n = chef_s[0]['name']
                            if chef_n:
                                name = str(chef_n)
                        else:
                            raise ChefSearchError('"%s" Not Found' % chef_s)
                    else:
                        raise ChefSearchError('"%s" Not Found' % chef_s)
                else:
                    name = node_name

                try:
                    if node:
                        _cr = chef.Node(name)
                    else:
                        _cr = chef.Client(name)
                    _cr.delete()
                except TypeError:
                    self.logger.warn('CHEF API returned an error on "%s"'
                                     % node_name)
        except chefexp.ChefServerNotFoundError:
            self.logger.warn('The Node %s was not found' % name)
        except chefexp.ChefError:
            self.logger.error('Chef is mad, or busy, there was an error'
                              ' and the request was not processed normally')
        except chefexp.ChefServerError:
            self.logger.error('Chef server did not respond normally'
                              ' Check Chef and try again. Chef Server : %s '
                              % self.url)
        except chefexp.ChefAPIVersionError:
            self.logger.error('There seems to be an issue with your API'
                              ' version Check you Chef Server and try again')
        except ChefSearchError:
            self.logger.warn('The Node %s was not found' % name)
        except Exception, exp:
            self.logger.warn('CHEF Failure when working on "%s" ==> %s'
                             % (node_name, exp))
            self.logger.error(traceback.format_exc())
