This is an attempt at building a simple email classifier. The intent is to take in an email pitching either a cargo or a position, and attempt to idenitfy which region the said cargo or vessel is located in, by honing in to the most important lines of the chartering message, and looking for specific references to ports.

The classifier relies on two public sets of data.

A Google Sheets list of all the ports in the world (17k):
https://docs.google.com/spreadsheets/d/1APztiISS-I8m-KF9d3d6tEXvXu33rYF5yU8mRI7z_iE/edit#gid=0

And a Google Sheets list of all the Bulk Vessel names in the world (13k):
https://docs.google.com/spreadsheets/d/1yKPGZhV8XerSrifLVJBwLVej1mm0JWF4KnzUt-W5VQM/edit#gid=0


# Setting this up
This code relies on connecting to Google Sheets for key static data. In order to set this up, you need to create credentials for the Google API to programmatically read this data.

You can find a more indepth discussion here, but generally the steps involved are:
https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html

1. Go to the Google APIs Console.
2. Create a new project.
3. Click Enable API. Search for and enable the Google Drive API.
4. Create credentials for a Web Server to access Application Data.
5. Name the service account and grant it a Project Role of Editor.
6. Download the JSON file.
7. Copy the JSON file to your code directory and rename it to client_secret.json
8. Find the  client_email inside client_secret.json. Back in your spreadsheet, click the Share button in the top right, and paste the client email into the People field

You will then have to modify this file (line 34 and 64) to reference your key
```python
    # and an API key generates from the console, you will have to create your own integration key
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('YOUR_FILENAME_HERE', scope)
    gc = gspread.authorize(credentials)
```
Your code will now use this email account to authorize API access, and you will be able to connect to the two public spreadsheets and pull the list of 17k ports into a dataframe inside of your own code.

# Usage:
```python
import portid
#initialize the data
ports = portid.get_ports()
vessels = portid.get_vessels()

email_body = '' #load the string of text in the eml here

key_text = portid.clean_text(email_body, vessels)
p = portid.find_ports_in_text(ports, key_text)
print(p['Continents'])
```
