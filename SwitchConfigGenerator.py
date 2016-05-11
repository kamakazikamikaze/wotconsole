#!/bin/env python
from __future__ import print_function
import os
# import csv
import openpyxl
# from pprint import pprint
from ciscoconfparse import CiscoConfParse


def VlanExtract(config1, config2):
    vlans = []
    lines = []  # We need to modify the snooping command without calling commit so soon
    AllVlanObjects = config1.find_objects_w_child(r'^vlan', r'^ name')
    lines.append('ip dhcp snooping vlan ')
    lines.append('no ip dhcp snooping information option')
    lines.append('ip dhcp snooping')
    lines.append('vlan internal allocation policy ascending')
    for obj in AllVlanObjects:
        lines.append("!\n" + obj.text)
        vlans.append(obj.text.split()[-1])
        for child in obj.children:
            lines.append(child.text)
    lines[0] += ','.join(vlans)
    for line in lines:
        config2.append_line(line)
    config2.commit()


def migrate_ports(oldconfig, newconfig, hostname):
    filtered_files = [x for x in os.listdir(
        './cutsheets/') if (x.split()[0].split('-')[0] in hostname)]
    jacks = {}
    # We'll want to add ports in logical order to the config, so we'll use a
    # list to track them
    portorder = []
    # Originally I had this load all the old jacks/ports first and then add
    # the new ports, however I realized that this would increase the amount of
    # iterations necessary later for finding which ports actually applied to
    # this new switch. While it would be good to have in case we expand this
    # to a multi-switch config generator, I don't see the need to cling onto
    # legacy code when it's easy enough to just swap the two points of logic
    # to allow it
    for file in [x for x in filtered_files if 'to be' in x.lower()]:
        wb = openpyxl.load_workbook('./cutsheets/' + file)
        for ws in wb:
            if not hostname.lower() in ws['A1'].value.lower():
                continue
            for row in ws.rows[3:]:
                for cell in row:
                    try:
                        # CiscoConfParse breaks if there is an extra value, ex.
                        # F1/0/01 as opposed to F1/0/1. We'll spilt this up and
                        # re-join it, casting the last/port segment into an integer
                        # to drop the leading 0
                        jacks[int(cell.value)] = {
                            'new port': '/'.join(row[0].value.split('/')[0:-1] + [str(int(row[0].value.split('/')[-1]))]),
                            'new switch': ws.title
                        }
                        portorder.append(int(cell.value))
                        continue
                    except (ValueError, TypeError):
                        pass
    for file in [x for x in filtered_files if 'as-is' in x.lower()]:
        wb = openpyxl.load_workbook('./cutsheets/' + file)
        for ws in wb:
            for row in ws.rows[1:]:
                for cell in row:
                    try:
                        if int(cell.value) in jacks.keys():
                            jacks[int(cell.value)].update({
                                'old port': '/'.join(row[0].value.split('/')[0:-1] + [str(int(row[0].value.split('/')[-1]))]),
                                'old switch': ws.title
                            })
                    except (ValueError, TypeError):
                        pass
    for jack in portorder:
        try:
            port = oldconfig.find_interface_objects(jacks[jack]['old port'])
            intname = port[0].name
            port[0].replace(intname, jacks[jack]['new port'])
            newconfig.append_line("!")
            newconfig.append_line(port[0].text)
            for child in port[0].children:
                newconfig.append_line(child.text)
        except KeyError:
            print(
                jacks[jack]['new port'],
                'is connected to jack',
                jack,
                'which does not exist on the old switch. Please manually add new configuration for it.')
    # pprint(jacks)
    newconfig.commit()


# search interfaces for non-standard configs that will need to be reviewed
# individually
def InterfacesForReview(config2):
    PowerInts = config2.find_objects_w_child(r"^interf", r"^ power")
    # print PowerInts
    if PowerInts:
        print("\nManually review the following Interfaces for Power settings")
        for obj in PowerInts:
            print(' ', obj.text)
    DuplexInts = config2.find_objects_w_child(r"^interf", r"^ duplex")
    if DuplexInts:
        print("\nManually review the following Interfaces for Duplex settings")
        for obj in DuplexInts:
            print(' ', obj.text)
    SpeedInts = config2.find_objects_w_child(r"^interf", r"^ speed")
    if SpeedInts:
        print("\nManually review the following Interfaces for Speed settings")
        for obj in SpeedInts:
            print(' ', obj.text)
    PurgatoryInts = config2.find_objects_wo_child(
        r"^interf", r"^ switchport mode")
    if PurgatoryInts:
        print("\nThese interfaces did not specify Access or Trunk mode.\nManually review the following:")
        for obj in PurgatoryInts:
            print(' ', obj.text)
    print('')


# Find the first child object containing switchport voice vlan matching
# the voice vlan in config, and adding that child to any access ports
# without a voice vlan
def AddVoiceVlan(config2):
    Modified = []
    Voice = ' switchport voice vlan ' + voicevlan
    NewIntfs = config2.find_objects_wo_child(
        r"^interf", r"^ switchport mode trunk")
    for obj in NewIntfs:
        if obj.access_vlan != 0:  # testing to see if access port, should probably adjust to search for switchport mode access, but some ports have this explicit and some don't
            hasVoice = False
            for child in obj.children:
                if "voice" in child.text:
                    hasVoice = True
            if hasVoice == False:
                obj.append_to_family(Voice)
                Modified.append(obj.text)
    if len(Modified) > 0:
        print("The following ports had a Voice VLAN added. Please manually check that this is appropriate:")
        for each in Modified:
            print(' ', each)
    config2.commit()


# On trunk ports, remove access/voice vlan configs, spanning-tree
# portfast, and no snmp trap link-status
def TrunkCleanUp(config2):
    TrunkInts = config2.find_objects_w_child(
        r'^interf', r'^ switchport mode trunk|shutdown')
    for obj in TrunkInts:
        for child in obj.children:
            if r"switchport access" in child.text:
                child.delete()
            elif r"switchport voice" in child.text:
                child.delete()
            elif r"spanning-tree portfast" in child.text:
                child.delete()
            elif r"no snmp" in child.text:
                child.delete()
    config2.commit()
    # Now we want to remove from trunk ports VLANs 1,1002,1003,1004,1005
    # I am thinking we can detect any ports with these VLANs trunked, extract
    # all VLANs, delete the child object, remove the unwanted VLANS, then
    # append a new child
    TrunkInts = config2.find_objects_w_child(
        r'^interf', r'^ switchport mode trunk')
    for obj in TrunkInts:
        TrunkLines = obj.re_search_children(r"switchport trunk allowed vlan")
        obj.delete_children_matching(r"switchport trunk allowed vlan")
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
                        ",".join(TrunkNumbers)
                else:
                    TrunkConfigLine = ' switchport trunk allowed vlan ' + \
                        ",".join(TrunkNumbers)
                obj.append_to_family(TrunkConfigLine)
    config2.commit()


# search interfaces for non-standard configs that will need to be reviewed
# individually.  This must be run AFTER TrunkCleanUp()
def RemoveMDIXandDOT1Q(config2):
    MdixInts = config2.find_objects("no\smdix\sauto")
    for obj in MdixInts:
        if obj != []:
            obj.delete()
    config2.commit()
    Dot1qInts = config2.find_objects("switchport\strunk\sencapsulation\sdot1q")
    for obj in Dot1qInts:
        if obj != []:
            obj.delete()
    config2.commit()


# on access ports, remove native and trunk vlans
def AccessCleanUp(config2):
    AccessInts = config2.find_objects_w_child(
        r'^interf', r'^ switchport mode access')
    for obj in AccessInts:
        for child in obj.children:
            if r"switchport trunk" in child.text:
                child.delete()
    config2.commit()
    # I found that some configs are missing the "mode access", so I am also
    # applying to any that are missing "switchport mode"
    AccessInts = config2.find_objects_wo_child(
        r'^interf', r'^ switchport mode')
    for obj in AccessInts:
        for child in obj.children:
            if r"switchport trunk" in child.text:
                child.delete()
    config2.commit()


# extract management vlan and IP address, assuming layer 2 switch with only VLAN1 and management VLAN
# this needs to be edited to just extract the IP, and use the standard
# configuration for the rest of management VLAN
def ExtractManagement(config1, config2):
    Vlan1 = config1.find_objects(r"^interface Vlan1$")
    for vlan in Vlan1:
        vlan.delete()
    config1.commit()
    VlanInts = config1.find_objects_wo_child(
        r"^interface Vlan", r"^ ip address")
    for vlan in VlanInts:
        config2.append_line(vlan.text)
        for child in vlan.children:
            config2.append_line(child.text)
        config2.append_line('!')
    config2.commit()
    # Need to extract the management vlan number to add to the tacacs
    # interface on 4506 switches
    # We should probably create our own append function to add items we want
    # to NewConfig
    ManagementVlan = config1.find_objects_w_child(
        r"^interface Vlan", r"^ ip address")
    # print(ManagementVlan)
    config2.append_line("!")
    config2.append_line(ManagementVlan[0].text)
    if 'n' in raw_input(
            'Will this equipment use the same IP address? [Y|n]: ').lower():
        NewIP = raw_input('Enter new IP address: ')
        NewGateway = raw_input('Enter new Gateway: ')
        NewMask = raw_input('Enter new subnet Mask: ')
        config2.append_line(' ip address ' + NewIP + ' ' + NewMask)
        config2.append_line('!')
        config2.append_line('ip default-gateway ' + NewGateway)
        config2.append_line('!')
    else:
        for child in ManagementVlan[0].children:
            config2.append_line(child.text)
        config2.append_line('!')
        DefaultGateway = config1.find_objects(r'^ip default-gateway')
        config2.append_line("!")
        config2.append_line(DefaultGateway[0].text)
        config2.append_line("!")
    config2.commit()


def FileExport(outputfile, config2):
    config2.save_as('./output/' + outputfile)
    print("\nFile saved as", outputfile)


if __name__ == '__main__':
    directory = sorted([x for x in os.listdir('./configs/') if 'confg' in x])
    for item in enumerate(directory):
        print(' [' + str(item[0] + 1) + ']', item[1])
    name = None
    while not name in xrange(1, len(directory) + 1):
        name = int(raw_input('Please select the file number of the config: '))
    file = directory[name - 1]

    # switch_types = ['2960', '3560', '3650', '3750', '3850', '4506', 'Other']
    switch_types = ['3560', '3850', '4506', 'Other']
    print("Compatible switch models:")
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

    # should we extract a list from the config and present it?
    voicevlan = raw_input('Enter voice VLAN: ')
    # should we extract a list from the config and present it?
    SnoopingVLANs = raw_input(
        'List all VLANs for snooping, separated by commas: ')
    outputfile = raw_input('Enter output file name: ')

    # parse the config file argument and then extract the interfaces
    parse = CiscoConfParse('./configs/' + file, factory=True)
    # The new parser needs a file associated with it, so create a throwaway.
    # Trying to give it a legit file strangely invokes an error later on...
    NewConfig = CiscoConfParse(os.tmpfile(), factory=True)

    # read the csv argument and save as a list that defines the port mapping
    # with open('./configs/' + csvFile, 'rb') as f:
    #     reader = csv.reader(f)
    #     IntChanges = list(reader)

    NewConfig.append_line('!')
    NewConfig.append_line('hostname ' + hostname)
    NewConfig.append_line('!')
    NewConfig.commit()

    VlanExtract(parse, NewConfig)
    migrate_ports(parse, NewConfig, hostname)
    InterfacesForReview(NewConfig)
    AddVoiceVlan(NewConfig)
    TrunkCleanUp(NewConfig)
    RemoveMDIXandDOT1Q(NewConfig)  # This must be run AFTER TrunkCleanUp()

    ExtractManagement(parse, NewConfig)
    NewConfig.append_line('!')
    with open('./templates/' + baseconfig, 'r') as b:
        for line in b:
            NewConfig.append_line(line.rstrip())
    NewConfig.commit()
    FileExport(outputfile, NewConfig)
