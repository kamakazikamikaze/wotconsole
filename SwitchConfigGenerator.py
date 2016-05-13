#!/bin/env python
from __future__ import print_function
import os
import openpyxl
from ciscoconfparse import CiscoConfParse
import warnings
import re

try:  # Portability for Python 3, though 2to3 would convert it
    input = raw_input
    xrange = range
except NameError:
    pass

# Should specific models require different configuration, explicitly state
# them here

feed_ports_regex = {
    "3560": r"Gi?0/11|Gi?0/12",
    "3750": r"Gi?[1-7]/0/[1-4]",
    "3850": r"Te?[1-7]/1/[1-4]|Gi[1-7]/1/[1-4]",  # Gig OR TenGig
    "4506": r"Te?[1-6]/[1-2]|Gi?[1-6]/[3-6]"
}

switch_models = ["3560", "3750", "3850", "4506", "Other"]

cutsheet_dir = "./cutsheets/"

config_dir = "./configs/"

output_dir = "./output/"

template_dir = "./templates/"


def condensify_ports(ports):
    # TODO: Accept range of ports and convert to human-readable range
    pass


def vlan_extract(oldconfig, newconfig, fullconfig=True):
    vlans = []
    lines = []  # We need to modify the snooping command without calling commit so soon
    AllVlanObjects = oldconfig.find_objects_w_child(r"^vlan", r"^ name")
    if not fullconfig:
        for obj in AllVlanObjects:
            vlans.append(obj.text.split()[-1])
    else:
        lines.append("!")
        lines.append("!")
        lines.append("ip dhcp snooping vlan ")
        lines.append("no ip dhcp snooping information option")
        lines.append("ip dhcp snooping")
        lines.append("vlan internal allocation policy ascending")
        for obj in AllVlanObjects:
            lines.append("!")
            lines.append(obj.text)
            vlans.append(obj.text.split()[-1])
            for child in obj.children:
                lines.append(child.text)
        lines[2] += ",".join(vlans)
        for line in lines:
            newconfig.append_line(line)
        newconfig.commit()
    return vlans


def migrate_ports(oldconfig, newconfig, hostname):
    hostnotfound = True
    warnings.simplefilter("ignore")
    # Supervisor blade is not added to spreadsheets
    blades = set()
    nojacks = []
    newjacks = []
    filtered_files = [x for x in os.listdir(
        cutsheet_dir) if (x.split()[0].split("-")[0] in hostname)]
    if len(filtered_files) == 0:
        raise Exception("No cutsheets found!")
    jacks = {}
    for file in [x for x in filtered_files if (
            "as-is" in x.lower() or "as is" in x.lower())]:
        wb = openpyxl.load_workbook(cutsheet_dir + file)
        for ws in wb:
            for row in ws.rows[1:]:
                for cell in row:
                    # CiscoConfParse cannot accept leading 0"s in port names,
                    # ex. Fa1/0/01. While this is a localized issue of using
                    # Excel"s autofill, we"ll add the courtesy of dropping it
                    # from the port (not module) number ourselves
                    try:
                        portname = row[0].value
                        indices = [m.span()
                                   for m in re.finditer(r"\d+", portname)]
                        portname = portname[0:indices[0][
                            0]] + "/".join([str(int(portname[num[0]:num[1]])) for num in indices])
                        jacks[int(cell.value)] = {
                            "old port": portname,
                            "old switch": ws.title
                        }
                    # except Exception as e:
                        # print(e)
                    except:
                        continue
    for file in [x for x in filtered_files if (
            "to-be" in x.lower() or "to be" in x.lower())]:
        wb = openpyxl.load_workbook(cutsheet_dir + file)
        for ws in wb:
            if not hostname.lower() in ws["A1"].value.lower():
                continue  # This isn"t a worksheet for the switch
            hostnotfound = False
            for row in ws.rows[3:]:
                portname = row[0].value
                indices = [m.span() for m in re.finditer(r"\d+", portname)]
                portname = portname[0:indices[0][
                    0]] + "/".join([str(int(portname[num[0]:num[1]])) for num in indices])
                # This grabs the blade number. re.finditer will look for all digits
                # and will be stored in 'm'. m.span will give the index numbers for
                # where the match starts (inclusive) and where it ends (exclusive),
                # and returns them as tuples. Since the blade is the first number,
                # we want the first match. We then get the first number from that
                # tuple since it's the index number of the string. You may be asking,
                # "wait, aren't the cutsheets configured to only use the first letter
                # of the port type, e.g. 'F|G|T'?" Yes, that's how it is currently,
                # but since the cutsheet generator was designed by a student and
                # edited by students, I have this unwarranted fear of someone changing
                # 'T' to 'Te', etc. after I am long gone and this is still in use
                blades.add(
                    int(portname[
                        [m.span() for m in re.finditer(r"\d", portname)][0][0]
                    ])
                )
                transferred = False
                for cell in row:
                    try:
                        port = oldconfig.find_interface_objects(
                            jacks[int(cell.value)]["old port"])
                        newconfig.append_line("!")
                        newconfig.append_line("interface " + portname)
                        for child in port[0].children:
                            newconfig.append_line(child.text)
                        transferred = True
                        break  # Got the jack, move to next row
                    except (ValueError, TypeError):  # Failures for int() cast
                        continue  # Try next cell
                    except KeyError:
                        # We have a valid jack number but it"s new
                        nojacks.append(portname)
                        # print(
                        #     "Port",
                        #     portname,
                        #     "is connected to a new jack. Please configure this manually.")
                        newconfig.append_line("!")
                        newconfig.append_line("interface " + portname)
                        newconfig.append_line(" %%NEW CONNECTION%%")
                        transferred = True
                        break
                if not transferred:
                    newjacks.append(portname)
                    # print(
                    #     "Port",
                    #     portname,
                    #     "is not connected to a jack and will be shutdown. Please confirm this manually")
                    newconfig.append_line("!")
                    newconfig.append_line("interface " + portname)
                    newconfig.append_line(" shutdown")
    if hostnotfound:
        raise Exception("No 'To Be' cutsheet found! Exiting...")
    newconfig.commit()
    return blades, nojacks, newjacks


# search interfaces for non-standard configs that will need to be reviewed
# individually
def interfaces_for_review(newconfig):
    PowerInts = newconfig.find_objects_w_child(r"^interf", r"^ power")
    # print PowerInts
    if PowerInts:
        print("\nManually review the following Interfaces for Power settings")
        for obj in PowerInts:
            print(" ", obj.text)
    DuplexInts = newconfig.find_objects_w_child(r"^interf", r"^ duplex")
    if DuplexInts:
        print("\nManually review the following Interfaces for Duplex settings")
        for obj in DuplexInts:
            print(" ", obj.text)
    SpeedInts = newconfig.find_objects_w_child(r"^interf", r"^ speed")
    if SpeedInts:
        print("\nManually review the following Interfaces for Speed settings")
        for obj in SpeedInts:
            print(" ", obj.text)
    PurgatoryInts = newconfig.find_objects_wo_child(
        r"^interf", r"^ switchport mode")
    PurgatoryInts = [obj for obj in PurgatoryInts if not obj.re_search_children(
        r"^[\s]?shut(down)?$")]
    if PurgatoryInts:
        print("\nThese interfaces did not specify Access or Trunk mode.\nManually review the following:")
        for obj in PurgatoryInts:
            print(" ", obj.text)
    print("")


# Find the first child object containing switchport voice vlan matching
# the voice vlan in config, and adding that child to any access ports
# without a voice vlan
def add_voice_vlan(voicevlan, newconfig):
    Modified = []
    Voice = " switchport voice vlan " + voicevlan
    NewIntfs = newconfig.find_objects_wo_child(
        r"^interf", r"^ switchport mode trunk")
    for obj in NewIntfs:
        if obj.access_vlan != 0:  # testing to see if access port, should probably adjust to search for switchport mode access, but some ports have this explicit and some don"t
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
            print(" ", each)
    newconfig.commit()


# On trunk ports, remove access/voice vlan configs, spanning-tree
# portfast, and no snmp trap link-status
def trunk_cleanup(newconfig):
    TrunkInts = newconfig.find_objects_w_child(
        r"^interf", r"^ switchport mode trunk|shutdown")
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
    newconfig.commit()
    # Now we want to remove from trunk ports VLANs 1,1002,1003,1004,1005
    # I am thinking we can detect any ports with these VLANs trunked, extract
    # all VLANs, delete the child object, remove the unwanted VLANS, then
    # append a new child
    TrunkInts = newconfig.find_objects_w_child(
        r"^interf", r"^ switchport mode trunk")
    for obj in TrunkInts:
        TrunkLines = obj.re_search_children(r"switchport trunk allowed vlan")
        # obj.delete_children_matching(r"switchport trunk allowed vlan")
        for child in TrunkLines:
            # TrunkVlans = []
            Add = False
            if "add" in child.text.lower():
                Add = True
            TrunkNumbers = set(child.text.split()[-1].split(","))
            NumsToRemove = set(
                ["1", "1002-1005", "1002", "1003", "1004", "1005"])
            TrunkNumbers = list(TrunkNumbers - NumsToRemove)
            if len(TrunkNumbers) > 0:
                if Add:
                    TrunkConfigLine = " switchport trunk allowed vlan add " + \
                        ",".join(TrunkNumbers)
                    obj.replace(
                        r"^ switchport trunk allowed vlan add ",
                        TrunkConfigLine)
                else:
                    TrunkConfigLine = " switchport trunk allowed vlan " + \
                        ",".join(TrunkNumbers)
                    obj.replace(
                        r"^ (?!add)(switchport trunk allowed vlan )",
                        TrunkConfigLine)
                # obj.append_to_family(TrunkConfigLine)
    newconfig.commit()


# search interfaces for non-standard configs that will need to be reviewed
# individually.  This must be run AFTER trunk_cleanup()
def remove_mdix_and_dot1q(newconfig):
    MdixInts = newconfig.find_objects("no\smdix\sauto")
    for obj in MdixInts:
        if obj != []:
            obj.delete()
    newconfig.commit()
    Dot1qInts = newconfig.find_objects(
        "switchport\strunk\sencapsulation\sdot1q")
    for obj in Dot1qInts:
        if obj != []:
            obj.delete()
    newconfig.commit()


# on access ports, remove native and trunk vlans
def access_cleanup(newconfig):
    AccessInts = newconfig.find_objects_w_child(
        r"^interf", r"^ switchport mode access")
    for obj in AccessInts:
        for child in obj.children:
            if r"switchport trunk" in child.text:
                child.delete()
    newconfig.commit()
    # I found that some configs are missing the "mode access", so I am also
    # applying to any that are missing "switchport mode"
    AccessInts = newconfig.find_objects_wo_child(
        r"^interf", r"^ switchport mode")
    for obj in AccessInts:
        for child in obj.children:
            if r"switchport trunk" in child.text:
                child.delete()
    newconfig.commit()


# extract management vlan and IP address, assuming layer 2 switch with only VLAN1 and management VLAN
# this needs to be edited to just extract the IP, and use the standard
# configuration for the rest of management VLAN
def extract_management(oldconfig, newconfig):
    Vlan1 = oldconfig.find_objects(r"^interface Vlan1$")
    for vlan in Vlan1:
        vlan.delete()
    oldconfig.commit()
    VlanInts = oldconfig.find_objects_wo_child(
        r"^interface Vlan", r"^ ip address")
    for vlan in VlanInts:
        newconfig.append_line(vlan.text)
        for child in vlan.children:
            newconfig.append_line(child.text)
        newconfig.append_line("!")
    newconfig.commit()
    # Need to extract the management vlan number to add to the tacacs
    # interface on 4506 switches
    # We should probably create our own append function to add items we want
    # to newconfig
    ManagementVlan = oldconfig.find_objects_w_child(
        r"^interface Vlan", r"^ ip address")
    # print(ManagementVlan)
    newconfig.append_line("!")
    newconfig.append_line(ManagementVlan[0].text)
    if "n" in input(
            "Will this equipment use the same IP address?[Y|n]: ").lower():
        NewIP = input("Enter new IP address: ")
        NewGateway = input("Enter new Gateway: ")
        NewMask = input("Enter new subnet Mask: ")
        newconfig.append_line(" ip address " + NewIP + " " + NewMask)
        newconfig.append_line(" no ip route-cache")
        newconfig.append_line(" no ip mroute-cache")
        newconfig.append_line("!")
        newconfig.append_line("ip default-gateway " + NewGateway)
        newconfig.append_line("!")
    else:
        for child in ManagementVlan[0].children:
            newconfig.append_line(child.text)
        newconfig.append_line("!")
        DefaultGateway = oldconfig.find_objects(r"^ip default-gateway")
        newconfig.append_line("!")
        newconfig.append_line(DefaultGateway[0].text)
        newconfig.append_line("!")
    # Only the 4506 uses the following line, but it will be ignored on other
    # devices anyways, so we"ll just leave it here
    newconfig.append_line("ip tacacs source-interface " +
                          ManagementVlan[0].text.split()[-1])
    newconfig.commit()


def file_export(outputfile, newconfig):
    newconfig.save_as(output_dir + outputfile)
    print("\nFile saved as", outputfile)


def setup_feeds(newconfig, switch_type, blades, vlans):
    if "y" in input(
            "\nWould you like to set up feedports?[y|N]: ").lower():
        try:
            finished = False
            print("When you are finished, type 'no' for the feedport name")
            print("(Use 'T' or 'G' instead of 'Ten' or 'Gig'!)")
            while not finished:
                feedport = input("Feedport name: ").upper()
                if not feedport.lower() == "no":
                    blade = int(feedport[
                        [m.span() for m in re.finditer(r"\d", feedport)][0][0]
                    ])
                    if re.search(feed_ports_regex[switch_models[switch_type]], feedport) and (
                            blade in blades):
                        exists = newconfig.find_objects(
                            r"^interface " + feedport.strip())
                        if len(exists) > 1:
                            print("Uh, your interface matches several others:")
                            for each in exists:
                                print(" ", each.text)
                            print("Abandoning changes...")
                        elif len(exists) == 1:
                            existing = exists[0]
                            print("Interface already exists!")
                            print(existing.text)
                            for line in existing.children:
                                print(line.text)
                            if "y" in input("Overwrite?[y|N]: ").lower():
                                for child in existing.children:
                                    child.delete()
                                newconfig.commit()
                                setup_feed(newconfig, feedport)
                        else:
                            setup_feed(newconfig, feedport)
                    else:
                        print(
                            "That is an invalid port. Either the spelling is wrong or the numbering is out of range!")
                else:
                    finished = True
        except Exception as e:
            print("Exception:", e)


def setup_feed(newconfig, feedport):
    existing = newconfig.find_objects(r"^interface " + feedport.strip())
    if existing:
        exists = existing[0]
        if "y" in input("Would you like to add a description?[y|N]: ").lower():
            exists.append_to_family(" description " + input("Description: "))
        if switch_models[switch_type] == "3560":
            exists.append_to_family(" switchport trunk encapsultion dot1q")
        exists.append_to_family(" switchport mode trunk")
        exists.append_to_family(
            " switchport trunk allowed vlan " +
            ",".join(vlans))
        exists.append_to_family(" ip dhcp snooping trust")
    else:
        newconfig.insert_before(
            r"ip dhcp snooping vlan",
            "interface " + feedport)
        if "y" in input("Would you like to add a description?[y|N]: ").lower():
            newconfig.insert_before(
                r"ip dhcp snooping vlan",
                " description " +
                input("Description: "))
        if switch_models[switch_type] == "3560":
            newconfig.insert_before(
                r"ip dhcp snooping vlan",
                " switchport trunk encapsultion dot1q")
        newconfig.insert_before(
            r"ip dhcp snooping vlan",
            " switchport mode trunk")
        newconfig.insert_before(r"ip dhcp snooping vlan",
                                " switchport trunk allowed vlan " +
                                ",".join(vlans))
        newconfig.insert_before(
            r"ip dhcp snooping vlan",
            " ip dhcp snooping trust")
        newconfig.insert_before(r"ip dhcp snooping vlan", "!")
    newconfig.commit()


if __name__ == "__main__":
    directory = sorted([x for x in os.listdir(config_dir) if "confg" in x])
    for item in enumerate(directory):
        print(" [" + str(item[0] + 1) + "]", item[1])
    name = None
    while not name in xrange(1, len(directory) + 1):
        name = int(
            input("Please select the file number of the old config: "))
    file = directory[name - 1]

    print("Compatible switch models:")
    for switch in enumerate(switch_models):
        print(" [" + str(switch[0] + 1) + "]", switch[1])
    switch_type = None
    while not switch_type in xrange(1, len(switch_models) + 1):
        switch_type = int(
            input("What switch model are you programming? ")) - 1

    hostname = ""
    while len(hostname) == 0:
        hostname = input("Enter hostname of new switch: ").upper()

    outputfile = ""
    while len(outputfile) == 0:
        outputfile = input("Enter output file name: ")

    oldconfig = CiscoConfParse(config_dir + file, factory=True)
    # The new parser needs a file associated with it, so create a throwaway.
    # Trying to give it a legit file strangely invokes an error later on...
    newconfig = CiscoConfParse(os.tmpfile(), factory=True)

    createconfig = (not "n" in input(
        "Generate full config file?[Y|n]: ").lower())
    if createconfig:
        baseconfig = ".txt"
        if (switch_type == len(switch_models) - 1):
            baseconfig = "baseconfig.txt"
        else:
            baseconfig = switch_models[switch_type] + "base.txt"

        newconfig.append_line("!")
        newconfig.append_line("hostname " + hostname)
        newconfig.append_line("!")
        newconfig.commit()

    blades, nojacks, newjacks = migrate_ports(
        oldconfig, newconfig, hostname)
    if switch_models[switch_type] == "4506":
        blades = set(xrange(0, 7))  # Blades CAN be left empty, so there's that
    vlans = vlan_extract(oldconfig, newconfig, createconfig)
    setup_feeds(newconfig, switch_type, blades, vlans)
    print("Available voice VLANs:")
    vv = oldconfig.find_objects(r"^vlan 1\d\d$")
    # vv = [v for v in vlans if v[0] == "1" and len(v) == 3]
    skipvoice = False
    if len(vv) > 1:
        voicevlan = ""
        while len(voicevlan) == 0:
            for v, num in zip(vv, xrange(1, len(vv) + 1)):
                print(" [" + str(num) + "]", v.text.split()
                      [-1], "-", v.children[0].text.split()[1:])
            print(" [0] Skip")
            voicevlan = input("    Enter voice VLAN: ")
            try:
                if int(voicevlan) == 0:
                    skipvoice = True
                    break
                else:
                    voicevlan = vv[int(voicevlan) - 1].text.split()[-1]
            except:
                voicevlan = ""
    elif len(vv) == 1:
        if "n" in input("Only one voice VLAN found: " + vv[0].text.split(
        )[-1] + " - " + str(vv[0].children[0].text.split()[1:]) + ". Use this?[Y|n]: ").lower():
            skipvoice = True
        else:
            voicevlan = vv[0].text.split()[-1]
    else:
        print("No standard voice VLAN detected.")

    if createconfig:
        interfaces_for_review(newconfig)
    if not skipvoice:
        add_voice_vlan(voicevlan, newconfig)

    trunk_cleanup(newconfig)
    # This must be run AFTER trunk_cleanup()
    if not switch_models[switch_type] == "3560":
        remove_mdix_and_dot1q(newconfig)

    if createconfig:
        extract_management(oldconfig, newconfig)
        newconfig.append_line("!")
        with open(template_dir + baseconfig, "r") as b:
            for line in b:
                newconfig.append_line(line.rstrip())
        newconfig.commit()

    file_export(outputfile, newconfig)
