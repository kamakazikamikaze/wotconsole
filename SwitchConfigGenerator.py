#!/bin/env python
from __future__ import print_function
import os
# import csv
import openpyxl
# from pprint import pprint
from ciscoconfparse import CiscoConfParse


def vlan_extract(oldconfig, newconfig):
    vlans = []
    lines = []  # We need to modify the snooping command without calling commit so soon
    AllVlanObjects = oldconfig.find_objects_w_child(r'^vlan', r'^ name')
    lines.append('ip dhcp snooping vlan ')
    lines.append('no ip dhcp snooping information option')
    lines.append('ip dhcp snooping')
    lines.append('vlan internal allocation policy ascending')
    for obj in AllVlanObjects:
        lines.append('!\n' + obj.text)
        vlans.append(obj.text.split()[-1])
        for child in obj.children:
            lines.append(child.text)
    lines[0] += ','.join(vlans)
    for line in lines:
        newconfig.append_line(line)
    newconfig.commit()


def migrate_ports(oldconfig, newconfig, hostname):
    filtered_files = [x for x in os.listdir(
        './cutsheets/') if (x.split()[0].split('-')[0] in hostname)]
    jacks = {}
    for file in [x for x in filtered_files if 'as-is' in x.lower()]:
        wb = openpyxl.load_workbook('./cutsheets/' + file)
        for ws in wb:
            for row in ws.rows[1:]:
                for cell in row:
                    # CiscoConfParse cannot accept leading 0's in port names,
                    # ex. Fa1/0/01. While this is a localized issue of using
                    # Excel's autofill, we'll add the courtesy of dropping it
                    # from the port (not module) number ourselves
                    try:
                        jacks[int(cell.value)] = {
                            'old port': '/'.join(row[0].value.split('/')[0:-1] + [str(int(row[0].value.split('/')[-1]))]),
                            'old switch': ws.title
                        }
                    except:
                        continue
    for file in [x for x in filtered_files if 'to be' in x.lower()]:
        wb = openpyxl.load_workbook('./cutsheets/' + file)
        for ws in wb:
            if not hostname.lower() in ws['A1'].value.lower():
                continue  # This isn't a worksheet for the switch
            for row in ws.rows[3:]:
                portname = '/'.join(row[0].value.split('/')[0:-1] +
                                    [str(int(row[0].value.split('/')[-1]))])
                transferred = False
                for cell in row:
                    try:
                        port = oldconfig.find_interface_objects(
                            jacks[int(cell.value)]['old port'])
                        newconfig.append_line('!')
                        newconfig.append_line('interface ' + portname)
                        for child in port[0].children:
                            newconfig.append_line(child.text)
                        transferred = True
                        break  # Got the jack, move to next row
                    except (ValueError, TypeError):  # Failures for int() cast
                        continue  # Try next cell
                    except KeyError:
                        # We have a valid jack number but it's new
                        print(
                            'Port',
                            portname,
                            'is connected to a new jack. Please configure this manually.')
                        newconfig.append_line('!')
                        newconfig.append_line('interface ' + portname)
                        newconfig.append_line(' %%NEW CONNECTION%%')
                        transferred = True
                        break
                if not transferred:
                    print(
                        'Port',
                        portname,
                        'is not connected to a jack and will be shutdown. Please confirm this manually')
                    newconfig.append_line('!')
                    newconfig.append_line('interface ' + portname)
                    newconfig.append_line(' shutdown')
    newconfig.commit()


# search interfaces for non-standard configs that will need to be reviewed
# individually
def interfaces_for_review(newconfig):
    PowerInts = newconfig.find_objects_w_child(r'^interf', r'^ power')
    # print PowerInts
    if PowerInts:
        print('\nManually review the following Interfaces for Power settings')
        for obj in PowerInts:
            print(' ', obj.text)
    DuplexInts = newconfig.find_objects_w_child(r'^interf', r'^ duplex')
    if DuplexInts:
        print('\nManually review the following Interfaces for Duplex settings')
        for obj in DuplexInts:
            print(' ', obj.text)
    SpeedInts = newconfig.find_objects_w_child(r'^interf', r'^ speed')
    if SpeedInts:
        print('\nManually review the following Interfaces for Speed settings')
        for obj in SpeedInts:
            print(' ', obj.text)
    PurgatoryInts = newconfig.find_objects_wo_child(
        r'^interf', r'^ switchport mode')
    if PurgatoryInts:
        print('\nThese interfaces did not specify Access or Trunk mode.\nManually review the following:')
        for obj in PurgatoryInts:
            print(' ', obj.text)
    print('')


# Find the first child object containing switchport voice vlan matching
# the voice vlan in config, and adding that child to any access ports
# without a voice vlan
def add_voice_vlan(newconfig):
    Modified = []
    Voice = ' switchport voice vlan ' + voicevlan
    NewIntfs = newconfig.find_objects_wo_child(
        r'^interf', r'^ switchport mode trunk')
    for obj in NewIntfs:
        if obj.access_vlan != 0:  # testing to see if access port, should probably adjust to search for switchport mode access, but some ports have this explicit and some don't
            hasVoice = False
            for child in obj.children:
                if 'voice' in child.text:
                    hasVoice = True
            if hasVoice == False:
                obj.append_to_family(Voice)
                Modified.append(obj.text)
    if len(Modified) > 0:
        print('The following ports had a Voice VLAN added. Please manually check that this is appropriate:')
        for each in Modified:
            print(' ', each)
    newconfig.commit()


# On trunk ports, remove access/voice vlan configs, spanning-tree
# portfast, and no snmp trap link-status
def trunk_cleanup(newconfig):
    TrunkInts = newconfig.find_objects_w_child(
        r'^interf', r'^ switchport mode trunk|shutdown')
    for obj in TrunkInts:
        for child in obj.children:
            if r'switchport access' in child.text:
                child.delete()
            elif r'switchport voice' in child.text:
                child.delete()
            elif r'spanning-tree portfast' in child.text:
                child.delete()
            elif r'no snmp' in child.text:
                child.delete()
    newconfig.commit()
    # Now we want to remove from trunk ports VLANs 1,1002,1003,1004,1005
    # I am thinking we can detect any ports with these VLANs trunked, extract
    # all VLANs, delete the child object, remove the unwanted VLANS, then
    # append a new child
    TrunkInts = newconfig.find_objects_w_child(
        r'^interf', r'^ switchport mode trunk')
    for obj in TrunkInts:
        TrunkLines = obj.re_search_children(r'switchport trunk allowed vlan')
        obj.delete_children_matching(r'switchport trunk allowed vlan')
        for child in TrunkLines:
            # TrunkVlans = []
            Add = False
            if 'add' in child.text.lower():
                Add = True
            TrunkNumbers = set(child.text.split()[-1].split(','))
            NumsToRemove = set(
                ['1', '1002-1005', '1002', '1003', '1004', '1005'])
            TrunkNumbers = list(TrunkNumbers - NumsToRemove)
            if len(TrunkNumbers) > 0:
                if Add:
                    TrunkConfigLine = ' switchport trunk allowed vlan add ' + \
                        ','.join(TrunkNumbers)
                else:
                    TrunkConfigLine = ' switchport trunk allowed vlan ' + \
                        ','.join(TrunkNumbers)
                obj.append_to_family(TrunkConfigLine)
    newconfig.commit()


# search interfaces for non-standard configs that will need to be reviewed
# individually.  This must be run AFTER trunk_cleanup()
def remove_mdix_and_dot1q(newconfig):
    MdixInts = newconfig.find_objects('no\smdix\sauto')
    for obj in MdixInts:
        if obj != []:
            obj.delete()
    newconfig.commit()
    Dot1qInts = newconfig.find_objects(
        'switchport\strunk\sencapsulation\sdot1q')
    for obj in Dot1qInts:
        if obj != []:
            obj.delete()
    newconfig.commit()


# on access ports, remove native and trunk vlans
def AccessCleanUp(newconfig):
    AccessInts = newconfig.find_objects_w_child(
        r'^interf', r'^ switchport mode access')
    for obj in AccessInts:
        for child in obj.children:
            if r'switchport trunk' in child.text:
                child.delete()
    newconfig.commit()
    # I found that some configs are missing the 'mode access', so I am also
    # applying to any that are missing 'switchport mode'
    AccessInts = newconfig.find_objects_wo_child(
        r'^interf', r'^ switchport mode')
    for obj in AccessInts:
        for child in obj.children:
            if r'switchport trunk' in child.text:
                child.delete()
    newconfig.commit()


# extract management vlan and IP address, assuming layer 2 switch with only VLAN1 and management VLAN
# this needs to be edited to just extract the IP, and use the standard
# configuration for the rest of management VLAN
def extract_management(oldconfig, newconfig):
    Vlan1 = oldconfig.find_objects(r'^interface Vlan1$')
    for vlan in Vlan1:
        vlan.delete()
    oldconfig.commit()
    VlanInts = oldconfig.find_objects_wo_child(
        r'^interface Vlan', r'^ ip address')
    for vlan in VlanInts:
        newconfig.append_line(vlan.text)
        for child in vlan.children:
            newconfig.append_line(child.text)
        newconfig.append_line('!')
    newconfig.commit()
    # Need to extract the management vlan number to add to the tacacs
    # interface on 4506 switches
    # We should probably create our own append function to add items we want
    # to newconfig
    ManagementVlan = oldconfig.find_objects_w_child(
        r'^interface Vlan', r'^ ip address')
    # print(ManagementVlan)
    newconfig.append_line('!')
    newconfig.append_line(ManagementVlan[0].text)
    if 'n' in raw_input(
            'Will this equipment use the same IP address? [Y|n]: ').lower():
        NewIP = raw_input('Enter new IP address: ')
        NewGateway = raw_input('Enter new Gateway: ')
        NewMask = raw_input('Enter new subnet Mask: ')
        newconfig.append_line(' ip address ' + NewIP + ' ' + NewMask)
        newconfig.append_line('!')
        newconfig.append_line('ip default-gateway ' + NewGateway)
        newconfig.append_line('!')
    else:
        for child in ManagementVlan[0].children:
            newconfig.append_line(child.text)
        newconfig.append_line('!')
        DefaultGateway = oldconfig.find_objects(r'^ip default-gateway')
        newconfig.append_line('!')
        newconfig.append_line(DefaultGateway[0].text)
        newconfig.append_line('!')
    newconfig.commit()


def file_export(outputfile, newconfig):
    newconfig.save_as('./output/' + outputfile)
    print('\nFile saved as', outputfile)


if __name__ == '__main__':
    directory = sorted([x for x in os.listdir('./configs/') if 'confg' in x])
    for item in enumerate(directory):
        print(' [' + str(item[0] + 1) + ']', item[1])
    name = None
    while not name in xrange(1, len(directory) + 1):
        name = int(
            raw_input('Please select the file number of the old config: '))
    file = directory[name - 1]

    if 'n' in raw_input('Generate full config file?[Y|n] ').lower():
        hostname = raw_input('Enter hostname of new switch: ')
        outputfile = raw_input('Enter output file name: ')
        oldconfig = CiscoConfParse('./configs/' + file, factory=True)
        newconfig = CiscoConfParse(os.tmpfile(), factory=True)
        migrate_ports(oldconfig, newconfig, hostname)
    else:
        switch_types = ['3560', '3750', '3850', '4506', 'Other']
        print('Compatible switch models:')
        for switch in enumerate(switch_types):
            print(' [' + str(switch[0] + 1) + ']', switch[1])
        SwitchType = None
        while not SwitchType in xrange(1, len(switch_types) + 1):
            SwitchType = int(
                raw_input('What switch model are you programming? ')) - 1

        baseconfig = '.txt'
        if (SwitchType == len(switch_types) - 1):
            baseconfig = 'baseconfig.txt'
        else:
            baseconfig = switch_types[SwitchType] + 'base.txt'

        hostname = raw_input('Enter hostname of new switch: ')
        voicevlan = raw_input('Enter voice VLAN: ')
        outputfile = raw_input('Enter output file name: ')

        # parse the config file argument and then extract the interfaces
        oldconfig = CiscoConfParse('./configs/' + file, factory=True)
        # The new parser needs a file associated with it, so create a throwaway.
        # Trying to give it a legit file strangely invokes an error later on...
        newconfig = CiscoConfParse(os.tmpfile(), factory=True)

        newconfig.append_line('!')
        newconfig.append_line('hostname ' + hostname)
        newconfig.append_line('!')
        newconfig.commit()

        vlan_extract(oldconfig, newconfig)
        migrate_ports(oldconfig, newconfig, hostname)
        interfaces_for_review(newconfig)
        add_voice_vlan(newconfig)
        trunk_cleanup(newconfig)
        # This must be run AFTER trunk_cleanup()
        remove_mdix_and_dot1q(newconfig)

        extract_management(oldconfig, newconfig)
        newconfig.append_line('!')
        with open('./templates/' + baseconfig, 'r') as b:
            for line in b:
                newconfig.append_line(line.rstrip())
        newconfig.commit()

    file_export(outputfile, newconfig)
