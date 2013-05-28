import argparse
import sys
from tribble import info
from tribble import daemonizer


def executable():
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

    parser.add_argument('--start',
                        action='store_true',
                        default=None,
                        help='Start %(prog)s')

    parser.add_argument('--restart',
                        action='store_true',
                        default=None,
                        help='Restart %(prog)s')

    parser.add_argument('--stop',
                        action='store_true',
                        default=None,
                        help='Stops %(prog)s')

    parser.add_argument('--status',
                        action='store_true',
                        default=None,
                        help='Show %(prog)s Status')

    parser.add_argument('--debug-mode',
                        action='store_true',
                        default=None,
                        help=('Uses the standard "stdout" and "stderr"'
                              ' streams while in Daemon Mode'))

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit('\nGive me something to do and I will do it\n')
    else:
        # Parse the Arguments that have been provided
        args = parser.parse_args()

        # Change Arguments in to a Dictionary
        args = vars(args)
        daemonizer.daemon_args(p_args=args)

if __name__ == '__main__':
    executable()
