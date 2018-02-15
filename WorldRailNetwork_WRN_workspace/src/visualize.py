#!/usr/bin/python
# -*- coding: UTF-8 -*-



'''
Created on Jan 17, 2017

@author: hegxiten
'''

from mpl_toolkits.basemap import Basemap
import csv
import matplotlib.pyplot as plt
import networkx as nx
import time
import codecs
import sys

default_encoding='utf-8'
if sys.getdefaultencoding()!=default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

PI=3.14159265358

def visualizewayNetwork(FOLDER,FILE,CONCURRENCYVAL,GLOBALROUNDINGDIGITS):
    nodes={}
    stations={}

    minlat,minlon,maxlat,maxlon=90,180,-90,-180
    
    #Load stations
    startt=time.time()
    with codecs.open(FOLDER+FILE+'_stations.csv', 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
        for row in spamreader:
            stations[int(row[0])]=[row[1],float(row[2]),float(row[3])]
    stopt=time.time()
    print("Loading stations ("+str(stopt-startt)+")")


    #Load nodes
    startt=time.time()
    with codecs.open(FOLDER+FILE+'_nodes.csv', 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
        for row in spamreader:
            nodes[int(row[0])]=[row[1],float(row[2]),float(row[3])]

            if float(row[2])<minlat:
                minlat=float(row[2])
            if float(row[2])>maxlat:
                maxlat=float(row[2])
            if float(row[3])<minlon:
                minlon=float(row[3])
            if float(row[3])>maxlon:
                maxlon=float(row[3])



    stopt=time.time()
    print("Loading nodes ("+str(stopt-startt)+")")
    
    print(minlat,minlon,maxlat,maxlon)
    centlon,centlat=(maxlon-minlon)/2,(maxlat-minlat)/2

    #map = Basemap(projection='stere',lon_0=centlon, lat_0=centlat,lat_ts=centlat, llcrnrlon = minlon, llcrnrlat = minlat,urcrnrlon = maxlon, urcrnrlat = maxlat,rsphere=6371200.,resolution='l',area_thresh=10000)

    map = Basemap(projection='merc',lon_0=centlon, lat_0=centlat,lat_ts=centlat, llcrnrlon = minlon, llcrnrlat = minlat,urcrnrlon = maxlon, urcrnrlat = maxlat,rsphere=6371200.,resolution='l')

    map.drawcoastlines(linewidth=0.25)
    map.drawcountries(linewidth=0.25)
    map.fillcontinents(color="coral",lake_color="aqua")

    

    #Load links
    startt=time.time()
    with codecs.open(FOLDER+FILE+'_links.csv', 'rb',encoding='utf-8') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='$')
        header=spamreader.next()
        for row in spamreader:
            mfrom=int(row[0])
            mto=int(row[1])
            dist=float(row[header.index('distance')])

            lats=[nodes[mfrom][1],nodes[mto][1]]
            lons=[nodes[mfrom][2],nodes[mto][2]]
            
            x, y = map(lons, lats) # forgot this line 
    
            map.plot(x, y, '-', markersize=0.1,  color="b")
            '''labels=[unicode(str(mfrom),"utf-8")]
            print(labels)
            #ploting labels
            for xpt, ypt, label in zip(x, y, labels):
                plt.text(xpt, ypt, label, fontsize=10)'''
#------------------------------------------------------------------------------ 

    print(len(nodes))
    count=0
    for n in nodes:
        lats=[nodes[n][1]]
        lons=[nodes[n][2]]
        
        x, y = map(lons, lats) # forgot this line s
        
        if n in stations:
            count+=1
            map.plot(x, y, '.', markersize=5,  color="r")
            labels=[unicode(stations[n][0],"utf-8")]
            #print(labels)
            #ploting labels
            for xpt, ypt, label in zip(x, y, labels):
                plt.text(xpt, ypt, label, fontsize=10)
                
    print ("stations amount:"+str(count))

    plt.show()


if __name__ == '__main__':
    print ("===you're in test mode of visualize.py===")
    FILE='illinois-latest.osm.pbf'
    FOLDER='/home/hegxiten/workspace/data/'+FILE+'/'
    CONCURRENCYVAL=4
    GLOBALROUNDINGDIGITS=5
    
    visualizewayNetwork(FOLDER, FILE, CONCURRENCYVAL, GLOBALROUNDINGDIGITS)
    print ("===test mode of visualize.py terminated===")
