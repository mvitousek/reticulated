#!/usr/bin/env python3

import sys
from setuptools import setup, find_packages

version = '1.0.0rc1'
description = 'Static and runtime typechecking for Python'
url='https://github.com/mvitousek/reticulated'
long_description = '''

Reticulated Python provides combined static and dynamic typing, aka 
gradual typing, to Python3.'''.lstrip()

setup(
    name='retic',
    version=version,
    packages=find_packages(exclude=['tests*']),
    description=description,
    long_description=long_description,
    url=url,
    author='Michael M. Vitousek',
    author_email='mmvitousek@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Indended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ],
    keywords='type types typing typecheck typechecking typechecker gradual',
    entry_points={
        'console_scripts': [
            'retic = retic.retic:main'
        ]})
