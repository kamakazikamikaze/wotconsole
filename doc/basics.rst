Getting started with the awesome configuration generator
========================================================

Installation and Preparation
----------------------------

Before you begin, a few packages are necessary to download and install. You can do this via ``pip`` for easy installation. You can simply type ``pip install -r requirements.txt`` (or ``pip install -r dev-requirements.txt`` if you plan on contributing).

Dependencies
^^^^^^^^^^^^

.. include:: ../requirements.txt
   :literal:

Developer Dependencies
^^^^^^^^^^^^^^^^^^^^^^

.. include:: ../dev-requirements.txt
   :literal:

Directory Structure
-------------------

In order to run the script, several folders need to
be created::

   configconverter
   |\_ configs
   |\_ cutsheets
   \\_ output
    \_ templates

Invoking the module from CLI
----------------------------

The module includes an ``if __name__ == '__main__':`` statement so it can be
called from the directory itself. You may copy it directly, but we've included
it here (with the ``import``) for convenience::

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
     # Add ip dhcp snooping later! Adding it immediately after interfaces
     # causes a bug if trying to use file as startup-config
     vlans = vlan_extract(oldconfig, newconfig, feed_ports_regex[
         switch_models[switch_type]], createconfig)
     setup_feeds(newconfig, switch_type, blades, vlans)
     interfaces_for_review(newconfig, nojacks, newjacks)
     set_voice_vlan(oldconfig)
     access_cleanup(newconfig)
     trunk_cleanup(newconfig)
 
     # This must be run AFTER trunk_cleanup()
     if not switch_models[switch_type] == "3560":
         remove_mdix_and_dot1q(newconfig)
     if createconfig:
         baseconfig = ".txt"
         if (switch_type == len(switch_models) - 1):
             baseconfig = "baseconfig.txt"
         else:
             baseconfig = switch_models[switch_type] + "base.txt"
         newconfig.prepend_line("!")
         newconfig.prepend_line("hostname " + hostname)
         newconfig.prepend_line("!")
         newconfig.commit()
         extract_management(oldconfig, newconfig)
         add_snooping(newconfig, vlans)
         newconfig.append_line("!")
         with open(template_dir + baseconfig, "r") as b:
             for line in b:
                 newconfig.append_line(line.rstrip())
         newconfig.commit()
 
     file_export(outputfile, newconfig)

.. note:: You are still responsible for including the module directory in the
          search path