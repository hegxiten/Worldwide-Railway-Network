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

def simplify():
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

    def collectEdges():

        allEdgeRef=[]
        parsedset=set()
        for n in node_fromto_dict:
            if len(node_fromto_dict[n])==2:
                allEdgeRef.append(n)
        for n in allEdgeRef:
            if n in parsedset:
                continue
            else:
                backbottom=n
                frontbottom=n
                backtop=node_fromto_dict[n][0][1]
                fronttop=node_fromto_dict[n][1][1]
                backreflist=[n,backtop]
                frontreflist=[n,fronttop]
                edgelength=distance_mapper[(n,backtop)]+distance_mapper[(n,fronttop)]
                while node_fromto_dict.has_key(backtop) and (len(node_fromto_dict[backtop])==2):
                    cachenode=backtop
                    for (mfrom,mto) in node_fromto_dict[backtop]:
                        if mto != backbottom:
                            backtop=mto
                    backreflist.append(backtop)
                    backbottom=cachenode
                    edgelength+=distance_mapper[(backbottom,backtop)]
                while node_fromto_dict.has_key(fronttop) and (len(node_fromto_dict[fronttop])==2):
                    cachenode=fronttop
                    for (mfrom,mto) in node_fromto_dict[fronttop]:
                        if mto != frontbottom:
                            fronttop=mto
                    frontreflist.append(fronttop)
                    frontbottom=cachenode
                    edgelength+=distance_mapper[(frontbottom,fronttop)]
                backreflist=list(reversed(backreflist))
                backreflist=backreflist[:-1]
                edgereflist=backreflist+frontreflist
                reverseedgereflist=list(reversed(edgereflist))
                
                parsedset=parsedset|set(edgereflist)
                
                vertexset=tuple(sorted([edgereflist[0],edgereflist[-1]]))
                
                if edgeDict.get(vertexset) is None:
                    edgeDict[vertexset]={}
                    edgeDict[vertexset][tuple(sorted(edgereflist))]=[edgereflist,reverseedgereflist,edgelength]
                else:
                    edgeDict[vertexset][tuple(sorted(edgereflist))]=[edgereflist,reverseedgereflist,edgelength]
                    
                
    
    
    def removeSidings(maxlengththreshold=5):
        sidingnodeset=set()
        for vs in edgeDict.keys():
            
            if len(edgeDict[vs])>=2:
                
                print ("potentialsiding:"+str(vs))
                mainedge=[]
                reversedmainedge=[]
                sidinglist=[]
                edgelist=[]
                reversededgelist=[]
                lengthlist=[]

                for edge in edgeDict[vs].values():
                    edgelist.append(edge[0])
                    reversededgelist.append(edge[1])
                    lengthlist.append(edge[2])

                maxlength=max(lengthlist)
                minlength=min(lengthlist)
                
                if maxlength>maxlengththreshold:
                    continue
                else:
                    print("yes! siding!")
                    '''for p in edgelist:
                        for n in p:
                            if n in stations:
                                print n
                                if p in edgelist:
                                    mainedge=edgelist.pop(edgelist.index(p))
                                    sidinglist=edgelist'''
                    if mainedge==[]:
                        mainedge=edgelist.pop(lengthlist.index(minlength))
                        sidinglist=edgelist
                    
                    
                    for siding in sidinglist:
                        if tuple(sorted(siding)) in edgeDict[vs]:
                            del edgeDict[vs][tuple(sorted(siding))]
                
                        for sn in siding[1:-2]:
                            if sn in node_fromto_dict:
                                sidingnodeset.add(sn)
                        if (mainedge[0],siding[1]) in node_fromto_dict[mainedge[0]]:
                            node_fromto_dict[mainedge[0]].remove((mainedge[0],siding[1]))
                            print ("root removed!"+str((mainedge[0],siding[1])))
                        if (mainedge[0],siding[-2]) in node_fromto_dict[mainedge[0]]:
                            node_fromto_dict[mainedge[0]].remove((mainedge[0],siding[-2]))
                            print ("root removed!"+str((mainedge[0],siding[-2])))
                        if (mainedge[-1],siding[-2]) in node_fromto_dict[mainedge[-1]]:
                            node_fromto_dict[mainedge[-1]].remove((mainedge[-1],siding[-2]))
                            print ("root removed!"+str((mainedge[-1],siding[-2])))
                        if (mainedge[-1],siding[1]) in node_fromto_dict[mainedge[-1]]:
                            node_fromto_dict[mainedge[-1]].remove((mainedge[-1],siding[1]))
                            print ("root removed!"+str((mainedge[-1],siding[1])))
        for n in sidingnodeset:
            if n in node_fromto_dict:
                del node_fromto_dict[n]


    def midpointget(node_fromto_dict):
        midpoint_dict={}
        waysegment=[]
        for i in node_fromto_dict.values():
            for p in i:
                waysegment.append(p)
        for (mfrom, mto) in waysegment:
            midlat=(refnodes_coord_list[refnodes_index_dict[mfrom]][0]+refnodes_coord_list[refnodes_index_dict[mto]][0])/2
            midlon=(refnodes_coord_list[refnodes_index_dict[mfrom]][1]+refnodes_coord_list[refnodes_index_dict[mto]][1])/2
                    
            midpoints_coord.append((midlat,midlon))
            midsegment.append(((mfrom,mto),(mto,mfrom)))

            
            
    def connectstations(thresholddistance=1):
        startt=time.time()
        tree = spatial.KDTree(midpoints_coord)
        print("Iterating ...")
        l=0
        for s in disconnected_stations:    
            res=tree.query([stations[s][1],stations[s][2]], k=1)
            '''query nearest two nodes to reduce branches'''
            #print (res)
            #print(stations[s][0]+","+str(round(res[0],3))+","+str(refnodes[res[1]]))
           
            nearestsegment=midsegment[res[1]]
            segvertex1=midsegment[res[1]][0][0]
            segvertex2=midsegment[res[1]][0][1]
            
            distance_1S=haversine.hav_distance(stations[s][1],stations[s][2],refnodes_coord_list[refnodes_index_dict[segvertex1]][0],refnodes_coord_list[refnodes_index_dict[segvertex1]][1])
            distance_2S=haversine.hav_distance(stations[s][1],stations[s][2],refnodes_coord_list[refnodes_index_dict[segvertex2]][0],refnodes_coord_list[refnodes_index_dict[segvertex2]][1])
            distance_12=haversine.hav_distance(refnodes_coord_list[refnodes_index_dict[segvertex1]][0],refnodes_coord_list[refnodes_index_dict[segvertex1]][1],refnodes_coord_list[refnodes_index_dict[segvertex2]][0],refnodes_coord_list[refnodes_index_dict[segvertex2]][1])
      
            ss=(distance_12+distance_1S+distance_2S)/2
            dis_from_station_to_waysegment=(2*math.sqrt(ss*(ss-distance_12)*(ss-distance_1S)*(ss-distance_2S))/distance_12)
         
            node_fromto_dict[s]=[]
            #stationstatusdict[s]='lonely'
           
            if dis_from_station_to_waysegment <= thresholddistance:
                '''if distance_1S<distance_2S:
                    for i in node_fromto_dict[refnodes[res[1][0]]]:
                        node_fromto_dict[s].append((s,i[1]))
                        node_fromto_dict[i[1]].remove((i[1],refnodes[res[1][0]]))
                        node_fromto_dict[i[1]].append((i[1],s))
                    
                    node_fromto_dict.pop(refnodes[res[1][0]])
                else:
                    for i in node_fromto_dict[refnodes[res[1][1]]]:
                        node_fromto_dict[s].append((s,i[1]))
                        node_fromto_dict[i[1]].remove((i[1],refnodes[res[1][1]]))
                        node_fromto_dict[i[1]].append((i[1],s))
                    
                    node_fromto_dict.pop(refnodes[res[1][1]])'''
                
                distance_mapper[(s,segvertex1)]=distance_1S
                distance_mapper[(segvertex1,s)]=distance_1S
                distance_mapper[(s,segvertex2)]=distance_2S
                distance_mapper[(segvertex2,s)]=distance_2S
                if node_fromto_dict.get(segvertex1) is None:
                    node_fromto_dict[segvertex1]=[]
                if node_fromto_dict.get(segvertex2) is None:
                    node_fromto_dict[segvertex2]=[]
                node_fromto_dict[s].append((s,segvertex1))
                node_fromto_dict[segvertex1].append((segvertex1,s))
                node_fromto_dict[s].append((s,segvertex2))
                node_fromto_dict[segvertex2].append((segvertex2,s))
                
                if (segvertex1,segvertex2) in node_fromto_dict[segvertex1]:
                    node_fromto_dict[segvertex1].remove((segvertex1,segvertex2))
                if (segvertex2,segvertex1) in node_fromto_dict[segvertex2]:
                    node_fromto_dict[segvertex2].remove((segvertex2,segvertex1))
                if s not in refnodes_index_dict:
                    refnodes_index_dict[s]=len(refnodes_coord_list)
                    refnodes.append(s)
                    refnodes_coord_list.append((stations[s][1],stations[s][2]))
                if s not in refnode_mapper:
                    refnode_mapper[s]=s
            
            if l%1000==0:
                print(str(l)+"/"+str(len(stations)))
            l=l+1

        stopt=time.time()
        print("Connecting isolated station nodes to the network. Time:("+str(stopt-startt)+")")
    
    def removeSpurLines(node_fromto_dict,thresholdvalue):
        startt=time.time()
        spurlistComplete=[]
        allNodes=node_fromto_dict.keys()
        for n in allNodes:
            if (len(node_fromto_dict[n])==1) and (n not in stations):
                bottomnode=node_fromto_dict[n][0][0]
                topnode=node_fromto_dict[n][0][1]
                spurnodelist=[bottomnode]
                spurLength=distance_mapper[(bottomnode,topnode)]
                while node_fromto_dict.has_key(topnode) and (len(node_fromto_dict[topnode])==2) and (topnode not in stations) and spurLength<thresholdvalue:
                    spurnodelist.append(topnode)
                    cachenode=topnode
                    for (mfrom,mto) in node_fromto_dict[topnode]:
                        if mto != bottomnode:
                            topnode=mto
                    bottomnode=cachenode
                    spurLength+=distance_mapper[(bottomnode,topnode)]
                if node_fromto_dict.get(topnode) and (topnode in stations or len(node_fromto_dict[topnode])==2):
                    continue
                if node_fromto_dict.get(topnode) and len(node_fromto_dict[topnode])==1:
                    spurnodelist.append(topnode)
                if node_fromto_dict.get(topnode) and (topnode,bottomnode) in node_fromto_dict[topnode]:
                    node_fromto_dict[topnode].remove((topnode,bottomnode))
                if spurLength<thresholdvalue:
                    spurlistComplete+=spurnodelist
                    
        for i in range(len(spurlistComplete)):
            if node_fromto_dict.get(spurlistComplete[i]):
                node_fromto_dict.pop(spurlistComplete[i])
        stopt=time.time()
        return node_fromto_dict
        print("-------Performing spurlines removing ("+str(stopt-startt)+")-------")
    
    def cutSidingSwitches():
        startt=time.time()
        count=0
        switchlist=[]
        for node in node_fromto_dict:
            if node_fromto_dict.get(node):
                if len(node_fromto_dict[node])==3:
                    switchlist.append(node)
                    count+=1
        print ("----->>Start processing switches: "+str(count)+"<<-----")
        l=0
        for n in switchlist:
            if node_fromto_dict.get(n):
                if len(node_fromto_dict[n])==3:
                    
                    mtolist=[]
                    distanceDict={}
                    angleDict={}
                    
                    for (mfrom, mto) in node_fromto_dict[n]:
                        mtolist.append(mto)
                    
                    if refnodes_index_dict.get(n) and refnodes_index_dict.get(mtolist[0]) and refnodes_index_dict.get(mtolist[1]) and refnodes_index_dict.get(mtolist[2]):
                        distanceDict[(n,mtolist[0])]=haversine((refnodes_coord_list[refnodes_index_dict.get(n)][0], refnodes_coord_list[refnodes_index_dict.get(n)][1]), (refnodes_coord_list[refnodes_index_dict.get(mtolist[0])][0], refnodes_coord_list[refnodes_index_dict.get(mtolist[0])][1]))    
                        distanceDict[(n,mtolist[1])]=haversine((refnodes_coord_list[refnodes_index_dict.get(n)][0], refnodes_coord_list[refnodes_index_dict.get(n)][1]), (refnodes_coord_list[refnodes_index_dict.get(mtolist[1])][0], refnodes_coord_list[refnodes_index_dict.get(mtolist[1])][1]))
                        distanceDict[(n,mtolist[2])]=haversine((refnodes_coord_list[refnodes_index_dict.get(n)][0], refnodes_coord_list[refnodes_index_dict.get(n)][1]), (refnodes_coord_list[refnodes_index_dict.get(mtolist[2])][0], refnodes_coord_list[refnodes_index_dict.get(mtolist[2])][1]))
                        distanceDict[(mtolist[0],mtolist[1])]=haversine((refnodes_coord_list[refnodes_index_dict.get(mtolist[0])][0], refnodes_coord_list[refnodes_index_dict.get(mtolist[0])][1]), (refnodes_coord_list[refnodes_index_dict.get(mtolist[1])][0], refnodes_coord_list[refnodes_index_dict.get(mtolist[1])][1]))
                        distanceDict[(mtolist[1],mtolist[2])]=haversine((refnodes_coord_list[refnodes_index_dict.get(mtolist[1])][0], refnodes_coord_list[refnodes_index_dict.get(mtolist[1])][1]), (refnodes_coord_list[refnodes_index_dict.get(mtolist[2])][0], refnodes_coord_list[refnodes_index_dict.get(mtolist[2])][1]))
                        distanceDict[(mtolist[2],mtolist[0])]=haversine((refnodes_coord_list[refnodes_index_dict.get(mtolist[2])][0], refnodes_coord_list[refnodes_index_dict.get(mtolist[2])][1]), (refnodes_coord_list[refnodes_index_dict.get(mtolist[0])][0], refnodes_coord_list[refnodes_index_dict.get(mtolist[0])][1]))
                        try:
                            if (distanceDict[(n,mtolist[0])]**2+distanceDict[(n,mtolist[1])]**2-distanceDict[(mtolist[0],mtolist[1])]**2)/(2*distanceDict[(n,mtolist[0])]*distanceDict[(n,mtolist[1])])>1 \
                            or (distanceDict[(n,mtolist[1])]**2+distanceDict[(n,mtolist[2])]**2-distanceDict[(mtolist[1],mtolist[2])]**2)/(2*distanceDict[(n,mtolist[1])]*distanceDict[(n,mtolist[2])])>1 \
                            or (distanceDict[(n,mtolist[2])]**2+distanceDict[(n,mtolist[0])]**2-distanceDict[(mtolist[2],mtolist[0])]**2)/(2*distanceDict[(n,mtolist[2])]*distanceDict[(n,mtolist[0])])>1:
                                continue
                            else:
                                angleDict[(mtolist[0],mtolist[1])]=math.acos((distanceDict[(n,mtolist[0])]**2+distanceDict[(n,mtolist[1])]**2-distanceDict[(mtolist[0],mtolist[1])]**2)/(2*distanceDict[(n,mtolist[0])]*distanceDict[(n,mtolist[1])]))*180/PI
                                angleDict[(mtolist[1],mtolist[2])]=math.acos((distanceDict[(n,mtolist[1])]**2+distanceDict[(n,mtolist[2])]**2-distanceDict[(mtolist[1],mtolist[2])]**2)/(2*distanceDict[(n,mtolist[1])]*distanceDict[(n,mtolist[2])]))*180/PI
                                angleDict[(mtolist[2],mtolist[0])]=math.acos((distanceDict[(n,mtolist[2])]**2+distanceDict[(n,mtolist[0])]**2-distanceDict[(mtolist[2],mtolist[0])]**2)/(2*distanceDict[(n,mtolist[2])]*distanceDict[(n,mtolist[0])]))*180/PI
                        
                                #==============================================================================================================================
                                # Most of railway junction nodes have three directions. Siding lines always derived in an acute angle from the parent lines.
                                # 
                                # Traverse from the initial two directions and find another mutual junction node in the end. 
                                # The longer path should be kicked out, and get the siding line kneaded. 
                                #
                                #==============================================================================================================================
                                
                                anglelist=[]
                                directionlist=[]
                                for k,v in angleDict.iteritems():
                                    directionlist.append(k)
                                    anglelist.append(v)
                                minAngleDirection=directionlist[anglelist.index(min(anglelist))]
                                maxAngleDirection=directionlist[anglelist.index(max(anglelist))]
                                
                                for d in maxAngleDirection:
                                    if d in minAngleDirection:
                                        for sd in minAngleDirection:
                                            if sd!=d:
                                                sidingdirection=sd
                                
                                
                                bottomnode=n
                                topnode=sidingdirection
                                sidingnodelist=[n]
                                sidinglength=haversine(refnodes_coord_list[refnodes_index_dict.get(bottomnode)],refnodes_coord_list[refnodes_index_dict.get(topnode)])
                                
                                while node_fromto_dict.has_key(topnode) and len(node_fromto_dict[topnode])==2 and topnode not in stations and sidinglength<=10:
                                    sidingnodelist.append(topnode)
                                    cachenode=topnode
                                    for (nfrom,nto) in node_fromto_dict[cachenode]:
                                        if nto != bottomnode:
                                            topnode=nto
                                    bottomnode=cachenode
                                    sidinglength+=distance_mapper[(bottomnode,topnode)]
                                sidingnodelist.append(topnode)
                                
                                if topnode in stations or sidinglength>4:
                                    continue
                                
                                if sidinglength<=2:
                                    node_fromto_dict[n].remove((n,sidingdirection))
                                    node_fromto_dict[sidingdirection].remove((sidingdirection,n))
                        except:
                            continue
                        
                        
            if l%100==0:
                print("----->>"+str(l)+"/"+str(count))
            l=l+1
        stopt=time.time()
        print("----->>Performing switches processing ("+str(stopt-startt)+")<<-----")               
    
    def processAcuteRemains(thresholdvalue):
        startt=time.time()
        acutenodelist=[]
        allNodes=node_fromto_dict.keys()
        for n in allNodes:
            
            if node_fromto_dict.get(n) and len(node_fromto_dict[n])==2:
                try:
                    nodecoord=refnodes_coord_list[refnodes_index_dict.get(n)]
                    direction=(node_fromto_dict[n][0][1],node_fromto_dict[n][1][1])
                    directionCoords=((refnodes_coord_list[refnodes_index_dict.get(direction[0])][0], refnodes_coord_list[refnodes_index_dict.get(direction[0])][1]), (refnodes_coord_list[refnodes_index_dict.get(direction[1])][0], refnodes_coord_list[refnodes_index_dict.get(direction[1])][1]))
                    distance_12=haversine(directionCoords[0], directionCoords[1])
                    distance_1n=haversine(directionCoords[0],nodecoord)
                    distance_2n=haversine(directionCoords[1],nodecoord)
                    angle=math.acos(((distance_1n**2+distance_2n**2-distance_12**2)/(2*distance_1n*distance_2n)))*180/PI
                    if angle<thresholdvalue and n not in stations:
                        acutenodelist.append(n)
                        node_fromto_dict[direction[0]].remove((direction[0],n))
                        node_fromto_dict[direction[1]].remove((direction[1],n))
                except:
                    continue
        
        for an in acutenodelist:
            if node_fromto_dict.has_key(an):
                node_fromto_dict.pop(an)
        stopt=time.time()
        print("----->>Processing Acute Node Remains ("+str(stopt-startt)+")<<-----")
    
            
    def contraction(thresholddistance=0.5):
        startt=time.time()
        allNodes=node_fromto_dict.keys()
        
        for n in allNodes:
            neighbours=[0,0]
            if node_fromto_dict[n] and len(node_fromto_dict[n])==2:
                neighbours[0]=node_fromto_dict[n][0][1]
                neighbours[1]=node_fromto_dict[n][1][1]
                #print(neighbours[0],n,neighbours[1])
                distance1=distance_mapper.get((neighbours[0],n),0)
                distance2=distance_mapper.get((neighbours[1],n),0)
                
                if distance1+distance2<thresholddistance and neighbours[0]!=neighbours[1]:        
                    node_fromto_dict.pop(n)
              
                    if neighbours[0] in node_fromto_dict and (neighbours[0],n) in node_fromto_dict[neighbours[0]]:
                        node_fromto_dict[neighbours[0]].remove((neighbours[0],n))
                        
                    if neighbours[1] in node_fromto_dict and (neighbours[1],n) in node_fromto_dict[neighbours[1]]:
                        node_fromto_dict[neighbours[1]].remove((neighbours[1],n))
                        
                    if neighbours[0] in node_fromto_dict:#(set)
                        if (neighbours[0],neighbours[1]) not in node_fromto_dict[neighbours[0]]:
                            node_fromto_dict[neighbours[0]].append((neighbours[0],neighbours[1]))
                            distance_mapper[(neighbours[0],neighbours[1])]=distance1+distance2
                        
                    if neighbours[1] in node_fromto_dict:
                        if (neighbours[1],neighbours[0]) not in node_fromto_dict[neighbours[1]]:
                            node_fromto_dict[neighbours[1]].append((neighbours[1],neighbours[0]))
                            distance_mapper[(neighbours[1],neighbours[0])]=distance1+distance2
                    
            
                        
        stopt=time.time()
        print("Performing contraction ("+str(stopt-startt)+")")       
        
    
    def digitrounding(digit):    
        
        #Round stations
        startt=time.time()
        for s in stations:
            stations[s]=[stations[s][0],round(stations[s][1],digit),round(stations[s][2],digit)]
        stopt=time.time()
        print("Rounding stations ("+str(stopt-startt)+")")
    
        #Round refnode coords
        startt=time.time()
        for n in node_fromto_dict:
            
            refnodes_coord_list[refnodes_index_dict[n]]=(round(refnodes_coord_list[refnodes_index_dict[n]][0],digit),round(refnodes_coord_list[refnodes_index_dict[n]][1],digit))
            
            c1,c2=round(float(refnodes_coord_list[refnodes_index_dict[n]][0]),digit),round(float(refnodes_coord_list[refnodes_index_dict[n]][1]),digit)#c1--lat, c2--lon
            
            if (c1,c2) not in approxCoord_map:
                approxCoord_map[(c1,c2)]=int(row[0])         #row[0]--coordidfor row in spamreader:
                refnodes_index_dict[int(row[0])]=len(refnodes_coord_list)
                refnodes.append(int(row[0]))
                refnodes_coord_list.append((c1,c2))
                refnode_mapper[int(row[0])]=int(row[0])
                
            else:
                refnode_mapper[int(row[0])]=approxCoord_map[(c1,c2)]
                    
        stopt=time.time()
        print("Rounding refnode coords ("+str(stopt-startt)+")")
    
        #Round refnode segments
        startt=time.time()
        with codecs.open(FOLDER+FILE+'_waysegments.csv', 'rb',encoding='utf-8') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
        waysegmentlist=set()
        for n in node_fromto_dict:
            for segment in node_fromto_dict[n]:
                waysegmentlist.add(segment)
        for segment in waysegmentlist:
            if refnode_mapper.get(int(segment[0])) is None:
                pass
            else:
                mfrom=refnode_mapper[int(segment[0])]
                mto=refnode_mapper[int(segment[1])]
                
                if mfrom not in node_fromto_dict:
                    node_fromto_dict[mfrom]=[]
        
                if mto not in node_fromto_dict:
                    node_fromto_dict[mto]=[]
    
                distance=haversine.hav_distance(refnodes_coord_list[refnodes_index_dict[mfrom]][0],refnodes_coord_list[refnodes_index_dict[mfrom]][1], refnodes_coord_list[refnodes_index_dict[mto]][0],refnodes_coord_list[refnodes_index_dict[mto]][1])
    
                distance_mapper[(mfrom,mto)]=distance
                distance_mapper[(mto,mfrom)]=distance
    
                if (mfrom,mto) not in node_fromto_dict[mfrom] and mfrom!=mto:
                    node_fromto_dict[mfrom].append((mfrom,mto))

                if (mto,mfrom) not in node_fromto_dict[mto] and mfrom!=mto:
                    node_fromto_dict[mto].append((mto,mfrom))
    
        stopt=time.time()
        print("Rounding refnode segments ("+str(stopt-startt)+")")