# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:48:03 2024
fixed on Fri May 31 11:19:05 2024

@author: RonjaEbnerTheOceanCl

Data needed to run this script

"""
#%% libraries
import os
import numpy as np
import geopandas as gpd
import shapely.ops as sp_ops

import Mani2024_functions as fnc
import Mani2024_Centerline as cl

from shapely.geometry import LineString
from pyproj import Transformer


#%% data
center_coords       = cl.center_coords()
CenterLineString    = cl.centerline()
transformer = Transformer.from_crs('EPSG:4326', 'EPSG:24047', always_xy=True) 

#%%

# Get all files in folder

directory   = "../01_alteredData/"
arr         = os.listdir(directory) #list of files in directory
NAMES       = []
count       = 0
IDs         = []
# delete all files with aux.xml ending
CenterLine= gpd.read_file(directory + "CenterLineChaoPhraya_curve_new.shp")
# loading all trajectories into a dictionary of dataframes
print("store data in dict")
TRAJECTORIES = {'tracker_id':"DataFrame"}
for n in arr[:-4]:
    if (('.shp' in n) and ('Mani' in n)):
        NAMES.append(n)
        currentID = n[-12:-4]
        print("... tracker " + currentID)
        IDs.append(currentID)
        trajectory = gpd.read_file(directory + n)
        TRAJECTORIES[currentID] = trajectory
print("done") 
   
#%%     
## create the segment lists
sgmnt_count     = 3
center_width    = 1/sgmnt_count
segment_length  = 0.5   #km


str_dir = ['undefined', 'up' , 'down']
for direction in [-1, 1]:
    
    sgmnt_nr = list(range(int(CenterLine.river_km.iloc[-1]/segment_length)))
    sgmnt_lw = [x*segment_length for x in sgmnt_nr] #lower  limit
    sgmnt_hg = [x+segment_length for x in sgmnt_lw] #higher limit
    
    # assign the width in the midle of the segment
    sgmnt_wd = [fnc.river_width(sgmnt_lw[x]+0.5*segment_length) for x in sgmnt_nr]
    
    # empty lists to sort  the the data in
    sgmnt_lft= [0 for x in sgmnt_lw]
    sgmnt_mid= [0 for x in sgmnt_lw]
    sgmnt_rgt= [0 for x in sgmnt_lw]
    sgmnt_avdist= [0 for x in sgmnt_lw]
    
    # counting variables
    sum_dist    = 0
    sum_n       = 0
    for nn in NAMES:
        
        # in this loop we analyse the different trajectories and sort the
        # information into the lists that then later will be compiled into a
        # a geodatabase that we can can read with qgis
        
        # load the trajectory
        trajectory = gpd.read_file(directory + nn)

        # sort for the movement direction
        # up(+1) or down (-1)
        data = trajectory.loc[trajectory.direction == direction]
        try:
           index_prv   = int(data.river_km.iloc[0]/segment_length)
        except:
           print("DataFrame too small")
           
        
        for kk in range(len(data)):
            
            if data['spat. acc.'].iloc[kk] > 10:
                continue
            
            
            r_km  = data.river_km.iloc[kk]
            index = int(r_km/segment_length)
            dist  = data['distance'].iloc[kk]*data.position.iloc[kk]
            
            # check if index is new
            jump_test = index-index_prv
            if jump_test == 0:            
                # add the information to the counting variables
                sum_dist += dist
                sum_n    += 1
    
            elif np.sign(jump_test)== -direction:
                # the floater is moving into the same direction as before
                if abs(jump_test)>1:
                    # if jump is larger than 1, then we need to interpolate
                    # we only interpolate if the jump is in the direction of the 
                    # movement
                    av_dist = sum_dist/sum_n
                    #print("average distance is " + str(av_dist))
                    fnc.safe_to_list(av_dist, index, sgmnt_wd, center_width,
                                     sgmnt_mid,sgmnt_rgt,sgmnt_lft,sgmnt_avdist )
                    # get slope
                    slope = ((data['distance'].iloc[kk-1] - data['distance'].iloc[kk])/
                             (data.river_km.iloc[kk-1] - data.river_km.iloc[kk]))
                    
                    diff  = data.river_km.iloc[kk-1] - sgmnt_lw[index_prv]*0.5
                    
                    for x in range(abs(jump_test)):
                        # it is possible that more than 1 segment gets skipped
                        interp_dist = slope*(segment_length*x + diff)
                        fnc.safe_to_list(av_dist, index, sgmnt_wd, center_width,
                                         sgmnt_mid,sgmnt_rgt,sgmnt_lft,sgmnt_avdist )
                        diff = 0
                else:
                    # trajer moves to the next segment
                    # information is added
                    av_dist = sum_dist/sum_n
                    fnc.safe_to_list(av_dist, index, sgmnt_wd, center_width,
                                     sgmnt_mid,sgmnt_rgt,sgmnt_lft,sgmnt_avdist )
                    
                    sum_dist = dist
                    sum_n    = 1
                        
            else:
                # the floater has moved into the opposite direction
                # and the counting starts again
                av_dist = sum_dist/sum_n
                #print("average distance is " + str(av_dist))
                fnc.safe_to_list(av_dist, index, sgmnt_wd, center_width,
                                 sgmnt_mid,sgmnt_rgt,sgmnt_lft,sgmnt_avdist )
                sum_dist = dist
                sum_n    = 1
                
            index_prv = index
            
        
        print(nn)  
    
    
    # https://gis.stackexchange.com/questions/346018/adding-points-every-x-distance-along-a-linestring
    Dist             = segment_length*0.5*1000 
    add_distance     = segment_length *1000
    CenterLineString = sp_ops.transform(transformer.transform,
                                        LineString(center_coords))
    
    sgmnt_geometry = []
    while Dist < CenterLineString.length:
       new_point = CenterLineString.interpolate(Dist)
       sgmnt_geometry.append(new_point)
       Dist += add_distance ## add more
       
    sgmnt_position = []
    for ii in range(len(sgmnt_nr)):
        total  = sgmnt_lft[ii]+sgmnt_mid[ii]+sgmnt_rgt[ii]
        if total >0:
            av_pos = sgmnt_avdist[ii]/total
        else:
            av_pos = 0
        sgmnt_position.append(av_pos)
        
    sgmnt_nr = sgmnt_nr[::-1] 
    sgmnt_lw = sgmnt_lw[::-1]  
    sgmnt_hg = sgmnt_hg[::-1] 
    sgmnt_lft = sgmnt_lft[::-1] 
    sgmnt_mid = sgmnt_mid[::-1] 
    sgmnt_rgt = sgmnt_rgt[::-1] 
    sgmnt_wd = sgmnt_wd[::-1] 
    sgmnt_position = sgmnt_position[::-1] 
        
    d = {
        'geometry'      : sgmnt_geometry,
        'number'        : sgmnt_nr,
        'lower_lim'     : sgmnt_lw,    
        'upper_lim'     : sgmnt_hg,
        'cnt_left'      : sgmnt_lft,
        'cnt_mid'       : sgmnt_mid,
        'cnt_right'     : sgmnt_rgt,
        'width'         : sgmnt_wd,
        'av_pos'   : sgmnt_position}
    
    analysed_CenterLine = gpd.GeoDataFrame(d, crs='EPSG:24047')
    #safe as shp
    # -1 :downstream; +1 :upstream
    segments= ['500', '1000']#m
    name = ('../02_Results/SegmentedCenterLine_' 
            + str(int(segment_length*1000)) + "_" 
            + str_dir[direction] + "_hotline_10mSpatAcc.shp")
    analysed_CenterLine.to_file(name)
