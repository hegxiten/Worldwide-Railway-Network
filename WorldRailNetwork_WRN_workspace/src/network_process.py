#!/usr/bin/python
# -*- coding: UTF-8 -*-



'''
Created on Jan 17, 2017

@author: hegxiten
'''

import sys
import geo.haversine as haversine
from imposm.parser import OSMParser
import geo.haversine as haversine
import numpy
import time
from scipy import spatial
import csv
import codecs
import math

default_encoding='utf-8'
if sys.getdefaultencoding()!=default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

PI=3.14159265358

def process_network(FOLDER,FILE,CONCURRENCYVAL,GLOBALROUNDINGDIGITS):

    stations={}
    '''stations[station_node_osmid]=[name, lat, lon]'''
    refnodes_index_dict={}        
    '''refnodes_index_dict[nodeid]=listindex_of_nodeid'''
    refnodes=[]             
    '''refnodes=[nodeid1,nodeid2,nodeid3...]'''
    refnodes_coord_list=[]        
    '''refnodes_coord_list[coord1,coord2,coord3...]'''
    node_fromto_dict={}     
    '''node_fromto_dict[fromnode]=[(fromnode,tonode1),(fromnode,tonode2),(fromnode,tonode3)...]'''
    distance_mapper={}     
    '''distance_mapper[(fromnode,tonode)]=distance'''
    attribute_mapper={}
    '''attribute_mapper[(fromnode,tonode)]=attribute_dictionary'''
    
    midpoints_coord=[]      
    '''miderpoint_map[(fromnode,tonode)]=(midercoord)'''
    midsegment=[]
    
    
    approxCoord_map={}       
    '''approxCoord_map[coord]=nodeid(veryfirstone)'''
    refnode_mapper={}       
    '''refnode_mapper[nodeid2]=nodeid1(previous_nodeid1 with the same coordinate as nodeid2 after digit rounding)'''
    edgeDict={}             
    '''edgeDict[(vertex tuple)]=(edgereflist,edgelength)'''
    disconnected_stations=[]
    connected_stations=[]
    
    def loadstations():
        '''Load stations from csv format output'''
        startt=time.time()
        with codecs.open(FOLDER+FILE+'_stations.csv', 'rb') as csvfile:
            '''Example row: >>1234(osmid),$Illinois Terminal$($name$),40.11545(latitude),-88.24111(longitude)<<'''
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
            for row in spamreader:
                stations[int(row[0])]=[row[1],float(row[2]),float(row[3])]
        stopt=time.time()
        print("Loading stations. Time:("+str(stopt-startt)+")")

    
    def loadcoordinates():
        '''Load coordinates of reference-nodes from csv format output'''
        startt=time.time()
        with codecs.open(FOLDER+FILE+'_waysegment_nodecoords.csv', 'rb',encoding='utf-8') as csvfile:
            '''Example row: >>123(osmid),40.11545(latitude),-88.24111(longitude)<<'''
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
            for row in spamreader:
                c1,c2=float(row[1]),float(row[2])
                '''c1--lat, c2--lon'''
                #c1,c2=round(float(row[1]),ROUNDINGDIGITS),round(float(row[2]),ROUNDINGDIGITS)
                if (c1,c2) not in approxCoord_map:
                    approxCoord_map[(c1,c2)]=int(row[0])         
                    '''row[0]--coordid'''
                    refnodes_index_dict[int(row[0])]=len(refnodes_coord_list)
                    refnodes.append(int(row[0]))
                    refnodes_coord_list.append((c1,c2))
                    refnode_mapper[int(row[0])]=int(row[0])
                else:
                    refnode_mapper[int(row[0])]=approxCoord_map[(c1,c2)]
        stopt=time.time()
        print("Loading refnode coordinates. Time:("+str(stopt-startt)+")")
    
    
    def loadwaysegments():
        '''Load way segments from csv format output'''
        startt=time.time()
        with codecs.open(FOLDER+FILE+'_waysegments.csv', 'rb',encoding='utf-8') as csvfile:
            '''Example row: >>1234567(osmid1),7654321(osmid2),1435(gauge),350(maxspeed in kph),yes(highspeed or not),N/A(service),main(usage)<<'''
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
            header=spamreader.next()
            attr_list=header[2:]
            attr_list.append('distance')
            for row in spamreader:
                if refnode_mapper.get(int(row[0])) is None:
                    print ("none")
                else:
                    mfrom=refnode_mapper[int(row[0])]
                    mto=refnode_mapper[int(row[1])]
                    
                    if mfrom not in node_fromto_dict:
                        node_fromto_dict[mfrom]=[]
                    if mto not in node_fromto_dict:
                        node_fromto_dict[mto]=[]
        
                    distance=haversine.hav_distance(refnodes_coord_list[refnodes_index_dict[mfrom]][0],refnodes_coord_list[refnodes_index_dict[mfrom]][1], refnodes_coord_list[refnodes_index_dict[mto]][0],refnodes_coord_list[refnodes_index_dict[mto]][1])
                    attr_dict={}
                    for i in attr_list:
                        if i=='distance':
                            attr_dict[i]=str(distance)
                        else:
                            attr_dict[i]=row[header.index(i)]
                    attribute_mapper[(mfrom,mto)]=attr_dict
                    attribute_mapper[(mto,mfrom)]=attr_dict

                    if (mfrom,mto) not in node_fromto_dict[mfrom] and mfrom!=mto:
                        node_fromto_dict[mfrom].append((mfrom,mto))
                    if (mto,mfrom) not in node_fromto_dict[mto] and mfrom!=mto:
                        node_fromto_dict[mto].append((mto,mfrom))
    
        '''station's connectivity judging by suffix'''
        for s in stations:
            if s not in node_fromto_dict:
                disconnected_stations.append(s)
                stations[s].append('disconnected')
            else:
                connected_stations.append(s)
                stations[s].append('connected')
        
        stopt=time.time()
        print("Loading way segments ("+str(stopt-startt)+")")
    

    def output_nodes_csv():
        target = codecs.open(FOLDER+FILE+"_nodes.csv", 'w',encoding='utf-8')
        for x in node_fromto_dict:
            if x in stations:
                if len(node_fromto_dict[x])!=0:
                    target.write(str(x)+",$"+stations[x][0].decode('utf-8')+"$,"+str(stations[x][1])+","+str(stations[x][2])+"\n")        
            else:
                target.write(str(x)+",$$,"+str(refnodes_coord_list[refnodes_index_dict[x]][0])+","+str(refnodes_coord_list[refnodes_index_dict[x]][1])+"\n")        
        target.close()
        '''Example row: >>1234(osmid),$Illinois Terminal$($name$),40.11545(latitude),-88.24111(longitude)<<'''

    def output_links_csv():
        target = codecs.open(FOLDER+FILE+"_links.csv", 'w',encoding='utf-8')
        headerkeys=attribute_mapper.values()[0].keys()
        header='vertex_1,vertex_2'
        for k in headerkeys:
            header=header+','+k
        target.write(header+'\n')
        for x in node_fromto_dict:
            for (a,b) in node_fromto_dict[x]:
                if a in node_fromto_dict and b in node_fromto_dict:
                    row_to_write=str(a)+","+str(b)
                    for attr in headerkeys:
                        row_to_write=row_to_write+','+attribute_mapper[(a,b)].get(attr,"N/A")
                    target.write(row_to_write+"\n")        
        target.close()
        '''Example row: >>1234(osmid_vertex1),5678(osmid_vertex2),0.1534285(haversine_distance)<<'''
    loadstations()
    loadcoordinates()
    loadwaysegments()
    output_nodes_csv()
    output_links_csv()
    
    return node_fromto_dict

if __name__ == '__main__':
    print ("===you're in test mode of network_process.py===")
    FILE='beijing_china_latest.osm.pbf'
    FOLDER='/home/hegxiten/workspace/data/'+FILE+'/'
    CONCURRENCYVAL=4
    GLOBALROUNDINGDIGITS=5
    
    node_fromto_dict=process_network(FOLDER, FILE, CONCURRENCYVAL, GLOBALROUNDINGDIGITS)
    print ("===test mode of network_process.py terminated===")
