#!/usr/bin/env python

from setuptools import setup

setup(
    name='wotconsole',
    version='0.4',
    description='WarGaming World of Tanks Console API Wrapper',
    author='Kent Coble',
    author_email='coblekent@gmail.com',
    url='https://bitbucket.org/kamakazikamikaze/wotconsole',
    license='LICENSE.TXT',
    long_description=open('README.rst').read(),
    packages=['wotconsole'],
    install_requires=['requests>=2.12.4']
)
