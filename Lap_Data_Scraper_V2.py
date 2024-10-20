"""
*******************************************************************************
Created on October 09, 2024

NASCAR Cup Series Race Data Scraper (Version 2)
Author: Jared Revier
Date: 10/09/2024 (Completed the functions used to create each df')
                  
Updated: 10/17/2024 (Added a loop to the "driver_lapdata" function )

Updated: 10/19/2024 (Added the df to csv conversion and storage path to
                     the "driver_lapdata" function.) 


Objective:
1.) Gather individual race info and the race data for all drivers for any given 
    race via REST API.

2.) Using Pandas, organize the data into DataFrames then clean the data.

3.) Convert DataFrames into .csv files and upload the data into a SQL database.
    

    
This program is set up to only gather NASCAR Cup Series data. If one desired to
gather Truck or Xfinity Series data, adjust which series are dropped in the 
"raceID_scraper" function.

Also, NASCAR only has race data from 2022 to Present. Anything prior to 2022 is
no longer available to be gathered through this API scraper.
*******************************************************************************    
"""


import requests
import numpy as np
import pandas as pd
import time
import os

year = 2022
  

    

'''
*******************************************************************************
This function serves to collect the race ID number of every race in a given
season.
*******************************************************************************
'''


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
    



print(f'Initailizing raceID_scraper for the {year} season...')


race_id = raceID_scraper(year)  



'''
*******************************************************************************
This function stores the JSON arrays that contain the race information and 
lap data for a race based on which race ID number is provided to the function.
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



'''
*******************************************************************************
This function serves to gather relevant information about the race that is
being scraped.
*******************************************************************************
'''


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



'''
*******************************************************************************
This function creates a df that is a roster of all drivers that participated in
this race. The data includes the driver name, their driver ID number, the 
race ID number, car number, and car manufacturer.
*******************************************************************************
'''

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



'''
*******************************************************************************
This section loops through each driver in the race and creates a df of their
lap time, lap average speed, and position. The df will also include the 
race and driver id number as part of each df.
*******************************************************************************
'''


for i in range(len(lapdata['laps'])):
    
    def driver_lapdata(raceinfo, lapdata, i):
        
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
        ******************************************************************************
        NOTE: The index of the driver id and lap_data variable call must be the 
              same!!! Otherwise the data will not match up with the correct driver!!!
        ******************************************************************************
        '''
        
        #need to drop the 'Lap' column from the df. If left in, concat would cause
        #data types to change
        lap_data = pd.DataFrame(lapdata['laps'][i]['Laps']) #READ THE NOTE ABOVE
        lap_data = lap_data.drop(columns='Lap')
        
        
        #compile everything into a single df
        lap_data = pd.concat([race_id, driver_id, laps, lap_data], axis=1)
        
        #Is it working properly? Print the df
        #print(lap_data)
        
        #if a driver DNF'd, the position data will be missing from the lap_data df
        #after their last recorded lap (i.e. the data will be nan)
        #replace nan and change data type to int
        lap_data['RunningPos'] = lap_data['RunningPos'].fillna(0)
        lap_data['RunningPos'] = lap_data['RunningPos'].astype(int)
        
        
        #if the driver has DNF'd, change their position value to the last recorded position
        #df.loc[row_indexer, "col"] = values to iterate through df rows
        for j in range(1, len(lap_data['RunningPos'])):
            if lap_data.loc[j, 'RunningPos'] == 0 and lap_data.loc[j-1, 'RunningPos'] > 0:
                lap_data.loc[j, 'RunningPos'] = lap_data.loc[j-1, 'RunningPos']
                #print(lap_data)
        
        #if the driver has DNF'd the LapTime and LapSpeed after their last recorded lap
        #will be nan. Also, LapSpeed will be a str data type (not sure why)
        #replace all nan from df and convert LapSpeed to float data type
        lap_data['LapTime'] = lap_data['LapTime'].fillna(0.000)
        lap_data['LapSpeed'] = lap_data['LapSpeed'].fillna(0.000)
        lap_data['LapSpeed'] = pd.to_numeric(lap_data['LapSpeed'], errors='coerce').fillna(0.000).astype(float)
        
        
        
        #clean up column names
        lap_data.columns = [x.replace("LapTime", "lap_time").replace("LapSpeed", "lap_speed") \
                           .replace("RunningPos", "running_pos")\
                            for x in lap_data.columns]
    
        
        
       #check if it is working 
       #print(lap_data)
       
       #return the df
        return lap_data
        
    
    #call the function to create a df of each drivers lap data for a given race
    #take the returned df with the drivers lap data and convert it into a 
    #.csv file store in desired directory
    
    driverdata_df = driver_lapdata(raceinfo, lapdata, i)
    #print(driverdata_df)
    
    race_name = raceinfo_df['race_name'].iloc[0]
    race_name = race_name.replace(" ", "_")
    
    driver_name = roster_df['driver_name'].iloc[i]
    driver_name = driver_name.replace(" ", "_")
    
    #the season year is stored as an int dtype, covert to str
    race_season = raceinfo_df['race_season'].iloc[0].astype(str)
    
    #check if the directories exist, if not create them
    dir_path = fr'C:\Users\dahed\Documents\Python\STATCAR\Cup_Season\{race_season}\{race_name}\\' 
    
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    #convert df to .csv and store in the directory that was created
    csv_path = dir_path + driver_name + '_' + race_season + '_' + race_name + '_lapdata.csv'
    driverdata_df.to_csv(csv_path, index=False) 

