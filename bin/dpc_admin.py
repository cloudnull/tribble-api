#!/usr/bin/env python
import os
import sys


possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                                os.pardir, os.pardir))

if os.path.exists(os.path.join(possible_topdir, 'tribble', '__init__.py')):
    sys.path.insert(0, possible_topdir)

if __name__ == '__main__':
    from tribble.admin import admin
    admin.admin_executable()
