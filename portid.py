import pandas as pd
import numpy as np
import gspread
import re
from oauth2client.service_account import ServiceAccountCredentials
from df2gspread import df2gspread as d2g


# there are a few ports which have super common names, like Date in Japan or On in Sweden
# it's too hard to try to match on these, so we just exclude them from the results
excluded_words = ['date', 'on', 'div', 're', 'best', 'soya','hull', 'mipo', 'se', 'anchorage', 'clare', 'gypsum', 'ada', 'ha', 'ii', 'stow','usa']

#this function takes an array of words, and then create an n-gram of the text
# e.g. ['a', 'b', 'c', 'd'] with n=3 => ['a b c', 'b c d']
#
# this is useful when trying to mtach port names with multiple words such as 'Phu My'
def ngrams(input, n):
    output = []
    for i in range(len(input)-n+1):
        txt = ''
        for j in range(n):
            txt = txt + ' ' + input[i+j]
        output.append(txt.strip())
    return output

def get_vessels():
    print("getting master list of vessels")
    #the key to the public list of vessel names found here:
    # https://docs.google.com/spreadsheets/d/1yKPGZhV8XerSrifLVJBwLVej1mm0JWF4KnzUt-W5VQM/edit#gid=0
    spreadsheet_key = '1yKPGZhV8XerSrifLVJBwLVej1mm0JWF4KnzUt-W5VQM'

    # and an API key generates from the console, you will have to create your own integration key
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('./dashboard_integration-914ab230c5a4.json', scope)
    gc = gspread.authorize(credentials)

    #now let's download the list of ports from our public spreadsheet
    book = gc.open_by_key(spreadsheet_key)
    wks_name = 'Bulk'
    worksheet = book.worksheet(wks_name)
    table = worksheet.get_all_values()
    data = pd.DataFrame(table[1:], columns=table[0])

    print ("Vessel name list downloaded")
    data['name'] = 'MV ' + data['name'].astype(str)
    data['name']=data["name"].str.lower()

    #finally we sort the list from longet name to shortest (which helps when we are doing some finds)
    s = data['name'].str.len().sort_values(ascending=False).index
    data = data.reindex(s)
    data = data.reset_index(drop=True)

    print(data.head(3))
    return data

def get_ports():
    print("Getting the master list of ports...")
    #the key to the public Ports spreadsheet found here:
    # https://docs.google.com/spreadsheets/d/1APztiISS-I8m-KF9d3d6tEXvXu33rYF5yU8mRI7z_iE
    spreadsheet_key = '1APztiISS-I8m-KF9d3d6tEXvXu33rYF5yU8mRI7z_iE'

    # and an API key generates from the console, you will have to create your own integration key
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('./dashboard_integration-914ab230c5a4.json', scope)
    gc = gspread.authorize(credentials)
    
    #now let's download the list of ports from our public spreadsheet

    book = gc.open_by_key(spreadsheet_key)
    wks_name = 'Global Ports'
    worksheet = book.worksheet(wks_name)
    table = worksheet.get_all_values()

    data = pd.DataFrame(table[1:], columns=table[0])
    
    print("ports downloaded")
    
    # now we clean ports
    data['latin_port_name']=data["latin_port_name"].str.lower()
    # in this case we have found the best matches by 
    # removings things after commas, parentheses and slashes - the content of which
    # afterwards is rarely in shipping emails
    #
    # e.g. Banjuwangi, Java
    #
    # we could clean this up in the source data itself, but it's low computation cost to
    # do so here, and it ensures we can quickly modify this for different experiments 
    # without breaking our source data

    #now we need to create some dupes, minus 'al ' and 'ad ' and ' Island', etc.

    for index, row in data.iterrows():
        cleaned = row['latin_port_name'].split(',',1)
        cleaned = cleaned[0].split('(',1)
        cleaned = cleaned[0].split('/',1)
        cleaned = cleaned[0].replace(' pt','')
        cleaned = cleaned.replace('.','')
        row['latin_port_name'] = cleaned.strip()
    print(data.head(3))

    return data
    
# this function looks at email text line by line and tries to narrow in on meaningful lines
# that help idenitfy the region. For example, we don't want to locate the data on where the 
# vessel was built or where it is flagged, even though those may be real ports
def clean_text(text, vessels):
    text = text.lower()
    text = text.replace('\'','')
    text= text.replace('\"','')
    verbose = True
    #first we find and remove vessel names
    for vessel in vessels['name']:
        if (verbose and (text.find(vessel)>-1)):
            print("found vessel: "+vessel)
        text = text.replace(vessel, 'vesselname')
    
    #next we look for key lines
    text = text.splitlines()
    
    #positive terms help find meaningful rows
    key_terms = ['mv', 'open', 'port', 'tct', ' pol', 'loadport', 'lport', 'dely', 
                 'pref', 'vesselname', 'from', ' / ']

    # negative terms then clear out rows that may include a positive filter, but are clearly not what we are looking for
    neg_terms = ['http', 'mobile:', 'flag', 'direct:', ' | ', 'from:', 
                 'dischport', 'all figures stated', 'built', 'registry', 'panama net', 
                 ' * ', 'unsubscribe', 'home', 'sulphur']
    
    # this helps us find dates in a row - often a signifier that the line talkes about a vessel's availability
    regex = ['[\s][0-9]{2}[-|/|~][0-9]{2}', '[0-9]{2}(th|st|nd)','[0-9]{2}[\s]*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)']
    
    best = ['']
    
    # we don't want to capture lines with flags in them, or build locations
    # those will give us false positives
    
    #need to copy the ports and take out the 'Ad ' and 'Al '
    #e.g. Dummam
    
    #so let's cut the text down to lines that we thinkare most likely to have the load port
    for line in text:
        
        #first we look for lines that have key words like 'open' or 'loadport'
        for term in key_terms:
            clean = line.lower()
            clean = clean.replace('.','')
            if term in clean[0:100]:
                if 'http' not in clean:
                    best.append(line[0:100])
                    if (verbose):
                        print("adding line: "+line[0:100]+" because "+term)
        
        #need to get rid of phone numbers
        
        # now we look for lines that have availability dates '11-12 JUNE'
        for term in regex:
            if re.search(term, line[0:100]):
                best.append(line[0:100])
                if (verbose):
                    print("adding line: "+line[0:100]+ ' because '+term)
    
    print('[----------]')
    final=[]
    #finally we get rid of all the bad lines
    for row in best:
        keep = True
        for term in neg_terms:
            if term in row:
                keep = False
                if (verbose):
                    print("removing line: "+row+" : because "+term)
        if (keep):
            final.append(row)
    
    output = '\n'.join(final)
    return output


def find_ports_in_text (ports, text):
    data = ports
    #print("searching ports of the text")
    
    # to make matching easier, we want to ignore case. We lowercased the port
    # names above when we cleaned the data.
    # here we do the same thing to the input text from the customer
    text = text.lower()

    #more text cleaning to go here
    # - can we get rid of lines with flags? a common problem is vessel is flagged for Sinagpore, but located somewhere else yet Singapore stil appears
    
    # now we create a dictionary of "words" within the our source text
    # first we split the text by punctuation, and then we create 2/3 grams of the text
    # and we add it all together into a single corpus of potential locations

    split_text = re.findall(r"[\w']+|[<>.,!?;/]", text)
    gram2 = ngrams(split_text,2)
    gram3 = ngrams(split_text,3)

    new_text = split_text+gram2+gram3
    #print(new_text[:3])
    
    filter1 = data["latin_port_name"].isin(new_text) 
    pass1 = ports[filter1]
    #print(pass1)
    
    # using the '~' symbole gives us an inverse match, returns all the rows where 
    # the values are not found (anyhting that passes our filter)
    filter_out = ~pass1['latin_port_name'].isin(excluded_words)

    pass2 = pass1[filter_out]
    return pass2

def id_ports(text):
    matches = find_ports_in_text(ports, text)
    return matches.to_json()