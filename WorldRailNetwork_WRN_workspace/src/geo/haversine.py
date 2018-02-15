#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on Jan 9, 2017

@author: hegxiten
'''

import math

def hav_distance(originlon,originlat, destinationlon,destinationlat):
    """ Haversine formula to calculate the distance between two lat/lon points on a sphere """
    """ The order of lon, lat doesn't matter"""

    radius = 6371 # FAA approved globe radius in km

    dlat = math.radians(destinationlat-originlat)
    dlon = math.radians(destinationlon-originlon)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(originlat)) \
        * math.cos(math.radians(destinationlat)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    # Return distance in km
    return d

def main():
    print ("we are in %s"%__name__)

if __name__=="__main__":
    main()
    