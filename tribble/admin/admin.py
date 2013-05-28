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

    # Setup for the positional Arguments
    subparser = parser.add_subparsers(title='Infrastructure Spawner',
                                      metavar='<Commands>\n')

    # All of the positional Arguments
    usersactions = subparser.add_parser('users',
                                        help=('interact with all users'))
    usersactions.set_defaults(users=True,
                              user=None)
    useractions = subparser.add_parser('user',
                                       help=('interact with a user'))
    useractions.set_defaults(user=True,
                             users=None)

    usersactions.add_argument('--list',
                             action='store_true',
                             default=None,
                             help='list all users')

    useractions.add_argument('--info',
                             nargs=3,
                             default=None,
                             required=True,
                             metavar='[X]',
                             help='<username> <password> <key>')

    useractions.add_argument('--create',
                             action='store_true',
                             default=None,
                             help='create user credentials')

    useractions.add_argument('--delete',
                             action='store_true',
                             default=None,
                             help='Delete a User')

    useractions.add_argument('--reset',
                             action='store_true',
                             default=None,
                             help='reset user credentials')

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
    def delete_user(user, psw, key):
        try:
            usr = CloudAuth.query.filter(CloudAuth.dcuser == user).first()
            start._DB.session.delete(usr)
            start._DB.session.commit()
        except Exception, exp:
            print 'Failed to delete user\nERROR : %s' % exp

    def create_user(user, psw, key):
        try:
            usr = CloudAuth(dcuser=user,
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
            table = prettytable.PrettyTable(['User', 'Date Created'])
            for user in CloudAuth.query.order_by(CloudAuth.dcuser):
                table.add_row([user.dcuser, user.created_at])
            print table
        except Exception:
            print traceback.format_exc()

    args = admin_args()
    start.setup_system(logger=verbose_logger.load_in())
    from tribble.db.models import CloudAuth, Instances

    if args.get('user'):
        if any([args.get('create'), args.get('reset'), args.get('delete')]):
            user, psw, key = args['info']
            if args.get('create'):
                create_user(user, psw, key)
            elif args.get('reset'):
                reset_user(user, psw, key)
            elif args.get('delete'):
                delete_user(user, psw, key)
            else:
                raise NoKnownMethod('Method Not specified')
        else:
            print 'No [--create], [--reset], or [--delete] method specified...'
    elif args.get('users'):
        if args.get('list'):
            users_list()
        else:
            print 'No [--list] method specified...'
