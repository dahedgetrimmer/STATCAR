#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 08/09/2023

@author: Jared Revier

Data scrapper that can gather lap data from NASCAR Cup Series Race and
create a .csv for each driver containing Lap Time, Lap Speed, Running Position
"""

import json
import requests
import pandas as pd

#Link to Phoenix Spring 2023 race lap data json
json_link = 'https://cf.nascar.com/cacher/2023/1/5271/lap-times.json'

response = requests.get(json_link)

if response.status_code == 200:
    
    PHX_S2023_lap_data = response.json()           #creates a dictionary of lap data
    
else:
    print('Failed to respond')


#creates a .csv for each driver with relevant data

for i in range(len(PHX_S2023_lap_data['laps'][:])):
    driver_name = PHX_S2023_lap_data['laps'][i]['FullName']
    df = pd.DataFrame(PHX_S2023_lap_data['laps'][i]['Laps'])
    
    
    info_labels = pd.Series(PHX_S2023_lap_data['laps'][i].keys())
    driver_info = pd.Series(PHX_S2023_lap_data['laps'][i])
    
    info_labels = info_labels.drop(index=5)
    driver_info = driver_info.drop('Laps')

    
    df = pd.concat([info_labels, driver_info, df])
    csv_path = '/home/jrevier/PyCAR Data/' + driver_name + '_Phoenix_Spr2023_Laptimes.csv'
    df.to_csv(csv_path, index=False,)


print('SUCCESS')

