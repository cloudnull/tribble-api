#!/usr/bin/env python
import os
import sys


possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                                os.pardir, os.pardir))

if os.path.exists(os.path.join(possible_topdir, 'tribble', '__init__.py')):
    sys.path.insert(0, possible_topdir)

if __name__ == '__main__':
    from tribble.admin import key_setup
    cert_path, key_path = key_setup.generate_self_signed_cert()
    print 'created cert = %s and key = %s' % (cert_path, key_path)
