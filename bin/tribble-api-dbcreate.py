#!/usr/bin/env python
import os
import sys

from tribble.api import start


possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                                os.pardir, os.pardir))

if os.path.exists(os.path.join(possible_topdir, 'tribble', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from tribble.admin import verbose_logger


if __name__ == '__main__':
    start.setup_system(logger=verbose_logger.load_in())
    from tribble.common.db import db_sync
    db_sync.create_db()
