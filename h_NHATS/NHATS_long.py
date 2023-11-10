#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 08:59:39 2022

Trying to run outside code from One code!


@author: cassandralejoly
"""



import numpy as np
import pandas as pd
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
import time
import os
import requests
from pandas import json_normalize
import json
import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import add_files_functions as add_files






def download_nhats_excel(date, target_word):
    url = 'https://ssd-api.jpl.nasa.gov/nhats.api'

    response = requests.get(url)
    data = response.json()
    #print(data)
    NHATS = pd.DataFrame(data['data'])
    
    # Convert the date argument to a pandas Timestamp object if it is not already one
    if not isinstance(date, pd.Timestamp):
        date = pd.Timestamp(date)

    # Convert the values in the date column to Timestamp objects if they are strings
    if NHATS['obs_start'].dtype == 'object':
        NHATS['obs_start'] = pd.to_datetime(NHATS['obs_start'], errors='coerce')


    # Filter the DataFrame to keep only rows where the date is less than or equal to the given date or is None
    filtered_NHATS = NHATS[(NHATS['obs_start'].isna()) | (NHATS['obs_start'] <= date)]

    #remove numbered asteroids
    # Use the strip() method to remove leading and trailing spaces from the 'fruit' column
    filtered_NHATS['fullname']=filtered_NHATS['fullname'].str.strip()

    
    filtered_NHATS2 = filtered_NHATS[filtered_NHATS['fullname'].str.startswith('(')]


    # Filter the remaining rows to keep only those where the word column is greater than or equal to the target word
    filtered_NHATS3 = filtered_NHATS2[np.logical_or(filtered_NHATS2['fullname'] >= target_word,filtered_NHATS2['obs_start'].notnull())]


    # Use str.replace() to remove the parentheses around each fruit name
    filtered_NHATS3['fullname'] = filtered_NHATS3['fullname'].str.replace(r'\(|\)', '')


     
    
    # Read in a second text file
    with open('NHATS_emailTargets.txt', 'r') as f:
        email_list = f.read()
    
    # Combine the contents of the two text files
    combined_txt = pd.concat([filtered_NHATS3['fullname'], pd.Series(email_list.split('\n'))], axis=0, ignore_index=True)
    
    # Save the combined text to a new file
    with open('NHATS_combined_list.txt', 'w') as f:
        f.write('\n'.join(combined_txt))

    
    
    



def main():

    
    ### Inputs necessary: 
    asteroid='(2021 XA)'  #2 years ago asteroid (or estimate)

        
    # Get the current date and time
    now = datetime.now()
    
    # Calculate the dates for tomorrow and the day after
    tomorrow = now + timedelta(days=1)
    two_weeks = now + timedelta(days=14)
    six_months = now + timedelta(days=183)
    
    # Format the dates as strings with the time 7:30
    today_date=now.strftime('%Y-%m-%d')
    date1 = tomorrow.strftime('%Y-%m-%d') + ' 07:30'
    date2 = two_weeks.strftime('%Y-%m-%d') + ' 07:30'
    date3 = six_months.strftime('%Y-%m-%d')



    #date1='2023-04-25 07:30' #input("What is the first date and time? ex: 2022-03-29 07:30 ")
    #date2='2023-04-26 07:30' #input("what is the second date and time? ex: 2022-04-10 07:30 ")
    date = today_date.replace('-', '')
    date_short = date[2:]





    '''
    date1='2023-05-16 07:30' #today
    date2='2023-06-01 07:30' #next time it is run    
    date3='2023-11-16'   #6 months from now

    
   
    date_parts = date1.split(' ')
    today_date = date_parts[0]  # '2023-03-11'
    '''
    
    download_nhats_excel(date3,asteroid)

    filename='NHATS_combined_list.txt'
    file=pd.read_csv(filename, header=None)




    
    # %% ### removing duplicates from list: 
    keep_desig = add_files.remove_duplicate(file[0], 'n')
    print(keep_desig)



    # %% ### Running MPC:


    # Running MPC:
    NHATS_data=add_files.MPC_Horizons_list(date1, date2, keep_desig)
    
    
    #Neodys_data = pd.read_csv('sort_dirty.csv')
    print('Sorting files now ...')
    add_files.sortall(today_date, NHATS_data, 'h_NHATS_'+date_short+'.txt')
        
        
    
    
    
if __name__ == "__main__":  main()
