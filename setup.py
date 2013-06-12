#!/usr/bin/env python

import setuptools
import sys
import os
import tarfile
import time
import subprocess

# Local Packages
from basestrings import strings
from tribble import info

# Check the version of Python that we have been told to use
if sys.version_info < (2, 6, 0):
    sys.stderr.write('The Tribble System Presently requires'
                     ' Python 2.6.0 or greater\n')
    sys.exit('\nUpgrade python because your version of it is VERY deprecated\n')

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
            ["tribbleapi = tribble.run:executable"]
    }
)


def file_write(path, conf):
    """
    Write out the file
    """
    with open(path, 'w+') as conf_f:
        conf_f.write(conf)


def config_files_setup():
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
        file_write(path=full, conf=config_file)
    else:
        if not os.path.isfile(full):
            file_write(path=full, conf=config_file)
        else:
            print('Their was a configuration file found, I am compressing the '
                  'old version and will place the new one on the system.')
            not_time = time.time()
            backupfile = '%s.%s.backup.tgz' % (full, not_time)
            tar = tarfile.open(backupfile, 'w:gz')
            tar.add(full)
            tar.close()
            file_write(path=full, conf=config_file)
    if os.path.isfile(full):
        os.chmod(full, 0600)
    print('Configuration file is ready. Please set your credentials in : %s'
          % full)


def init_script_setup():
    # create the init script
    i_name = 'tribble-system'
    i_path = '/etc/init.d'
    c_path = '/etc/%s' % info.__appname__
    i_full = '%s%s%s' % (i_path, os.sep, i_name)
    init_file = strings.tribble_init % {'syspath': c_path}
    if os.path.isdir(i_path):
        if os.path.isfile(i_full):
            os.remove(i_full)
        file_write(path=i_full, conf=init_file)
    else:
        raise LookupError('No Init Script Directory Found')

    if os.path.isfile(i_full):
        os.chmod(i_full, 0550)

    if os.path.isfile('/usr/sbin/update-rc.d'):
        subprocess.call(['/usr/sbin/update-rc.d', '-f', i_name, 'defaults'])
    elif os.path.isfile('/sbin/chkconfig'):
        subprocess.call(['/sbin/chkconfig', i_name, 'on'])


if len(sys.argv) > 1:
    if sys.argv[1] == 'install':
        # Run addtional Setup things
        config_files_setup()
        init_script_setup()
