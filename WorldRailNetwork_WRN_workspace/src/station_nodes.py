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
from sphinx.versioning import levenshtein_distance

default_encoding='utf-8'
if sys.getdefaultencoding()!=default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

PI=3.14159265358

def extract_station_nodes(FOLDER,FILE,CONCURRENCYVAL,GLOBALROUNDINGDIGITS):
    
    station_dict={}
    station_dict_complete={}
    subway_nodes_complete=set()
    subway_ways_from_relations=set()

    def collect_subway_nodes():
        def imposm_extract_subway_nodes_from_relations(relations):
            target_relation_tags=["subway","light_rail","tram"]
            for osmid, tags, members in relations:
                if tags.get("route","") in target_relation_tags or tags.get("railway") in target_relation_tags:
                    for m in members:
                        if m[1]=="node":
                            subway_nodes_complete.add(m[0])
                        if m[1]=="way":
                            subway_ways_from_relations.add(m[0])
        
        def imposm_extract_subway_nodes_from_ways(ways):
            target_way_tags=["subway","light_rail","tram"]
            for osmid, tags, refs in ways:
                if tags.get("railway","") in target_way_tags or osmid in subway_ways_from_relations:
                    for r in refs:
                        subway_nodes_complete.add(r)
        
    
        OSMParser(concurrency=CONCURRENCYVAL, relations_callback=imposm_extract_subway_nodes_from_relations).parse(FOLDER+FILE)
        OSMParser(concurrency=CONCURRENCYVAL, ways_callback=imposm_extract_subway_nodes_from_ways).parse(FOLDER+FILE)
      
    def station_nodes_from_areas():
        def imposm_extract_railway_station_nodes_from_areas(areas):
            target_area_tags=["station"]
            excluding_area_tags=["light_rail","subway"]
            for osmid, tags, refs in areas:
                '''areas are using the same key as ways in OpenStreetMap, while areas are "closed ways"'''
                if tags.get("railway","") in target_area_tags and tags.get("station","") not in excluding_area_tags:
                    station_dict[refs[0]]=[tags.get("name","N/A")]
                    station_dict_complete[refs[0]]=[tags]
                    '''the substitution node for the area of the station is to be refined'''
            
        def imposm_nodes_substitute_for_area_stations(coords):
            '''must running after imposm_extract_station_from_areas for some induced station substitution nodes are not extracted by OSMParser callbacks'''
            for osmid, lon, lat in coords:
                if osmid in station_dict and len(station_dict[osmid])==1:
                    station_dict[osmid].append(lat)
                    station_dict[osmid].append(lon)
                    station_dict[osmid].append("railwaysuffix")
                    station_dict_complete[osmid].append(lat)
                    station_dict_complete[osmid].append(lon)
                    station_dict_complete[osmid].append("railwaysuffix")
        OSMParser(concurrency=CONCURRENCYVAL, ways_callback=imposm_extract_railway_station_nodes_from_areas).parse(FOLDER+FILE)     
        OSMParser(concurrency=CONCURRENCYVAL, coords_callback=imposm_nodes_substitute_for_area_stations).parse(FOLDER+FILE)
    
                
    def station_nodes_from_nodes():
        def imposm_extract_railway_station_nodes_from_nodes(nodes):
            target_node_tags=["station"]
            excluding_node_tags=["light_rail","subway"]
            for osmid, tags, (lon,lat) in nodes:
                if tags.get("railway","") in target_node_tags and tags.get("station","") not in excluding_node_tags:             
                    station_dict[osmid]=[tags.get("name","N/A"),lat,lon]
                    station_dict_complete[osmid]=[tags, lat, lon]
        OSMParser(concurrency=CONCURRENCYVAL, nodes_callback=imposm_extract_railway_station_nodes_from_nodes).parse(FOLDER+FILE)

    
    def station_nodes_from_ways():
        def imposm_extract_railway_station_nodes_from_ways(ways):
            '''get accurate railway stations from exact railways ways instead of getting wrong subway stations'''
            target_way_tags=["rail"]
            for osmid, tags, refs in ways:
                if tags.get("railway","") in target_way_tags:
                    for i in refs:
                        if i in station_dict:
                            station_dict[i].append("railwaysuffix")
        OSMParser(concurrency=CONCURRENCYVAL, ways_callback=imposm_extract_railway_station_nodes_from_ways).parse(FOLDER+FILE)
    
    def station_nodes_from_relations():
        def imposm_extract_railway_stations_from_relations(relations):
            '''get accurate railway stations from exact railways relations instead of getting wrong subway stations'''
            target_relation_tags=["train","rail"]
            for osmid, tags, members in relations:
                if tags.get("route") in target_relation_tags or tags.get("railway") in target_relation_tags:
                    for i in members:
                        if i[1]=="node" and (i[0] in station_dict):
                            station_dict[i[0]].append("railwaysuffix")
        OSMParser(concurrency=CONCURRENCYVAL, relations_callback=imposm_extract_railway_stations_from_relations).parse(FOLDER+FILE)
    
    def filterout():
        def filterout_subway_station_nodes_in_dic():
            for s in subway_nodes_complete:
                if s in station_dict and station_dict[s][-1]!="railwaysuffix":
                    del station_dict[s]
        
        def filterout_repeating_stations():
            '''repeating station string processing is to be refined'''
            repeating_station_set=set()
            station_nodes_coord=[]
            stationmap=[]
            for s in station_dict:
                station_nodes_coord.append((station_dict[s][1],station_dict[s][2]))
                stationmap.append(s)
            tree = spatial.KDTree(station_nodes_coord)
            for s in station_dict:
                similarstation_dict={}
                similarstation_dict[s]=[station_dict[s][0],station_dict[s][1],station_dict[s][2]]
                res=tree.query((station_dict[s][1],station_dict[s][2]), k=3)
                for i in res[1]:
                    a=station_dict[s][0]
                    b=station_dict[stationmap[i]][0]
                    if a and b:
                        if haversine.hav_distance(station_dict[s][1],station_dict[s][2],station_dict[stationmap[i]][1],station_dict[stationmap[i]][2])<0.05:
                            if levenshtein_distance(station_dict[s][0], station_dict[stationmap[i]][0])<=1 or a.split(" ")[:2]==b.split(" ")[:2]:
                                if len(a)<=len(b):
                                    station_dict[stationmap[i]][0]=station_dict[s][0]
                                else:
                                    station_dict[s][0]=station_dict[stationmap[i]][0]
            iterated=set()
            for s in station_dict:
                if s in iterated:
                    continue
                else:
                    nearbystation_dict={}
                    nearbystation_dict[s]=[station_dict[s][0],station_dict[s][1],station_dict[s][2]]
                    res=tree.query((station_dict[s][1],station_dict[s][2]), k=5)
                    for i in res[1]:
                        nearbystation_dict[stationmap[i]]=[station_dict[stationmap[i]][0],station_dict[stationmap[i]][1],station_dict[stationmap[i]][2]]
                    keys=nearbystation_dict.keys()
                    values=nearbystation_dict.values()
                    namelist=[]
                    for i in range(len(values)):
                        namelist.append(values[i][0])
                    repeatlist=[]
                    for i in range(len(values)):
                        if namelist.count(namelist[i])>=2 and namelist[i]:
                            repeatlist.append(keys[i])
                    if len(repeatlist)==0:
                        continue
                    else:
                        iterated.add(s)
                        iterated=iterated|set(repeatlist)
                        stationtokeep=None
                        for i in range(len(repeatlist)):
                            if station_dict[repeatlist[i]][-1]=='railway':
                                stationtokeep=repeatlist.pop(i)
                                repeating_station_set=repeating_station_set|set(repeatlist)
                                break
                        if stationtokeep:
                            continue
                        else:
                            taglength=[]
                            for r in repeatlist:                
                                taglength.append(len(station_dict_complete[r][0]))
                            repeatlist.pop(taglength.index(max(taglength)))
                            repeating_station_set=repeating_station_set|set(repeatlist)
                
            '''#First Step: remove absolute repeating stations
            for k,v in nearbystation_dict.iteritems():
                if v[0] not in namelist:
                    stationidlist.append(k)
                    namelist.append(v[0])
                else:
                    IDindex=namelist.index(v[0])
                    existcoord=(station_dict[stationidlist[IDindex]][1],station_dict[stationidlist[IDindex]][2])
                    newcoord=(v[1],v[2])
                    distance=haversine_distance(existcoord[1], existcoord[0], newcoord[1], newcoord[0])
                    if distance>3:
                        stationidlist.append(k)
                        namelist.append(v[0])
                    else:
                        repeating_station_set.add(k)
            #Second Step: remove repeating stations whose names are in small edit distances
            '''
            for rs in repeating_station_set:
                if rs in station_dict:
                    #print station_dict[rs][0]
                    del station_dict[rs]   
        filterout_subway_station_nodes_in_dic()
        filterout_repeating_stations()
                
    print("Begin:   Parse 1---> Extract all stations and kicking out subway or repeating stations...") 
    startt=time.time()   
    collect_subway_nodes()
    station_nodes_from_areas()
    station_nodes_from_nodes()
    station_nodes_from_relations()
    station_nodes_from_ways()
    filterout()
    stopt=time.time()            
    print("Finish:  Parse 1---> Extract all stations and kicking out subway or repeating stations. Time:("+str(stopt-startt)+"s)")
    return station_dict

def output_station_csv(FOLDER,FILE,station_dict):
    target = codecs.open(FOLDER+FILE+"_stations.csv", 'w',encoding='utf-8')
    for x in station_dict:
        '''Export csv file for all stations'''
        target.write(str(x)+",$"+station_dict[x][0]+"$,"+str(station_dict[x][1])+","+str(station_dict[x][2])+"\n")
        '''Example row: >>1234(osmid),$Illinois Terminal$($name$),40.11545(latitude),-88.24111(longitude)<<'''
        #print station_dict[x][0]
    target.close()

if __name__ == '__main__':
    print ("===you're in test mode of station_nodes.py===")
    FILE='beijing_china_latest.osm.pbf'
    FOLDER='/home/hegxiten/workspace/data/'+FILE+'/'
    CONCURRENCYVAL=4
    GLOBALROUNDINGDIGITS=5
    
    stationdictionary=extract_station_nodes(FOLDER,FILE,CONCURRENCYVAL,GLOBALROUNDINGDIGITS)
    output_station_csv(FOLDER,FILE,stationdictionary)
    print ("===test mode of station_nodes.py terminated===")