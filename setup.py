#!/usr/bin/env python

# check Python's version
import sys
if sys.version < '2.4':
    sys.stderr.write('This module requires at least Python 2.5\n')
    sys.exit(1)

# import statements
import platform
from setuptools import setup, Command

# debug
DISTUTILS_DEBUG = False

# check linux platform
if not platform.system().startswith('Linux'):
    sys.stderr.write("inotify is not available under %s\n" % platform)
    sys.exit(1)


#class test(Command):
#    description = 'run tests'
#    user_options = []
#
#    def initialize_options(self):
#        pass
#
#    def finalize_options(self):
#        pass
#
#    def run(self):
#        from tests.run_all import main
#        main()


classif = [
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GPL v3',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries',
    'Topic :: System :: Monitoring'
    ]


setup(
#    cmdclass = {'test': test},
    name = 'treewatcher',
    version = '0.0.1',
    description = 'Linux filesystem directory monitoring',
    author = 'Jean-Baptiste Denis',
    author_email = 'jeanbaptiste.denis@gmail.com',
    license = 'GPL v3',
    platforms = 'Linux',
    classifiers = classif,
    packages = ['treewatcher'],
    install_requires = ["inotifyx>=0.1.1"]
    )
