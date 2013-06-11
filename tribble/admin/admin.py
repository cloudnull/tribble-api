import argparse
import traceback
import sys
import datetime
from tribble.appsetup import start
from tribble.admin import verbose_logger
from tribble import info
from tribble.appsetup import rosetta


class NoKnownMethod(Exception):
    pass


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
    users.set_defaults(users=True,
                       user_create=None,
                       user_reset=None,
                       user_delete=None)
    users.add_argument('--list',
                       action='store_true',
                       default=None,
                       help='list all users')

    user_create = subparser.add_parser('user-create',
                                       parents=[source_args, pw_args],
                                       help='Create a User')
    user_create.set_defaults(user=None,
                             user_create=True,
                             user_reset=None,
                             user_delete=None)

    user_reset = subparser.add_parser('user-reset',
                                      parents=[source_args, pw_args],
                                       help='Reset a User')
    user_reset.set_defaults(user=None,
                            user_create=None,
                            user_reset=True,
                            user_delete=None)

    user_delete = subparser.add_parser('user-delete',
                                       parents=[source_args],
                                       help='Delete a User')
    user_delete.set_defaults(user=None,
                             user_create=None,
                             user_reset=None,
                             user_delete=True)

    user_create.add_argument('--admin',
                             action='store_true',
                             default=None,
                             help=('Make the User a System Admin. *** WARNING!,'
                                   ' Admins have access to EVERYTHING ***'))

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
    def delete_user(user):
        try:
            usr = CloudAuth.query.filter(CloudAuth.dcuser == user).first()
            start._DB.session.delete(usr)
            start._DB.session.commit()
        except Exception, exp:
            print 'Failed to delete user\nERROR : %s' % exp

    def create_user(user, psw, key):
        try:
            usr = CloudAuth(user_type=args.get('admin', 0),
                            dcuser=user,
                            created_at=datetime.datetime.utcnow(),
                            updated_at=0,
                            dcsecret=rosetta.encrypt(password=key,
                                                     plaintext=psw))
            start._DB.session.add(usr)
            start._DB.session.commit()
        except Exception, exp:
            print 'Failed to create user\nERROR : %s' % exp

    def reset_user(user, psw, key):
        try:
            user_info = CloudAuth.query.filter(
                CloudAuth.dcuser == user).first()
            if user_info:
                user_info.updated_at = datetime.datetime.utcnow()
                user_info.dcsecret = rosetta.encrypt(password=key,
                                                     plaintext=psw)
                start._DB.session.add(user_info)
                start._DB.session.commit()
            else:
                print 'No User Found'
        except Exception:
            print traceback.format_exc()

    def users_list():
        import prettytable
        try:
            table = prettytable.PrettyTable(['Type', 'User', 'Date Created'])
            for user in CloudAuth.query.order_by(CloudAuth.dcuser):
                table.add_row([user.user_type, user.dcuser, user.created_at])
            print table
        except Exception:
            print traceback.format_exc()

    args = admin_args()
    start.setup_system(logger=verbose_logger.load_in())
    from tribble.db.models import CloudAuth, Instances
    if any([args.get('user_create'), args.get('user_reset')]):
        user = args.get('username')
        psw = args.get('password')
        key = args.get('key')
        if args.get('user_create'):
            create_user(user, psw, key)
        else:
            reset_user(user, psw, key)
    elif args.get('user_delete'):
        user = args.get('username')
        delete_user(user)
    elif args.get('users'):
        if args.get('list'):
            users_list()
        else:
            print 'No [--list] method specified...'
