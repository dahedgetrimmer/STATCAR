"""
Created on Fri Oct 11 19:05:14 2024

NASCAR Cup Series Race Data Scraper (Version 2)
Author: Jared Revier
Date: 10/09/2024
Last Updated: 10/17/2024


Objective:
1.) Gather individual race info and the race data for all drivers for any given race 
    via REST API.

2.) Using Pandas, organize the data into DataFrames then clean the data.

3.) Convert DataFrames into .csv files and upload the data into a SQL database.
    
"""


import requests
import numpy as np
import pandas as pd
import time
import os



def raceID_scraper(year):
    print('Scraping Cup Series Race IDs...')
    
    
    #Eventually this will loop through and compile a list of race ID's for an entire season. 
    #That list will be used to loop through and gather a seasons worth of data.
    # race_id = []
    
    
    seasoninfo_link = f'https://cf.nascar.com/cacher/{year}/race_list_basic.json'
    seasoninfo_response = requests.get(seasoninfo_link)
        
    if seasoninfo_response.status_code == 200:
            season_info = seasoninfo_response.json()
    else:
        print('Failed to connect...')
    
    #remove Xfinity Series (series_2) and Truck Series (series_3) data (for now) 
    del season_info['series_3']
    del season_info['series_2']

    for i in range(len(season_info['series_1'])):
        #next 2 lines for looping through an entire season.
        # id = season_info['series_1'][i]['race_id']
        # race_id.append(id)
    
        race_id = season_info['series_1'][i]['race_id']
    #Print race_id if you want to see the list of races
    print(race_id)
    print('Race ID list has been compiled!')
    return race_id
    


year = 2022
print(f'Initailizing raceID_scraper for the {year} season...')

race_id = raceID_scraper(year)  


'''
*******************************************************************************
MAKE IT LOOP THROUGH THE LIST OF RACE IDS
*******************************************************************************
'''


def racedata_scraper(race_id, year):
    
    lapdata_link = f'https://cf.nascar.com/cacher/{year}/1/{race_id}/lap-times.json' 
    raceinfo_link = f'https://cf.nascar.com/cacher/{year}/1/{race_id}/weekend-feed.json'
    
    print(lapdata_link)
    time.sleep(1)
    
    lapdata_response = requests.get(lapdata_link)
    raceinfo_response = requests.get(raceinfo_link)
    
    time.sleep(1)
    
    if lapdata_response.status_code and raceinfo_response.status_code == 200:
       lapdata = lapdata_response.json()
       raceinfo = raceinfo_response.json()
    else:
        print('Failed to connect...')
    
    del lapdata['flags']
        
   #Print lapdata and raceinfo if you want to see what is contained in the JSON arrays
        
   #print(lapdata)
   #print(raceinfo) 
    
    return lapdata, raceinfo

lapdata, raceinfo = racedata_scraper(race_id, year)


def race_df(raceinfo):
    for key in raceinfo.keys():
        print(key)
    
    race_info = pd.DataFrame(raceinfo['weekend_race'])
    
    
    for i in range(len(race_info)):
        print(race_info.loc[i])
    
    race_info = race_info.drop(columns = ['date_scheduled',
                                          'qualifying_date',
                                          'tunein_date',
                                          'pit_reports', 
                                          'radio_broadcaster',
                                          'television_broadcaster',
                                          'satellite_radio_broadcaster',
                                          'master_race_id',
                                          'inspection_complete',
                                          'playoff_round',
                                          'race_purse',
                                          'race_comments',
                                          'attendance',
                                          'results',
                                          'caution_segments',
                                          'race_leaders',
                                          'infractions',
                                          'schedule',
                                          'stage_results'])

#'timing_run_id' is not part of the 2022 race information data.
#Need to add a loop to check for these keys and skip any missing keys
#better yet, loop through the keys that I explicitly want, drop the rest.
    
    #clean up the dates data
    race_info['race_date'] = [x.split("T")[0] for x in race_info['race_date']]
    
    for i in range(len(race_info)):
        print(race_info.iloc[i])
    
    return race_info


raceinfo_df = race_df(raceinfo)




def create_roster(race_id, year):
    
    raceID = raceinfo['weekend_race'][0]['race_id']

    driver_roster = pd.DataFrame(lapdata['laps'][:])
    driver_roster = driver_roster.drop(columns = ['Laps', 'RunningPos'])
    
    rosterlength = len(driver_roster)
    race_id = pd.Series(np.full((rosterlength), raceID), name='race_id')
    driver_roster = pd.concat([driver_roster, race_id], axis=1)
    
    #clean up the column names
    driver_roster.columns = [x.lower().replace("full","driver_") \
                             .replace("number", "car_number") \
                             .replace("nascardriverid", "driver_id") \
                             for x in driver_roster.columns]
    
    #clean up the names in the driver_name column
    driver_roster['driver_name'] = [x.replace(" #","").replace(r" (P)","").replace(r"(i)","") \
                                    .replace(r"* ","") for x in driver_roster['driver_name']]
    
    #driver_roster.set_index(['driver_id', 'race_id'], inplace=True)
    
    print(driver_roster)
    
    return driver_roster

roster_df = create_roster(race_id, year)




def driver_lapdata(raceinfo, lapdata):
    
    #need to make this loop through each driver in the race.
    for i in range(len(lapdata['laps'])):
        name = lapdata['laps'][i]['FullName']
        #get the total laps ran in the race
        racelength = raceinfo['weekend_race'][0]['actual_laps']
        
        #get the race id number
        raceID = raceinfo['weekend_race'][0]['race_id']
        
        #create a series to represent the lap count
        laps = pd.Series(np.array(range(racelength+1)), name='lap')
        
        #print(laps)
        
        
        #create a series containing the race id number and driver id number.
        #the number of rows will be: racelength + 1
        
        race_id = pd.Series(np.full((racelength+1), raceID), name='race_id')
        
        driverID = lapdata['laps'][i]['NASCARDriverID']
        driver_id = pd.Series(np.full((racelength+1), driverID), name='driver_id')
        
        
        '''
        *************************************************************************
        NOTE: The index of the driver id and lap_data variable call must be the 
              same or the data will not match up with the correct driver!!!
        *************************************************************************        
        '''
        
        #need to drop the 'Lap' column from the df. If left in, concat would cause
        #data types to change
        lap_data = pd.DataFrame(lapdata['laps'][i]['Laps']) #READ THE NOTE ABOVE
        lap_data = lap_data.drop(columns='Lap')
        
        #Is it working properly? Print the df
        #print(lap_data)
        
        #if a driver DNF'd, the position data will be missing from the lap_data df
        #after their last recorded lap (i.e. the data will be nan)
        #replace nan and change data type to int
        lap_data['RunningPos'] = lap_data['RunningPos'].fillna(0)
        lap_data['RunningPos'] = lap_data['RunningPos'].astype(int)
        
        
        #if the driver has DNF'd, change their position value to the last recorded position
        #df.loc[row_indexer, "col"] = values to iterate through df rows
        for j in range(len(lap_data['RunningPos'])):
            if lap_data.loc[j, 'RunningPos'] == 0 and lap_data.loc[j-1, 'RunningPos'] > 0:
                lap_data.loc[j, 'RunningPos'] = lap_data.loc[j-1, 'RunningPos']
                #print(lap_data)
        
        #if the driver has DNF'd the LapTime and LapSpeed after their last recorded lap
        #will be nan. Also, LapSpeed will be a str data type (not sure why)
        #replace all nan from df and convert LapSpeed to float data type
        lap_data['LapTime'] = lap_data['LapTime'].fillna(0.000)
        lap_data['LapSpeed'] = lap_data['LapSpeed'].fillna(0.000)
        lap_data['LapSpeed'] = lap_data['LapSpeed'].astype(float)
        
        #add the lap count column to the front of the df
        #set df index as driver and race ID numbers
        lap_data = pd.concat([race_id, driver_id, laps, lap_data], axis=1, join='outer')
        
        #clean up column names
        lap_data.columns = [x.replace("LapTime", "lap_time").replace("LapSpeed", "lap_speed") \
                            .replace("RunningPos", "running_pos")\
                            for x in lap_data.columns]
        
        
        
        #Are you satisified with the final df?
        #Check it out
        print(lap_data)
        
        return lap_data, name
    
    
    
driver_data, driver = driver_lapdata(raceinfo, lapdata)
#print(driver_data)



