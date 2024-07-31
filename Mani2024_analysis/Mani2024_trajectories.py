# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 11:27:55 2024

@author: RonjaEbnerTheOceanCl

Part 1
1. polyline describing the center of the river
2. add river kilometers from first point (river_km)
3. add riverwidths
4. safe as shp file for future operations
"""
#%% libraries
import os
import geopandas as gpd

import Mani2024_functions as fnc
import Mani2024_Centerline as cl

from geopy import distance
from pyproj import Transformer
from shapely.ops import nearest_points
from shapely.geometry import Point

#%% definitions
center_width = 1/3


#%% data
center_coords       = cl.center_coords()
CenterLineString    = cl.centerline()
transformer = Transformer.from_crs('EPSG:4326', 'EPSG:24047', always_xy=True) 
#%% preparing the center line
# add information about
#   distance to river mouth
#   width  (based on interpolation of Thomas' data)
#   corvature

list_riverkm= [0]
list_width = [940.3]
list_geometry = [Point(center_coords[-1])]
list_curve = [0]
tmp=0
for KK in range(1,len(center_coords)):
    kk = len(center_coords) -KK
    tmp = fnc.river_km(center_coords, kk, tmp)
    list_riverkm.append(tmp)
    list_width.append(fnc.river_width(tmp))
    list_geometry.append(Point(center_coords[kk]))
    list_curve.append(fnc.get_bent(kk, center_coords))
    
norm      = max(max(list_curve), abs(min(list_curve)))
curv_norm = [i/norm for i in list_curve]

d = {
    'geometry'      : list_geometry,
    'river_km'      : list_riverkm,
    'width'         : list_width,
    'curvature'     : curv_norm}

CenterLine = gpd.GeoDataFrame(d, crs="EPSG:4326")
#safe as shp
CenterLine.to_file('../01_alteredDATA/CenterLineChaoPhraya_curve_new.shp')

#%% adding floater information
# Get all files in folder

directory   = "../00_rawData/"
arr         = os.listdir(directory) #list of files in directory
NAMES       = []
count       = 0
pos_correct = 1


for n in arr:
    if '.shp' in n:
        NAMES.append(n)
        
for nn in NAMES:
    # load the trajectory
    print(nn)
    trajectory = gpd.read_file(directory + nn)
    
    # get information for each point on the line in comparison to "CenterLine"
# 	1. distance to polyline
# 	2. river km (of projected point)
# 	3. left or right of polyline
# 	4. up or down movement ( river m decreasing or increasing)
    dist_list       = []
    river_km_list   = []
    width_list      = []
    position_list   = []
    direction_list  = []
    for kk in range(len(trajectory)):
        # test for spatial accuracy
        if trajectory["spat. acc."].iloc[kk]> 10:
            dist_list.append(-9999)
            river_km_list.append(-9999)
            width_list.append(-9999)
            position_list.append(-9999)
            direction_list.append(-9999)
        else:
            # get point
            point = trajectory["geometry"].iloc[kk]
            # get virtual point on line
            point_on_line   = nearest_points(CenterLineString, point)[0]
            
            # 1 distance to polyline
            dist= ((distance.distance(fnc.switchLonLat(point),
                                      fnc.switchLonLat(point_on_line))).km)*1000
            
            
            # 2 get the two closest points on centerline
            list_of_distances = [distance.distance(fnc.switchLonLat(center_point),
                                                  fnc.switchLonLat(point_on_line)).km 
                                 for center_point in center_coords]
            min0 = min(list_of_distances)
            index0 = -list_of_distances.index(min0)
            list_of_distances[-index0]= 9999
            min1 = min(list_of_distances)
            index1 = -list_of_distances.index(min1)
            
            # 3 get attributes 
            ## get river_km
            river_km=(CenterLine["river_km"].iloc[index0]+ min0)
            
            ## get width
            slope = ((CenterLine["width"].iloc[index1]-CenterLine["width"].iloc[index0])/
                     (CenterLine["river_km"].iloc[index1]-CenterLine["river_km"].iloc[index0]))
            width=(slope*min0 + CenterLine["width"].iloc[index0])
            # check if distance is alright
            if dist > 0.75 * width: # this allows for a 25% error in the river width
                dist = -9999
                        
            # 5 get direction
            if kk >1:
                
                change   = (river_km - river_km_list[-1])*1000
                accuracy = trajectory["spat. acc."].iloc[kk]
                thresh = 1e-9
                if abs(change) > accuracy:
                    if change>0:
                        direction = 1
                    else:
                        direction = -1
                else:
                    direction = 0
            else:
                direction = 0
                
            # # 4 analyse position
            # ## side or center

            ## left or right
            ### to have this right I need to identify the index with the lower river_km
            ind0 = CenterLine[CenterLine["river_km"] == min(CenterLine["river_km"].iloc[index0], 
                                                        CenterLine["river_km"].iloc[index1])].index[0] 
            ind1 = CenterLine[CenterLine["river_km"] == max(CenterLine["river_km"].iloc[index0], 
                                                        CenterLine["river_km"].iloc[index1])].index[0] 
            # taking the position from the function, but assign 0 when the distance is smaller than 0 
            pos =fnc.where_it_is(CenterLine, ind0, ind1, point)*(dist >10)
            
            # 6 append all lists
            dist_list.append(dist)
            river_km_list.append(river_km)
            width_list.append(width)
            position_list.append(pos)
            direction_list.append(direction)
        
    #ADD information to dataframe
    trajectory.insert(4, "distance",  dist_list     , True)
    trajectory.insert(4, "river_km",  river_km_list , True)
    trajectory.insert(4, "width"   ,  width_list    , True)
    trajectory.insert(4, "position",  position_list , True)
    trajectory.insert(4, "direction", direction_list, True)
    
    #DELETE rows with non-valid distance
    trajectory = trajectory.drop(trajectory[trajectory["distance"]== -9999].index)
    
    #SAFE altered DataFrames
    if len(trajectory.index) > 10:
        trajectory.to_file('../01_alteredData/Mani2024_' + nn[0:33] + '.shp')
