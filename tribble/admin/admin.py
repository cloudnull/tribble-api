import argparse
import traceback
import sys
import datetime
import os
import tarfile
import time
import subprocess
import prettytable

# Local Packages
from tribble.appsetup import start
from tribble.admin.basestrings import strings
from tribble.admin import verbose_logger, key_setup
from tribble import info
from tribble.appsetup import rosetta


class NoKnownMethod(Exception):
    pass


class AdministrativeTasks(object):
    def __init__(self, args):
        self.args = args
        self.user = self.args.get('username')
        self.psw = self.args.get('password')
        self.key = self.args.get('key')

    def file_write(self, path, conf):
        """
        Write out the file
        """
        with open(path, 'w+') as conf_f:
            conf_f.write(conf)

    def create_keys(self):
        cert_path, key_path = key_setup.generate_self_signed_cert()
        print('created :\n  Cert => %s\n  Key => %s' % (cert_path, key_path))

    def create_db_models(self):
        from tribble.db import models
        name = 'config.cfg'
        path = '/etc/%s' % info.__appname__
        full = '%s%s%s' % (path, os.sep, name)
        if os.path.isfile(full):
            models._DB.create_all()
            print('Database Models have been created')
        else:
            sys.exit('The Config File does not exist "%s"' % full)

    def config_files_setup(self):
        """
        Setup the configuration file
        """
        print('Moving the the System Config file in place')
        # setup will copy the config file in place.
        name = 'config.cfg'
        path = '/etc/%s' % info.__appname__
        full = '%s%s%s' % (path, os.sep, name)
        config_file = strings.config_file % {'syspath': path}
        if not os.path.isdir(path):
            os.mkdir(path)
            self.file_write(path=full, conf=config_file)
        else:
            if not os.path.isfile(full):
                self.file_write(path=full, conf=config_file)
            else:
                print('Their was a configuration file found, I am compressing'
                      ' the old version and will place the new one on the'
                      ' system.')
                not_time = time.time()
                backupfile = '%s.%s.backup.tgz' % (full, not_time)
                tar = tarfile.open(backupfile, 'w:gz')
                tar.add(full)
                tar.close()
                self.file_write(path=full, conf=config_file)
        if os.path.isfile(full):
            os.chmod(full, 0600)
        print('Configuration file is ready. Please set your credentials in : %s'
              % full)

    def init_script_setup(self):
        # create the init script
        i_name = 'tribble-system'
        i_path = '/etc/init.d'
        c_path = '/etc/%s' % info.__appname__
        i_full = '%s%s%s' % (i_path, os.sep, i_name)
        init_file = strings.tribble_init % {'syspath': c_path}
        if os.path.isdir(i_path):
            if os.path.isfile(i_full):
                os.remove(i_full)
            self.file_write(path=i_full, conf=init_file)
        else:
            raise LookupError('No Init Script Directory Found')

        if os.path.isfile(i_full):
            os.chmod(i_full, 0550)

        if os.path.isfile('/usr/sbin/update-rc.d'):
            subprocess.call(['/usr/sbin/update-rc.d', '-f', i_name, 'defaults'])
        elif os.path.isfile('/sbin/chkconfig'):
            subprocess.call(['/sbin/chkconfig', i_name, 'on'])

    def delete_user(self):
        try:
            usr = CloudAuth.query.filter(CloudAuth.dcuser == self.user).first()
            start._DB.session.delete(usr)
            start._DB.session.commit()
        except Exception, exp:
            print 'Failed to delete user\nERROR : %s' % exp

    def create_user(self):
        from tribble.db.models import CloudAuth
        try:
            usr = CloudAuth(user_type=self.args.get('admin', 0),
                            dcuser=self.user,
                            created_at=datetime.datetime.utcnow(),
                            updated_at=0,
                            dcsecret=rosetta.encrypt(password=self.key,
                                                     plaintext=self.psw))
            start._DB.session.add(usr)
            start._DB.session.commit()
        except Exception, exp:
            print 'Failed to create user\nERROR : %s' % exp

    def reset_user(self):
        from tribble.db.models import CloudAuth
        try:
            user_info = CloudAuth.query.filter(
                CloudAuth.dcuser == self.user).first()
            if user_info:
                user_info.updated_at = datetime.datetime.utcnow()
                user_info.dcsecret = rosetta.encrypt(password=self.key,
                                                     plaintext=self.psw)
                start._DB.session.add(user_info)
                start._DB.session.commit()
            else:
                print 'No User Found'
        except Exception:
            print traceback.format_exc()

    def users_list(self):
        from tribble.db.models import CloudAuth
        try:
            table = prettytable.PrettyTable(['Type', 'User', 'Date Created'])
            for user in CloudAuth.query.order_by(CloudAuth.dcuser):
                table.add_row([user.user_type, user.dcuser, user.created_at])
            print table
        except Exception:
            print traceback.format_exc()


def admin_args():
    """
    Look for flags, these are all of the available start options.
    """
    parser = argparse.ArgumentParser(
        formatter_class=lambda
        prog: argparse.HelpFormatter(prog,
                                     max_help_position=31),
        usage='%(prog)s',
        description=info.__description__,
        argument_default=None,
        epilog=info.__copyright__)

    source_args = argparse.ArgumentParser(add_help=False)
    source_args.add_argument('-u',
                             '--username',
                             required=True,
                             default=None,
                             help='Set a Username')

    pw_args = argparse.ArgumentParser(add_help=False)
    pw_args.add_argument('-k',
                         '--key',
                         required=True,
                         default=None,
                         help='Set a Decryption Key')

    pw_args.add_argument('-p',
                         '--password',
                         required=True,
                         default=None,
                         help='Set Password For User')

    # Setup for the positional Arguments
    subparser = parser.add_subparsers(title='Create Tribble System Users',
                                      metavar='<Commands>\n')

    # All of the positional Arguments
    users = subparser.add_parser('users', help=('interact with all users'))
    users.set_defaults(users=True)
    users.add_argument('--list',
                       action='store_true',
                       default=None,
                       help='list all users')

    user_create = subparser.add_parser('user-create',
                                       parents=[source_args, pw_args],
                                       help='Create a User')
    user_create.set_defaults(user_create=True)
    user_create.add_argument('--admin',
                             action='store_true',
                             default=None,
                             help=('Make the User a System Admin. *** WARNING!,'
                                   ' Admins have access to EVERYTHING ***'))

    user_reset = subparser.add_parser('user-reset',
                                      parents=[source_args, pw_args],
                                       help='Reset a User')
    user_reset.set_defaults(user_reset=True)

    user_delete = subparser.add_parser('user-delete',
                                       parents=[source_args],
                                       help='Delete a User')
    user_delete.set_defaults(user_delete=True)

    create_init = subparser.add_parser('create-init',
                                       help=('attempt to create the INIT'
                                             ' script for the system'))
    create_init.set_defaults(create_init=True)

    create_config = subparser.add_parser('create-config',
                                         help=('attempt to create the Config'
                                               ' file for the system'))
    create_config.set_defaults(create_config=True)

    create_models = subparser.add_parser('create-models',
                                         help='Create the Database Models')
    create_models.set_defaults(create_models=True)

    create_certs = subparser.add_parser('create-certs',
                                         help=('Create a Self Signed'
                                               ' Certificate for the system'))
    create_certs.set_defaults(create_certs=True)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit('\nGive me something to do and I will do it\n')
    else:
        # Parse the Arguments that have been provided
        args = parser.parse_args()
        # Change Arguments in to a Dictionary
        args = vars(args)
    return args


def admin_executable():
    start.setup_system(logger=verbose_logger.load_in())
    args = admin_args()
    admin = AdministrativeTasks(args=args)
    if args.get('user_create'):
        admin.create_user()
    elif args.get('user_reset'):
        admin.reset_user()
    elif args.get('user_delete'):
        admin.delete_user()
    elif args.get('users'):
        if args.get('list'):
            admin.users_list()
        else:
            print 'No [--list] method specified...'
    elif args.get('create_init'):
        admin.init_script_setup()
    elif args.get('create_config'):
        admin.config_files_setup()
    elif args.get('create_models'):
        admin.create_db_models()
    elif args.get('create_certs'):
        admin.create_keys()
    else:
        raise NoKnownMethod('No Method used')
