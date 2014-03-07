# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import ConfigParser
import logging
import os
import stat
import sys

from tribble import info


LOG = logging.getLogger('tribble-common')


def is_int(value):
    """Return int if the value can be an int.

    :param value: ``str``
    :return: ``int`` :return: ``str``
    """
    try:
        return int(value)
    except ValueError:
        return value


class ConfigurationSetup(object):
    """Parse arguments from a Configuration file.

    Note that anything can be set as a "Section" in the argument file.
    """
    def __init__(self):
        self.args = {}
        self.config_file = os.path.join(
            '/etc/', info.__appname__, 'tribble.conf'
        )
        self.check_perms()

    def check_perms(self):
        """Check the permissions of the config file.

        Permissions must be 0600 or 0400.
        """
        # If config file is specified, confim proper permissions
        if os.path.isfile(self.config_file):
            confpath = self.config_file
            if os.path.isfile(os.path.realpath(confpath)):
                mode = oct(stat.S_IMODE(os.stat(confpath).st_mode))
                if not any([mode == '0600', mode == '0400']):
                    raise SystemExit(
                        'To use a configuration file the permissions'
                        ' need to be "0600" or "0400"'
                    )
        else:
            LOG.error('Config file %s not found,' % self.config_file)

    def config_args(self, section='default'):
        """Loop through the configuration file and set all of our values.

        :param section: ``str``
        :return: ``dict``
        """

        # setup the parser to for safe config parsing with a no value argument
        # Added per - https://github.com/cloudnull/turbolift/issues/2
        if sys.version_info >= (2, 7, 0):
            parser = ConfigParser.SafeConfigParser(allow_no_value=True)
        else:
            parser = ConfigParser.SafeConfigParser()

        # Set to preserve Case
        parser.optionxform = str

        try:
            parser.read(self.config_file)
            for name, value in parser.items(section):
                name = name.encode('utf8')
                if any([value == 'False', value == 'false']):
                    value = False
                elif any([value == 'True', value == 'true']):
                    value = True
                else:
                    value = is_int(value=value)
                self.args[name] = value
        except Exception as exp:
            LOG.error(
                'Failure Reading in the configuration file. %s' % exp
            )
            return {}
        else:
            return self.args
