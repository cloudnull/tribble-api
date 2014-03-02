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
import traceback

import chef.exceptions as chefexp
import chef


LOG = logging.getLogger('tribble-engine')


class ChefSearchError(Exception):
    pass


class ChefClientStartError(Exception):
    pass


class ChefMe(object):
    def __init__(self, specs, name, function):
        run_list = specs.get('config_runlist', '')
        self.run_list = run_list.split(',')

        self.env = specs.get('config_env')
        self.url = specs.get('config_server')
        self.user = specs.get('config_username')
        self.temp_f = str(specs.get('config_key'))

        self.chef_s = None

        LOG.debug(self.temp_f)
        try:
            action = getattr(self, function)
            action(name)
        except Exception, exp:
            LOG.warn('Fatal ERROR Happened with Cheferizing'
                     ' the node %s ==> %s' % (name, exp))
            LOG.error(traceback.format_exc())

    def chefer_setup(self, node_name):
        # Prep the Chef API
        with chef.ChefAPI(url=self.url, key=self.temp_f, client=self.user):
            # Search for the node
            chef_s = chef.Search('node', q='name:*%s*' % node_name)
            name = None
            LOG.debug('Nodes found in chef_server ==> %s' % chef_s)
            if chef_s:
                chef_n = chef_s[0]['name']
                if chef_n:
                    name = str(chef_n)
            else:
                name = node_name

            LOG.info('Running Chef setup on %s' % name)
            # Load the node
            n_s = chef.Node(name)

            # Append the run_list / roles
            if self.run_list is None:
                n_s.run_list = []
            else:
                for _rl in self.run_list:
                    n_s.run_list.append(_rl)

            # Add the environment variables
            n_s.chef_environment = self.env

            # Save the instance in Chef
            n_s.save()

    def chefer_remove_all(self, name):
        self.chefer_remover(node_name=name, node=True)
        self.chefer_remover(node_name=name)

    def chefer_node_remove(self, name):
        self.chefer_remover(node_name=name, node=True)

    def chefer_client_remove(self, name):
        self.chefer_remover(node_name=name)

    def _get_name(self, node_name):
        if self.chef_s and len(self.chef_s) >= 1:
            name = self.chef_s[0].get('name')
            if name is None:
                raise ChefSearchError('"%s" Not Found' % self.chef_s)
        else:
            name = node_name

        return name

    def chefer_remover(self, node_name, node=False):
        try:
            with chef.ChefAPI(url=self.url, key=self.temp_f, client=self.user):
                if node:
                    LOG.info('Removing "%s" from CHEF Nodes' % node_name)
                    self.chef_s = chef.Search(
                        'node', q='name:*%s*' % node_name
                    )
                    name = self._get_name(node_name=node_name)
                    node_data = chef.Node(name)
                else:
                    LOG.info('Removing "%s" from CHEF Clients' % node_name)
                    self.chef_s = chef.Search(
                        'client', q='name:*%s*' % node_name
                    )
                    name = self._get_name(node_name=node_name)
                    node_data = chef.Client(name)

                try:
                    node_data.delete()
                except TypeError:
                    LOG.error('CHEF API returned an error on "%s"' % node_name)
        except chefexp.ChefServerNotFoundError:
            LOG.warn('The Node %s was not found' % node_name)
        except chefexp.ChefServerError:
            LOG.error('Chef server did not respond normally'
                      ' Check Chef and try again. Chef Server : %s '
                      % self.url)
        except chefexp.ChefAPIVersionError:
            LOG.error('There seems to be an issue with your API'
                      ' version Check you Chef Server and try again')
        except chefexp.ChefError:
            LOG.error('Chef is mad, or busy, there was an error'
                      ' and the request was not processed normally')
        except ChefSearchError:
            LOG.warn('The Node %s was not found' % node_name)
        except Exception, exp:
            LOG.warn('CHEF Failure when working on "%s" ==> %s'
                             % (node_name, exp))
            LOG.error(traceback.format_exc())
