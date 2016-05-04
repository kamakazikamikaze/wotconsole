#!/bin/env python
from __future__ import print_function
import os
import csv
from ciscoconfparse import CiscoConfParse


def VlanExtract(config1, config2):
    AllVlanObjects = config1.find_objects_w_child(r'^vlan', r'^ name')
    for obj in AllVlanObjects:
        config2.append_line("!\n" + obj.text)
        for child in obj.children:
            config2.append_line(child.text)
    config2.commit()


# work through the list of port changes, print new interface config to
# screen, and change all ports in intfs
def PortChange(config1, config2, csv):
    for i, j in csv:
        # print "Old Port: " + i +"\nNew Port: " +j
        if j != "":
            port = config1.find_interface_objects(i)
            # print "!"
            # print "interface ",j
            # for child in port[0].children:
            # print child.text
            intname = port[0].name
            port[0].replace(intname, j)
            # We should probably create our own append function to add items we
            # want to NewConfig
            config2.append_line("!")
            config2.append_line(port[0].text)
            for child in port[0].children:
                config2.append_line(child.text)
            config2.commit()


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
            # For Carlos: a Set is a collection that only allows unique values.
            #   Unlike List, two Sets can be subtracted from each other to obtain
            #   their 'difference'. This makes it faster and easier to prune
            #   values instead of having to loop over every one of them. At the
            #   end we can convert it back to a list so `.join()` can be used.
            NumsToRemove = set(
                ['1', '1002-1005', '1002', '1003', '1004', '1005'])
            # for i in NumsToRemove:
            #     if i in TrunkNumbers:
            #         TrunkNumbers.remove(i)
            # for i in TrunkNumbers:
            #     TrunkVlans.append(i)
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
    VlanInts = config1.find_objects_wo_child(
        r"^interface Vlan", r"^ ip address")
    for vlan in VlanInts:
        for child in vlan.children:
            config2.append_line(child.text)
        config2.append_line('!')

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


def FileExport(config2):
    config2.save_as(outputfile)
    print("\nFile saved as", outputfile)


if __name__ == '__main__':
    """
    #define input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('file', metavar = 'FILENAME', help = 'Name of cisco config file')
    parser.add_argument('csv', metavar = 'FILENAME', help = 'csv file of old port to new port.  file descriptions should be cisco legible, with all leading zeros removed')
    parser.add_argument('voicevlan', metavar = 'TEXT', help = 'voice vlan to be assigned to any access ports that don\'t have a voice vlan')
    parser.add_argument('outputfile', metavar = 'FILENAME', help = 'Name of output filename')
    args = parser.parse_args()
    """
    directory = sorted([x for x in os.listdir('./configs/') if 'confg' in x])
    for item in enumerate(directory):
        print(' [' + str(item[0] + 1) + ']', item[1])
    name = None
    while not name in xrange(1, len(directory) + 1):
        name = int(raw_input('Please select the file number of the config: '))
    file = directory[name - 1]

    switch_types = ['2960', '3560', '3650', '3750', '3850', '4506', 'Other']
    print("Compatible switch models:")
    for switch in enumerate(switch_types):
        print(' [' + str(switch[0] + 1) + ']', switch[1])
    SwitchType = None
    while not SwitchType in xrange(1, len(switch_types) + 1):
        SwitchType = int(
            raw_input('What switch model are you programming? ')) - 1

    hostname = raw_input('Enter hostname of new switch: ')
    # perhaps extract options again?
    directory = sorted([x for x in os.listdir(
        './configs/') if ('.csv' in x or '.xls' in x)])
    for item in enumerate(directory):
        print(' [' + str(item[0] + 1) + ']', item[1])
    name = None
    while not name in xrange(1, len(directory) + 1):
        name = int(raw_input('Please select the CSV file of port changes: '))
    csvFile = directory[name - 1]

    # should we extract a list from the config and present it?
    voicevlan = raw_input('Enter voice VLAN: ')
    # should we extract a list from the config and present it?
    SnoopingVLANs = raw_input(
        'List all VLANs for snooping, separated by commas: ')
    outputfile = raw_input('Enter output file name: ')

    # The CiscoConfParse package will append our lines at the end of the
    # config file, which is way after where the `end` directive (IOS `end`
    # command for CLI configuration) is located. This pretty much invalidates
    # our config file. We'll instead cut the config template in half, add our
    # lines, then re-join it into one file.
    if SwitchType == 6:
        baseconfig = 'baseconfig.txt'
    else:
        baseconfig = switch_types[SwitchType] + 'base.txt'
    with open('./templates/' + baseconfig, 'r') as b:
        with open('./output/temp.o', 'w') as t:
            for line in b:
                if not 'no ip http server' in line.lower():
                    t.write(line)
                else:
                    break

    # parse the config file argument and then extract the interfaces
    parse = CiscoConfParse('./configs/' + file, factory=True)
    NewConfig = CiscoConfParse('./output/temp.o', factory=True)

    # read the csv argument and save as a list that defines the port mapping
    with open(csvFile, 'rb') as f:
        reader = csv.reader(f)
        IntChanges = list(reader)

    NewConfig.append_line('!')
    NewConfig.append_line('hostname ' + hostname)
    NewConfig.append_line('!')
    VlanExtract(parse, NewConfig)
    PortChange(parse, NewConfig, IntChanges)
    InterfacesForReview(NewConfig)
    AddVoiceVlan(NewConfig)
    TrunkCleanUp(NewConfig)
    RemoveMDIXandDOT1Q(NewConfig)  # This must be run AFTER TrunkCleanUp()
    # Passes a boolean if we use the same IP
    ExtractManagement(parse, NewConfig)
    halfway = False
    with open(baseconfig, 'r') as b:
        for line in b:
            if 'no ip http server' in line.lower():
                NewConfig.append_line(line.rstrip())
                halfway = True
            elif halfway:
                NewConfig.append_line(line.rstrip())
    NewConfig.commit()
    FileExport('./output/' + NewConfig)
    os.remove('./output/temp.o')
