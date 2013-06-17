#!/usr/bin/env python

import setuptools
import sys
from tribble import info

# Check the version of Python that we have been told to use
if sys.version_info < (2, 6, 0):
    sys.stderr.write('The Tribble System Presently requires'
                     ' Python 2.6.0 or greater\n')
    sys.exit('\nUpgrade python because your'
             ' version of it is VERY deprecated\n')

with open('README') as r_file:
    long_description = r_file.read()

T_M = ['paramiko',
       'Fabric==1.6.0',
       'python-daemon==1.6',
       'PyCrypto',
       'PyChef',
       'sqlalchemy',
       'argparse',
       'apache-libcloud',
       'mysql-python',
       'statsd',
       'Flask-RESTful',
       'Flask',
       'Flask-SQLAlchemy',
       'prettytable',
       'gevent']

setuptools.setup(
    name=info.__appname__,
    version=info.__version__,
    author=info.__author__,
    author_email=info.__email__,
    description=info.__description__,
    long_description=long_description,
    license=info.__license__,
    packages=['tribble',
              'tribble.admin',
              'tribble.appsetup',
              'tribble.db',
              'tribble.dist',
              'tribble.operations',
              'tribble.purveyors',
              'tribble.purveyors.chef',
              'tribble.purveyors.fabric',
              'tribble.webapp'],
    url=info.__urlinformation__,
    install_requires=T_M,
    classifiers=[
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    entry_points={
        "console_scripts":
            ["tribble-api = tribble.run:executable",
             "tribble-admin = tribble.admin:admin_executable"]
    }
)
