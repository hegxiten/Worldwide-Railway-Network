#!/usr/bin/python
# -*- coding: UTF-8 -*-



'''
Created on Jan 10, 2017

@author: hegxiten
'''
import sys
from imposm.parser import OSMParser
import numpy
import time
from scipy import spatial
import csv
import codecs

default_encoding='utf-8'
if sys.getdefaultencoding()!=default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

PI=3.14159265358

target_attr_keys=['gauge','maxspeed','highspeed','service','usage','operator']
def extract_way_network(FOLDER,FILE,CONCURRENCYVAL,GLOBALROUNDINGDIGITS):

    railway_wayid_set=set()
    list_of_reflist_complete=[]
    way_segment_list=[]
    way_segment_tag_dict={}
    refnode_idset_for_coords=set()
    coord_list=[]
    coord_dict={}
    
    
    def imposm_extract_railway_ways_from_relations(relations):
        target_relation_tags=["train","rail"]
        for osmid, tags, members in relations:
            if tags.get("route") in target_relation_tags or tags.get("railway") in target_relation_tags:
                for x in members:
                    if x[1] =="way":
                        railway_wayid_set.add(x)
        
    print("Begin:   Parse 2---> Extract railway way elements from relations...")
    startt=time.time()        
    OSMParser(concurrency=CONCURRENCYVAL, relations_callback=imposm_extract_railway_ways_from_relations).parse(FOLDER+FILE)
    stopt=time.time()
    print("Finish:  Parse 2---> Extract railway ways elements from relations. Time:("+str(stopt-startt)+"s)")
            
    def imposm_extract_railway_ways_from_ways(ways):
        target_way_tags=["train","rail"]
        
        for osmid, tags, refs in ways:
            if tags.get("route") in target_way_tags or tags.get("railway") in target_way_tags or osmid in railway_wayid_set:
                list_of_reflist_complete.append(refs)
                for i in range(len(refs)):
                    refnode_idset_for_coords.add(refs[i])                
                for i in range(len(refs)-1):
                    way_segment_list.append([refs[i], refs[i+1]])
                    way_segment_tag_dict[(refs[i], refs[i+1])]={}
                    for attr in target_attr_keys:
                        way_segment_tag_dict[(refs[i], refs[i+1])].update({attr:tags.get(attr,'N/A')})
        
    print("Begin:   Parse 3---> Extract railway segments with imposm ways_callback...")
    startt=time.time()    
    OSMParser(concurrency=CONCURRENCYVAL, ways_callback=imposm_extract_railway_ways_from_ways).parse(FOLDER+FILE)
    stopt=time.time()
    print("Finish:  Parse 3---> Extract railway segments with imposm ways_callback. Time:("+str(stopt-startt)+"s)")
    
    print("Probe:   >>>>>>>>>>> Number of total nodes needed: "+str(len(refnode_idset_for_coords))+"<<<<<<<<<<<")
    
    def imposm_extract_refnode_coords(coords):    
        for (coordid,lon,lat) in coords:
            if coordid in refnode_idset_for_coords:
                if coordid not in coord_dict:
                    coord_dict[coordid]=len(coord_list)
                    coord_list.append([lat,lon])        

    print("Begin:   Parse 4---> Extract required coordinates of related nodes...")
    startt=time.time()    
    OSMParser(concurrency=CONCURRENCYVAL, coords_callback=imposm_extract_refnode_coords).parse(FOLDER+FILE)
    stopt=time.time()
    print("Finish:  Parse 4---> Extract required coordinates of related nodes. Time:("+str(stopt-startt)+"s)")
    
    network_extraction_list=[way_segment_list,way_segment_tag_dict,coord_list,coord_dict]
    return network_extraction_list

def output_waysegment_csv(FOLDER,FILE,way_segment_list,way_segment_tag_dict):
    target = codecs.open(FOLDER+FILE+"_waysegments.csv", 'w',encoding='utf-8')
    headerkeys=way_segment_tag_dict.values()[0].keys()
    header='vertex_1,vertex_2'
    for k in headerkeys:
        header=header+','+k
    target.write(header+'\n')
    for x in way_segment_list:
        row_to_write=str(x[0])+","+str(x[1])
        for attr in headerkeys:
            row_to_write=row_to_write+','+str(way_segment_tag_dict[tuple(x)].get(attr,"N/A"))
        target.write(row_to_write+"\n")
        '''Example row: >>1234567(osmid1),7654321(osmid2),1435(gauge),350(maxspeed in kph),yes(highspeed or not),N/A(service),main(usage)<<'''
    target.close()
    
    
def output_waysegmentcoord_csv(FOLDER,FILE,coord_list,coord_dict):
    target = codecs.open(FOLDER+FILE+"_waysegment_nodecoords.csv", 'w',encoding='utf-8')
    for x in coord_dict:
        target.write(str(x)+","+str(coord_list[coord_dict[x]][0])+","+str(coord_list[coord_dict[x]][1])+"\n")#coordid, lat, lon
        '''Example row: >>123(osmid),40.11545(latitude),-88.24111(longitude)<<'''
    target.close()

if __name__ == '__main__':
    print ("===you're in test mode of way_network.py===")
    FILE='beijing_china_latest.osm.pbf'
    FOLDER='/home/hegxiten/workspace/data/'+FILE+'/'
    CONCURRENCYVAL=4
    GLOBALROUNDINGDIGITS=5
   
    extraction=extract_way_network(FOLDER,FILE,CONCURRENCYVAL,GLOBALROUNDINGDIGITS)
    way_segment_list=extraction[0]
    way_segment_tag_dict=extraction[1]
    coord_list=extraction[2]
    coord_dict=extraction[3]
    output_waysegment_csv(FOLDER,FILE,way_segment_list, way_segment_tag_dict)
    output_waysegmentcoord_csv(FOLDER,FILE,coord_list, coord_dict)
    print ("===test mode of way_network.py terminated===")



