# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 13:56:02 2024

@author: RonjaEbnerTheOceanCl
"""

import pandas as pnd
import numpy as np

import geopandas as gpd
from geopandas import GeoDataFrame

from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
import shapely.ops as sp_ops
import rasterio
from rasterio.transform import Affine

from geopy import distance

import os

from pyproj import Transformer

def safe_to_list(av_dist, index, sgmnt_wd, center_width,
                 sgmnt_mid,sgmnt_rgt,sgmnt_lft,sgmnt_avdist ):
    '''
    adding the datapoint to either the left, middle or right section
    '''
    width = sgmnt_wd[index]
    if abs(av_dist) < 0.5*center_width*width:
        sgmnt_mid[index] +=1

    elif np.sign(av_dist)>0:
        sgmnt_lft[index] +=1

    else:
        sgmnt_rgt[index] +=1

    sgmnt_avdist[index] +=av_dist
    
    
def switchLonLat(data):
    '''
    the coordinates are in the wrong order for the distance function to read
    '''
    point = Point(data)
    s_x = point.y 
    s_y = point.x
    point_switched= (s_x, s_y)
    
    return point_switched
    
def river_width(river_m):
    '''
    The formula to descripte the width of the rivers is based on measurements
    conducted by Thomas Mani. It describes the river width with R² > 0.6 and 
    increasing accuracy for higher river kilometer
    '''
    width = 940.29*np.exp(-0.024*river_m)
    
    return width


def river_km(DATA, kk, prev):
    '''
    This functions adds the distance to river mouth and width of the river
    '''
    point0  = switchLonLat(DATA[kk-1])
    point1  = switchLonLat(DATA[kk])
    
    dist    = distance.distance(point0, point1).km
    river_km = prev + dist

    return river_km

def where_it_is(line, index1, index2, point):
    aX = line["geometry"].iloc[index1].x
    aY = line["geometry"].iloc[index1].y
    
    bX = line["geometry"].iloc[index2].x
    bY = line["geometry"].iloc[index2].y
    
    cX = point.x
    cY = point.y

    val = ((bX - aX)*(cY - aY) - (bY - aY)*(cX - aX))
    
    thresh = 1e-9
    if val >= thresh:
        return -1
    elif val <= -thresh:
        return +1
    else:
        return 0

def where_it_is_curve(a, b, c):
    # https://stackoverflow.com/questions/1560492/how-to-tell-whether-a-point-is-to-the-right-or-left-side-of-a-line
    factor = 1000000

    val= (( int((b.y)*factor) - int((a.y)*factor))*(int((c.x)*factor) - int((a.x)*factor))
         - (int((b.x)*factor) - int((a.x)*factor))*(int((c.y)*factor) - int((a.y)*factor)))
    
    return val

def get_bent(index, line_as_list):
    """
    This function gets the difference between left and right curves by
    comparing the distance between two points that have been created on each
    of the linesting
    """
    if index==0 or index ==len(line_as_list)-1:
         curve = 0
    else:
        
        # the three Points describe the curve segment       
        Point_A = Point(line_as_list[index -1])
        Point_B = Point(line_as_list[index   ])
        Point_C = Point(line_as_list[index +1])
        
        #point A and C for am line, B sits either left, right or on this line
        curve = where_it_is_curve(Point_A, Point_C, Point_B )        
        
    return curve