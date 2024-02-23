#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 08/09/2023

@author: Jared Revier

Data scrapper to gather lap data from NASCAR Cup Series races
"""

import json
import requests

#Link to Phoenix Spring 2023 race lap data json
json_link = 'https://cf.nascar.com/cacher/2023/1/5271/lap-times.json'

response = requests.get(json_link)

if response.status_code == 200:
    
    PHX_S2023_lap_data = response.json()           #creates a dictionary of lap data
    
    print (PHX_S2023_lap_data)
    
else:
    print('Failed to respond')
