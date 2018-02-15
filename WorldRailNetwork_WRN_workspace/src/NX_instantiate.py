#!/usr/bin/python
# -*- coding: UTF-8 -*-



'''
Created on Jan 17, 2017

@author: hegxiten
'''

import networkx as nx
import time
import codecs
import csv
import sys

default_encoding='utf-8'
if sys.getdefaultencoding()!=default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

PI=3.14159265358

def create_NX_graph(FOLDER,FILE,CONCURRENCYVAL,GLOBALROUNDINGDIGITS):
    
    G=nx.Graph()
    
    #Load stations
    startt=time.time()
    with codecs.open(FOLDER+FILE+'_stations.csv', 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
        for row in spamreader:
            G.add_node(int(row[0]), name=row[1], coordinate=(float(row[2]),float(row[3])))
            
    stopt=time.time()
    print("Networkx:: Adding stations to Networkx Graph. Time:("+str(stopt-startt)+")")
    
    #Load nodes
    startt=time.time()
    with codecs.open(FOLDER+FILE+'_WRN_nodes.csv', 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
        for row in spamreader:
            G.add_node(int(row[0]), name=row[1], coordinate=(float(row[2]),float(row[3])))
    stopt=time.time()
    print("Networkx:: Adding nodes to Networkx Graph. Time:("+str(stopt-startt)+")")
    
    #Load links
    startt=time.time()
    with codecs.open(FOLDER+FILE+'_WRN_links.csv', 'rb',encoding='utf-8') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
        header=spamreader.next()
        for row in spamreader:
            G.add_edge(int(row[0]), int(row[1]), distance=float(row[header.index('distance')]))
    stopt=time.time()
    print("Networkx:: Adding edges to Networkx Graph. Time:("+str(stopt-startt)+")")
    

if __name__ == '__main__':
    print ("===you're in test mode of networkx_instantiate.py===")
    FILE='beijing_china_latest.osm.pbf'
    FOLDER='/home/hegxiten/workspace/data/'+FILE+'/'
    CONCURRENCYVAL=4
    GLOBALROUNDINGDIGITS=5
    
    create_NX_graph(FOLDER, FILE, CONCURRENCYVAL, GLOBALROUNDINGDIGITS)
    print ("===test mode of networkx_instantiate.py terminated===")