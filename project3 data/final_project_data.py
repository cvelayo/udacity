#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json

# Regular expressions
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

# Function to shape the elemtent to fit the requirements
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        temp = {}
        ndlist = []
        if element.tag == 'node':
            temp['type'] = 'node'
            children = list(element)
            for key in element.attrib.keys():
                temp[key] = element.attrib[key]
            if len(children) > 0:
                for item in list(element):
                    if item.attrib['k'] =='addr:housenumber':
                        temp2 = temp.get('address',{})
                        temp2['housenumber'] = item.attrib['v']
                        temp['address'] = temp2
                    elif item.attrib['k'] =='addr:street':
                        temp2 = temp.get('address',{})
                        temp2['street'] = audit_street_type(item.attrib['v'].strip())
                        temp['address'] = temp2
                    elif item.attrib['k'] =='addr:postcode':
                        post_audit = clean_post(item.attrib['v'])
                        if post_audit:
                            temp2 = temp.get('address',{})
                            temp2['postcode'] = post_audit
                            temp['address'] = temp2
                    elif not item.attrib['k'].startswith('addr'):
                        temp[item.attrib['k']] = item.attrib['v']
        if element.tag == 'way':
            temp['type'] = 'way'
            children = list(element)
            for key in element.attrib.keys():
                temp[key] = element.attrib[key]
            if len(children) > 0:
                for item in list(element):
                    if 'k' in item.attrib:
                        if item.attrib['k'] =='addr:housenumber':
                            temp2 = temp.get('address',{})
                            temp2['housenumber'] = item.attrib['v']
                            temp['address'] = temp2
                        elif item.attrib['k'] =='addr:street':
                            temp2 = temp.get('address',{})
                            temp2['street'] = audit_street_type(item.attrib['v'].strip())
                            temp['address'] = temp2
                        elif item.attrib['k'] =='addr:postcode':
                            post_audit = clean_post(item.attrib['v'])
                            if post_audit:
                                temp2 = temp.get('address',{})
                                temp2['postcode'] = post_audit
                                temp['address'] = temp2

                        elif not item.attrib['k'].startswith('addr'):
                            temp[item.attrib['k']] = item.attrib['v']
                    elif item.tag == 'nd':
                        ndlist.append(item.attrib['ref'])
                
        standard = ['id','type',"version", "changeset", "timestamp", "user", "uid"]
        node['id'] = temp['id']
        node['type'] = temp['type']
        if 'visible' in temp:
            node['visible'] = temp['visible']
            del temp['visible']
        node['created'] = {'version':temp['version'],
                           'changeset':temp['changeset'],
                           'timestamp':temp['timestamp'],
                           'user':temp['user'],
                           'uid':temp['uid']}
        if temp['type'] == 'node':
            node['pos'] = [float(temp['lat']),float(temp['lon'])]
            del temp['lat']
            del temp['lon']
        if 'address' in temp:
            node['address'] = temp['address']
            del temp['address']
        for key in standard:
            del temp[key]
        for key in temp.keys():
            node[key] = temp[key]
        if not ndlist == []:
            node['node_refs'] = ndlist
            ndlist = []
        return node
    
    else:
        return None
    
# List of acceptable street types to skip
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Circle", "Highway", "Mall", "Point", "Way", "West", 
            "Broadway", "East", "North", "South"]

# Mapping dictionary
mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Rd": "Road",
            "Rd.":"Road",
            "Baseline" : "Baseline Road",
            "Arapahoe" : "Arapahoe Avenue",
            "Varra":"Varra Road",
            "Walnut": "Walnut Street",
            "st": "Street",
            "trail":"Trail",
            "ave.":"Avenue",
            "Appia": "Appia Way",
            "Roadaddr":"Avenue",
            "Ct":"Court",
            "Blvd":"Boulevard",
            "Cherryvale":"Cherryvale Road",
            "Centennial":"Centennial Trail",
            "Cir":"Circle",
            "Dr":"Drive",
            "Etna":"Etna Court",
            "Pl":"Place",
            "Valmont":"Valmont Road"
            }
# Function used to clean postcode field
def clean_post(postcode):
    if len(postcode) == 5:
        pass
    elif re.match('CO', postcode):
        postcode = re.sub('CO', '', postcode).strip()
    elif len(postcode.strip()) ==10:
        postcode = postcode[0:5]
    return postcode
        

# Function to determine whether or not the street type is in an acceptable format
def audit_street_type(street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_name = update_name(street_name, mapping)
    street_name = fix_direction(street_name)
    return street_name

# Uses mapping dictionary to replace inconsistent street names.
def update_name(name, mapping):
    if street_type_re.search(name):
        temp = street_type_re.search(name)
        key = name[temp.start():] 
        try:
            new = name[:temp.start()]+ mapping[key]
            name = new
        except:
            pass     
    return name

def fix_direction(name):
    if re.match(r'E\.?\s', name):
        name = re.sub(r'E\.?\s', r'East ', name)        
    elif re.match(r'S\.?\s', name):
        name = re.sub(r'S\.?\s', r'South ', name)        
    elif re.match(r'N\.?\s', name):
        name = re.sub(r'N\.?\s', r'North ', name)  
    elif re.match(r'W\.?\s', name):
        name = re.sub(r'W\.?\s', r'West ', name)
    return name

# Main function to open the file and process the json file.
def process_map(file_in, pretty = False):
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def test():
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    data = process_map('boulder.osm', False)
    
    #pprint.pprint(data)
    

    #print len(data)


if __name__ == "__main__":
    test()