#!/usr/bin/env python

# Cisco
# 1. A port-channel is an 802.3ad-style aggregate connection
# 2. A trunk is an 802.1q-tagged (multi-VLAN) link
#
# Procurve
# 1. A trunk is an 802.3ad-style aggregate connection
# 2. A VLAN-tagged link is an 802.1q-tagged (multi-VLAN) link,
# and must be tagged on each interface you want it to be available on

from __future__ import print_function
from ciscoconfparse import CiscoConfParse
import os
# import re
import sys
import tempfile

vendors = {
    'cisco': {
        'comment': '!',
        'indent': ' ',
        'interface': {
            'physical': r'^interface (([Tt](e|en)?)?([Gg](i|(igabit))?)?|[Ff](a|ast)?)(Ethernet)?(\d/)+\d+\s*$',
            'agg': r'^interface [Pp]o(rt-channel) \d+\s*$',
            'off': 'shutdown'
        },
        'vlan': r'^vlan \d+\s*$',
        'description': 'description',
        'snooping': {
            'enable': r'^ip dhcp snooping$',
            'vlans': r'^ip dhcp snooping vlan (\d+-?,?)+'
        },
        'surround': '',
        'child_end': None,
        'logging': {
            'server': 'logging host'
        }
    },
    'aruba': {
        'comment': ';',
        'indent': '   ',
        'interface': {
            'physical': r'interface \d+\s*$',
            'agg': r'interface Trk\d\s*$',
            'off': 'disable'
        },
        'vlan': r'^vlan \d+\s*$',
        'description': 'name',
        'snooping': {
            'enable': r'^dhcp snooping$',
            'vlans': r'^dhcp snooping vlan (\d+-?\s?)+'
        },
        'surround': '"',
        'child_end': 'exit',
        'logging': {
            'server': 'logging'
        }
    }
}


class Converter:
    _class = 'Converter'
    _vendor = None

    def __init__(self, oldconf=None, output_dir='./output/'):
        self.oldconf = oldconf
        self.output_dir = output_dir
        if sys.platform.startswith('win'):
            self.newconfig = CiscoConfParse(
                tempfile.NamedTemporaryFile(
                    dir=output_dir).file, factory=True)
        else:
            self.newconfig = CiscoConfParse(os.tmpfile(), factory=True)
        self.comment = ''

    def __repr__(self):
        return self._class + '({0.oldconf!s})'.format(self)


class CiscoToHPEAruba(Converter):
    _vendor = {
        'from': 'cisco',
        'to': 'aruba'
    }
    _class = "CiscoToHPEAruba"


# stub
class HPEArubaToCisco(Converter):
    _vendor = {
        'from': 'aruba',
        'to': 'cisco'
    }
    _class = 'HPEArubaToCisco'
