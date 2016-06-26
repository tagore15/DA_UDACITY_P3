#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if the second level tag "k" value contains problematic characters, it should be ignored
- if the second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if the second level tag "k" value does not start with "addr:", but contains ":", you can
  process it in a way that you feel is best. For example, you might split it into a two-level
  dictionary like with "addr:", or otherwise convert the ":" to create a valid key.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = ["version", "changeset", "timestamp", "user", "uid"]
MAP_AMENITY = {"clinic":"doctors", "pub":"bar"}
GOVERNMENT_ABBR_LIST = ["Govt.", "Govt", "Govr" ]

def shape_element(element, isClean):
    """ parses xml element and creates JSON """
    node = {}
    if element.tag == "node" or element.tag == "way" :
        # YOUR CODE HERE
        if element.tag == "node":
            node["pos"] = []
	    lat = element.get("lat")
	    lon = element.get("lon")
	    if lat:
            	node["pos"].append(float(lat))
	    if lon:
            	node["pos"].append(float(lon))
            node["type"] = "node"
        else:
            node["type"] = "way"
        for k in element.keys():
            if k in CREATED:
                if "created" not in node:
                    node["created"] = {}
                node["created"][k] = element.get(k)
            elif k not in ["lat", "lon"]:
                node[k] = element.get(k)
                
        for e in element.iter():
            if e.tag == "tag":
                k_value = e.get("k")
                v_value = e.get("v")
                if re.search(problemchars, k_value):
                    continue
                m = re.search(lower_colon, k_value)
                if m:
                    splits = k_value.split(":")
                    if k_value.startswith("addr:"):
                        if "address" not in node:
                            node["address"] = {}
			if isClean:
			    if splits[1] == "postcode":
			    	v_value = re.sub(" ", "", v_value) # removes spaces
				# check if it is a 6 digit numerical code				
				if not re.match(r'^\d{6}$', v_value): 
			            continue
                        node["address"][splits[1]] = v_value
                else:
                    if isClean and k_value == "amenity":
	                v_value = v_value.lower()
		        if v_value in MAP_AMENITY:
		            v_value = MAP_AMENITY[v_value]
		    if isClean and k_value == "name":
		    	for g in GOVERNMENT_ABBR_LIST:
                            v_value = re.sub(g, "Government", v_value, flags = re.I) 
                    node[k_value] = v_value
            if e.tag == "nd":
                if "node_refs" not in node:
                    node["node_refs"] = []
                node["node_refs"].append(e.get("ref"))
        return node
    else:
        return None


def process_map(file_in, isClean = False, pretty = False):
    """ read files to parse all top level xml elements and dump in a json file """
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    #data = []
    with codecs.open(file_out, "w") as fo:
        #context = ET.iterparse(file_in)
        #context = iter(context)
        #event,root = context.next()
        for _, element in ET.iterparse(file_in):
        #for event, element in context:
            el = shape_element(element, isClean)
            if el:
                #data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
            if element.tag == "node" or element.tag == "way":
                element.clear()


