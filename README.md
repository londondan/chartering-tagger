This is an attempt at building a simple email classifier. The intent is to take in an email pitching either a cargo or a position, and attempt to idenitfy which region the said cargo or vessel is located in, by honing in to the most important lines of the chartering message, and looking for specific references to ports.

The classifier relies on two public sets of data.

A Google Sheets list of all the ports in the world (17k):
https://docs.google.com/spreadsheets/d/1APztiISS-I8m-KF9d3d6tEXvXu33rYF5yU8mRI7z_iE/edit#gid=0

And a Google Sheets list of all the Bulk Vessel names in the world (13k):
https://docs.google.com/spreadsheets/d/1yKPGZhV8XerSrifLVJBwLVej1mm0JWF4KnzUt-W5VQM/edit#gid=0


Usage:

import portid
#initialize the data
ports = portid.get_ports()
vessels = portid.get_vessels()

email_body = '' #load the string of text in the eml here

key_text = portid.clean_text(email_body, vessels)
p = portid.find_ports_in_text(ports, key_text)
print(p['Continents'])
