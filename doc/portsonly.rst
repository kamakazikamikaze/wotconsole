Just need port configuration? I gotchu
======================================

If the managed device is setup correctly but ports have had a shift in
configuration, you can generate just the list of ports so as to not risk
accidentally overriding any management settings. You will still have the
option to configure feeding ports too, if desired. The following snippet
would be sufficient::

 from configconverter import SwitchConfigGenerator

 if __name__ == "__main__":
     oldconfig, newconfig = get_configs()
     switch_type = get_switch_model()
     hostname = force_user_input("Enter hostname of new switch: ").upper()
     outputfile = input(
         "Enter output file name (default - " + hostname + ".txt): ")
     outputfile = outputfile if outputfile else hostname + ".txt"
     createconfig = ("n" not in input(
         "Generate full config file?[Y|n]: ").lower())
 
     blades, nojacks, newjacks = migrate_ports(
         oldconfig, newconfig, hostname, switch_type)
     # Add ip dhcp snooping later: adding it immediately after interfaces
     # causes a bug if trying to use file as startup-config
     vlans = vlan_extract(oldconfig, newconfig, feed_ports_regex[
         switch_models[switch_type]], createconfig)
     setup_feeds(newconfig, switch_type, blades, vlans)
     interfaces_for_review(newconfig, nojacks, newjacks)
     set_voice_vlan(oldconfig)
     access_cleanup(newconfig)
     trunk_cleanup(newconfig)
     file_export(outputfile, newconfig)
