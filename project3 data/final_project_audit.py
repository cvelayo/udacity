"""
Your task in this exercise has two steps:

- audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix 
    the unexpected street types to the appropriate ones in the expected list.
    You have to add mappings only for the actual problems you find in this OSMFILE,
    not a generalized solution, since that may and will depend on the particular area you are auditing.
- write the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and should return the fixed name
    We have provided a simple test so that you see what exactly is expected
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "boulder.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)



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


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    print street_types
    return street_types


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


def test():
    st_types = audit(OSMFILE)

    pprint.pprint(dict(st_types))

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, mapping)
            print name, "=>", better_name



if __name__ == '__main__':
    test()