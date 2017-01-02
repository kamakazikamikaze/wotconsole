#!/usr/bin/env python

from setuptools import setup

setup(
    name='wotconsole',
    version='0.1dev',
    description='WarGaming World of Tanks Console API Wrapper',
    author='Kent Coble',
    author_email='coblekent@gmail.com',
    url='https://bitbucket.org/kamakazikamikaze/wot-console',
    license='LICENSE.TXT',
    long_description=open('README.rst').read(),
    install_requires=['requests']
)
