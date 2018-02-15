#!/usr/bin/python
# -*- coding: UTF-8 -*-



'''
Created on Jan 10, 2017

@author: hegxiten
'''
import sys
from imposm.parser import OSMParser
import geo.haversine as haversine
import numpy
import time
from scipy import spatial
import csv
import codecs
import networkx as nx

import station_nodes
import way_network
import network_process
import NX_instantiate
import visualize

default_encoding='utf-8'
if sys.getdefaultencoding()!=default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

PI=3.14159265358
#FILE='beijing_china_latest.osm.pbf'
FILE='illinois-latest.osm.pbf'
FOLDER='/home/hegxiten/workspace/data/'+FILE+'/'




CONCURRENCYVAL=4
GLOBALROUNDINGDIGITS=5


station_dict=station_nodes.extract_station_nodes(FOLDER,FILE,CONCURRENCYVAL,GLOBALROUNDINGDIGITS)
station_nodes.output_station_csv(FOLDER,FILE,station_dict)

way_network_extraction=way_network.extract_way_network(FOLDER,FILE,CONCURRENCYVAL, GLOBALROUNDINGDIGITS)
way_segment_list=way_network_extraction[0]
way_segment_tag_dict=way_network_extraction[1]

coord_list=way_network_extraction[2]
coord_dict=way_network_extraction[3]

way_network.output_waysegment_csv(FOLDER,FILE,way_segment_list,way_segment_tag_dict)
way_network.output_waysegmentcoord_csv(FOLDER,FILE,coord_list, coord_dict)

node_fromto_dict=network_process.process_network(FOLDER, FILE, CONCURRENCYVAL, GLOBALROUNDINGDIGITS)

visualize.visualizewayNetwork(FOLDER, FILE, CONCURRENCYVAL, GLOBALROUNDINGDIGITS)

NX_instantiate.create_NX_graph(FOLDER, FILE, CONCURRENCYVAL, GLOBALROUNDINGDIGITS)
