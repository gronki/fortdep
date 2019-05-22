# -*- coding: utf-8 -*-

import sys
assert sys.version_info[0] >= 3

from setuptools import setup
setup(
    name = 'fortdep',
    version = '190520',
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
