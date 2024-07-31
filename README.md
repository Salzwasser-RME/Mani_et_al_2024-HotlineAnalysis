# Mani_et_al_2024-Hotline

 This code was used to analyze the position of the floaters along
the main river

_____________________________________________________________________
# DATA STRUCTURE
_____________________________________________________________________

## 00_rawData
contains the trajectory of each drifter as a shp file as well as
the river centerline.

## 01_alteredData
contains the trajectories for the drifters that have a sufficient
amount of consecutive datapoints as shp files. for each datapoint
the following information has been added
- direction of the movement
- distance to river mouth (based on river center line)
- width of river
- distance to river center line

## 02_Results
Contains the final shp file that was used to create figure 4A&B

## Mani2024_Analysis
Contains the script needed to create the files in '01_alteredData'
and '02_Results'

_____________________________________________________________________
# Scripts
_____________________________________________________________________

## Mani2024_trajectories
This scripts adds information to the raw trajectory files by 
comparing the recorded locations of the floaters to the centerline
of the river.

## Mani2024_hotline
This script analyses the partial trajectories and records the
different positions for up and downstream movement.

## Mani2024_statistics
This script analyses the whether there is a trend for the drifters
to be on the inside or the outside of the curve

## Mani2024_functions
functions needed for the 3 scripts are defined here
