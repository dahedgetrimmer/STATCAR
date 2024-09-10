#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 08/09/2023
Updated on 09/03/2024

@author: Jared Revier

Data scrapper that can gather lap data from NASCAR Cup Series Race and
create a .csv for each driver containing Driver Data, Lap Times, Lap Speed, and Running Position
"""

import requests
import pandas as pd

#Link to Phoenix Spring 2023 race lap data json
json_link = 'https://cf.nascar.com/cacher/2023/1/5271/lap-times.json'

response = requests.get(json_link)

if response.status_code == 200:
    
    PHX_S2023_lap_data = response.json()           #creates a dictionary of lap data
    
else:
    print('Failed to respond')


#construct dataframe using Pandas

for i in range(len(PHX_S2023_lap_data['laps'][:])):
    driver_name = PHX_S2023_lap_data['laps'][i]['FullName']
    df = pd.DataFrame(PHX_S2023_lap_data['laps'][i]['Laps'])
    
   
    driver_info = pd.DataFrame(PHX_S2023_lap_data['laps'][i])

   
    driver_info = driver_info.drop(columns='Laps')
    driver_info = driver_info.drop(columns='RunningPos')
    
    df = pd.concat([driver_info, df], axis=1)
    df['LapTime'] = df['LapTime'].fillna(0)
    
#creates a .csv for each driver with relevant data
    
    csv_path = 'PATH_TO_DIR' + driver_name + '_Phoenix_Spr2023_Laptimes.csv'
    df.to_csv(csv_path, index=False,)


print('SUCCESS')


