#!/usr/bin/env python

from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='wotconsole',
    version='0.4.2',
    description='WarGaming World of Tanks Console API Wrapper',
    author='Kent Coble',
    author_email='coblekent@gmail.com',
    url='https://bitbucket.org/kamakazikamikaze/wotconsole',
    license='LICENSE.TXT',
    long_description=long_description,
    packages=['wotconsole'],
    install_requires=['requests>=2.22.0']
)
