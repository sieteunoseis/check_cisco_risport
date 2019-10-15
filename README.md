# check_cisco_risport
check_cisco_risport is a Nagios plugin to monitor the registration status of Cisco Unified Communications Servers devices


file: check_cisco_risport.py
Version 0.1.1 (10.15.2019)

check_cisco_risport is a Nagios plugin made by Jeremy Worden (jeremy.worden at gmail dot come)
to monitor the registration status of Cisco Unified Communications Servers devices.

The plugin uses the Cisco RisPort SOAP Service via HTTPS to do a wide variety of checks.

This nagios plugin is free software, and comes with ABSOLUTELY NO WARRANTY.
It may be used, redistributed and/or modified under the terms of the GNU
General Public Licence (see http://www.fsf.org/licensing/licenses/gpl.txt).


# tested with: 	
		Cisco Unified Communications Manager CUCM version 12.0.1.23900-9

# see also:
 		Cisco Unified Communications Manager XML Developers Guide, Release 9.0(1)
 		https://www.cisco.com/c/en/us/td/docs/voice_ip_comm/cucm/devguide/9_1_1/xmldev-911.html

# changelog:
		Version 0.1.1 (10.15.2019) initial release
    
# Usage
  -H="": AXL server IP address
  -u="": AXL usernanme
  -p="": AXL password
  -d="": Device name that you want to check registration status of
  -w="": Warninig level (1 - Registered, 2 - UnRegistered, 3 - Rejected, 4 - PartiallyRegistered, 5 - Unknown, 6 - NotFound)
  -c="": Critical level
  
# example
	./check_cisco_risport.py -H 10.10.10.1 -u username -p password -d SEP112233445566 -w 2 -c 5
	
# notes
	For SIP Trunk Status:
	Registered = Full Service
	Unregistered = Partial Service
	Unknown = No Service

