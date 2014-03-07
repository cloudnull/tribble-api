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

import chef
import chef.exceptions as chefexp


LOG = logging.getLogger('tribble-engine')


class ChefSearchError(Exception):
    """Exception when performing a chef search."""
    pass


class ChefClientStartError(Exception):
    """Exception when performing a chef client start."""
    pass


class ChefMe(object):
    """Interact with a chef-server.

    :param specs: ``dict``
    :param name: ``str``
    :param function: ``func``
    """
    def __init__(self, specs, name, function):
        run_list = specs.get('config_runlist', '')
        self.run_list = run_list.split(',')
        self.env = specs.get('config_env')
        self.url = specs.get('config_server')
        self.user = specs.get('config_username')
        self.temp_f = str(specs.get('config_key'))
        self.chef_search = None

        LOG.debug(self.temp_f)
        try:
            action = getattr(self, function)
            action(name)
        except Exception as exp:
            LOG.warn('Fatal ERROR Happened with Cheferizing'
                     ' the node %s ==> %s' % (name, exp))
            LOG.error(traceback.format_exc())

    def chefer_setup(self, node_name):
        """Interact with the Chef API.

        :param node_name: ``str``
        """
        LOG.info('Running Chef setup on %s' % node_name)
        with chef.ChefAPI(url=self.url, key=self.temp_f, client=self.user):
            # Search for the node
            self._chef_search(search='node', name=node_name)

            # node name
            name = self._get_name(node_name=node_name)

            # Load the node
            node = chef.Node(name)

            # Set node run list
            node.run_list = self.run_list

            # Add the environment variables
            node.chef_environment = self.env

            # Save the instance in Chef
            node.save()

    def chefer_remove_all(self, name):
        """Remove both a client and node from within chef-server.

        :param name: ``str``
        """
        for search_type in ['node', 'client']:
            self.chefer_remover(node_name=name, search=search_type)

    def chefer_node_remove(self, name):
        """Remove a node from chef-server.

        :param name: ``str``
        """
        self.chefer_remover(node_name=name, search='node')

    def chefer_client_remove(self, name):
        """Remove a client from chef-server.

        :param name: ``str``
        """
        self.chefer_remover(node_name=name, search='client')

    def _chef_search(self, search, name):
        self.chef_search = chef.Search(search, q='name:*%s*' % name)
        LOG.debug('search: %s - list: %s' % (search, self.chef_search))

    def _get_name(self, node_name):
        """Get the name of an instance from chef-server.

        :param node_name: ``str``
        :return: ``str``
        """
        if self.chef_search:
            name = self.chef_search[0].get('name')
            if name is None:
                raise ChefSearchError('"%s" Not Found' % self.chef_search)
            return name
        else:
            return node_name

    def chefer_remover(self, node_name, search):
        """Remove a node from chef-server.

        :param node_name:
        :param search:
        """
        try:
            with chef.ChefAPI(url=self.url, key=self.temp_f, client=self.user):
                LOG.info('Removing "%s" from CHEF Nodes' % node_name)
                self._chef_search(search=search, name=node_name)
                name = self._get_name(node_name=node_name)
                node_data = chef.Node(name)

                try:
                    node_data.delete()
                except TypeError:
                    LOG.error('CHEF API returned an error on "%s"' % node_name)

        except chefexp.ChefServerNotFoundError:
            LOG.warn('The Node %s was not found' % node_name)
        except chefexp.ChefServerError:
            LOG.error(
                'Chef server did not respond normally Check Chef and try'
                ' again. Chef Server : %s ' % self.url
            )
        except chefexp.ChefAPIVersionError:
            LOG.error(
                'There seems to be an issue with your API version Check you'
                ' Chef Server and try again'
            )
        except chefexp.ChefError:
            LOG.error(
                'Chef is mad, or busy, there was an error and the request was'
                ' not processed normally'
            )
        except ChefSearchError:
            LOG.warn('The Node %s was not found' % node_name)
        except Exception as exp:
            LOG.error(
                'CHEF Failure when working on "%s" => %s' % (node_name, exp)
            )
            LOG.error(traceback.format_exc())
