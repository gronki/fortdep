# -*- coding: utf-8 -*-

import sys
if sys.version_info[0] < 3:
    print(u'Python 3 is required. Please use python3 to run this script.')
    exit(-1)

from setuptools import setup
setup(
    name = 'fortdep',
    version = '190603',
    description = 'generates dependencies between Fortran source files to include in Makefile',
    url = 'https://github.com/gronki/fortdep',
    author = 'Dominik Gronkiewicz',
    author_email = 'gronki@gmail.com',
    license = 'MIT',
    py_modules = ['fortdep', 'fortdep2'],
    entry_points = {
        'console_scripts': [
            "fortdep = fortdep:main",
            "fortdep2 = fortdep2:main",
        ]
    }
)
