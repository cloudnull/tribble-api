# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import argparse
import datetime
import sys
import traceback

import prettytable

import tribble
from tribble.admin import key_setup
from tribble.api.application import DB
from tribble.common.db import db_proc
from tribble.common import logger
from tribble.common import rosetta
from tribble.common import system_config
from tribble import info

CONFIG = system_config.ConfigurationSetup()


class AdministrativeTasks(object):
    """Provides the administration of Tribble.

    :param args: ``dict``
    :param log: ``object``
    """

    def __init__(self, args, log):
        self.args = args
        self.log = log
        self.user = self.args.get('username')
        self.psw = self.args.get('password')
        self.key = self.args.get('key')
        self.sql_config = CONFIG.config_args(section='sql')

    @staticmethod
    def file_write(path, conf):
        """Write out the file

        :param path: ``str``
        :param conf: ``str``
        """
        with open(path, 'wb') as conf_f:
            conf_f.write(conf)

    def create_keys(self):
        """Create a self signed certificate."""
        cert_path, key_path = key_setup.generate_self_signed_cert()
        self.log.info(
            'created :\n  Cert => %s\n  Key => %s' % (cert_path, key_path)
        )

    def create_db_models(self):
        """Execute the create_all method and create the DB."""
        DB.create_all()
        self.log.info('Database Models have been created')

    def delete_user(self):
        """Delete a user in the Tribble DB.

        :return: ``str``
        """
        try:
            sess = DB.session
            user_query = db_proc.get_user_id(user_name=self.user)
            db_proc.delete_item(session=sess, item=user_query)
        except Exception as exp:
            self.log.error(traceback.format_exc())
            return 'Failed to delete user\nERROR : %s' % exp
        else:
            db_proc.commit_session(session=sess)
            self.log.warn('User %s was deleted' % self.user)

    def create_user(self):
        """Create a user in the Tribble DB.

        :return: ``str``
        """
        try:
            sess = DB.session
            new_user = db_proc.post_user(
                admin=self.args.get('admin', 0),
                user=self.user,
                encrypted=rosetta.encrypt(
                    password=self.key, plaintext=self.psw
                )
            )
            db_proc.add_item(session=sess, item=new_user)
            db_proc.commit_session(session=sess)
        except Exception as exp:
            return 'Failed to create user\nERROR : %s' % exp
        else:
            self.log.info('User %s was created' % self.user)

    def reset_user(self):
        """Reset a user in the Tribble DB.

        :return: ``str``
        """
        try:
            sess = DB.session
            user_query = db_proc.get_user_id(self.user)
            if not user_query:
                return 'No User Found.'
            else:
                user_query.updated_at = datetime.datetime.utcnow()
                user_query.dcsecret = rosetta.encrypt(
                    password=self.key,
                    plaintext=self.psw
                )
                db_proc.commit_session(session=sess)
        except Exception:
            self.log.error(traceback.format_exc())
        else:
            self.log.warn('User %s was reset' % self.user)

    def user_list(self):
        """Print out a table of all users in the Tribble DB.

        :return: ``str``
        """
        try:
            table = prettytable.PrettyTable(['Type', 'User', 'Date Created'])
            users = db_proc.get_users()
            for user in users:
                if int(user.user_type) == 1:
                    user_type = 'admin'
                else:
                    user_type = 'user'
                table.add_row([user_type, user.dcuser, user.created_at])
        except Exception:
            self.log.error(traceback.format_exc())
        else:
            return table


def admin_args():
    """Setup all available arguments.

    :return args: ``dict``
    """
    parser = argparse.ArgumentParser(
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog,
            max_help_position=31
        ),
        usage='%(prog)s',
        description=info.__description__,
        argument_default=None,
        epilog=info.__copyright__
    )

    parser.add_argument(
        '--debug',
        default=None,
        help='enable debug mode'
    )

    source_args = argparse.ArgumentParser(add_help=False)
    source_args.add_argument(
        '-u',
        '--username',
        required=True,
        default=None,
        help='Set a Username'
    )

    pw_args = argparse.ArgumentParser(add_help=False)
    pw_args.add_argument(
        '-k',
        '--key',
        required=True,
        default=None,
        help='Set a Decryption Key'
    )

    pw_args.add_argument(
        '-p',
        '--password',
        required=True,
        default=None,
        help='Set Password For User'
    )

    # Setup for the positional Arguments
    subparser = parser.add_subparsers(
        title='Create Tribble System Users',
        metavar='<Commands>\n'
    )

    # All of the positional Arguments
    user_list = subparser.add_parser('user-list', help='List all users')
    user_list.set_defaults(method='user_list')

    create_user = subparser.add_parser(
        'user-create',
        parents=[source_args, pw_args],
        help='Create a User'
    )
    create_user.set_defaults(method='create_user')
    create_user.add_argument(
        '--admin',
        action='store_true',
        default=None,
        help=('Make the User a System Admin. *** WARNING!, Admins have access'
              ' to EVERYTHING ***')
    )

    reset_user = subparser.add_parser(
        'user-reset',
        parents=[source_args, pw_args],
        help='Reset a User'
    )
    reset_user.set_defaults(method='reset_user')

    delete_user = subparser.add_parser(
        'user-delete',
        parents=[source_args],
        help='Delete a User'
    )
    delete_user.set_defaults(method='delete_user')

    init_script_setup = subparser.add_parser(
        'create-init',
        help='attempt to create the INIT script for the system'
    )
    init_script_setup.set_defaults(method='init_script_setup')

    create_db_models = subparser.add_parser(
        'create-models',
        help='Create the Database Models'
    )
    create_db_models.set_defaults(method='create_db_models')

    create_keys = subparser.add_parser(
        'create-certs',
        help='Create a Self Signed Certificate for the system'
    )
    create_keys.set_defaults(method='create_keys')

    if len(sys.argv) == 1:
        parser.print_help()
        raise SystemExit('\nGive me something to do and I will do it\n')
    else:
        # Parse the Arguments that have been provided
        args = parser.parse_args()
        # Change Arguments in to a Dictionary
        args = vars(args)
    return args


def admin_executable():
    """Execute the main method.

    When executing this method will get the "method" from the parsed arguments
    and then execute the class function.
    """
    default_config = CONFIG.config_args()
    log = logger.logger_setup(
        name='tribble-api',
        debug_logging=default_config.get('debug_mode', False)
    )

    args = admin_args()
    admin = AdministrativeTasks(args=args, log=log)

    try:
        action = getattr(admin, args['method'])
        print(action())
    except Exception as exp:
        raise tribble.NoKnownMethod('no method loaded, error: %s' % exp)
