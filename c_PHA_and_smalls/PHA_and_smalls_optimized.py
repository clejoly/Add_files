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
import add_files_functions as add_files
import warnings
from datetime import datetime, timedelta


def get_PHA_list(d_min,t_max):
    date_max=round((t_max-2023)*365.25)
    response = requests.get("https://ssd-api.jpl.nasa.gov/cad.api?dist-max="+str(d_min)+"&date-max=%2B"+str(date_max)+"&sort=object")
    data=pd.DataFrame.from_dict(response.json()['data'],orient="columns")
    data.rename(columns={0: 'des', 1: 'orbit_id', 2:'jd', 3: 'cd', 4:'dist', 5:'dist_min', 6:'dist_max', 7:'v_rel', 8:'v_inf', 9:'t_sigma_f', 10:'h' }, inplace=True)
    j=0
    for i in data[:]['des']:
        print(i)
        #print(j)
        if (' ' in i)==False:
            print("numbered")
            #print(i)
            data.drop(j,axis=0,inplace=True)
        j+=1
    return data



def separate_small_PHA(MPC_data):
    PHA = MPC_data[MPC_data['H'] < 22.5]
    smalls = MPC_data[MPC_data['H'] >= 22.5]            
    print(PHA.head())
    print(smalls.head())
    return PHA, smalls



    


def main():
    warnings.filterwarnings('ignore', 'A value is trying to be set on a copy of a slice from a DataFrame')


    ### Inputs necessary: 
    '''
    date1='2023-06-01 07:30' #input("What is your start time for run 1?  Example: 2022-03-02 07:30  ")

    date2='2023-06-14 07:30' #input("What is your start time for run 2?  Example: 2022-03-02 07:30  ")
    date_parts = date1.split(' ')
    today_date = date_parts[0]  # '2023-03-11'
    '''
    ### Obtaining initial data:
    data = get_PHA_list(0.0301, 2063) #data unpacked!
    
    #to test --> less data to deal with.
    #data = get_PHA_list(0.0101, 2024) #data unpacked!



    # Get the current date and time
    now = datetime.now()
    
    # Calculate the dates for tomorrow and the day after
    tomorrow = now + timedelta(days=1)
    two_weeks = now + timedelta(days=14)
    
    # Format the dates as strings with the time 7:30
    today_date=now.strftime('%Y-%m-%d')
    date1 = tomorrow.strftime('%Y-%m-%d') + ' 07:30'
    date2 = two_weeks.strftime('%Y-%m-%d') + ' 07:30'
    



    #date1='2023-04-25 07:30' #input("What is the first date and time? ex: 2022-03-29 07:30 ")
    #date2='2023-04-26 07:30' #input("what is the second date and time? ex: 2022-04-10 07:30 ")
    date = today_date.replace('-', '')
    date_short = date[2:]






    

    # %% ### removing duplicates from list: 
    keep_desig = add_files.remove_duplicate(data['des'], 'n')
    print(keep_desig)
    del data





    PHA_SMALL_data=add_files.MPC_Horizons_list(date1, date2, keep_desig)



    PHA, smalls = separate_small_PHA(PHA_SMALL_data)

    

    # %% # # Doing PHAs first!
        
    
    add_files.sortall(today_date,PHA,'c_PHA_0.03au_40yr_'+date_short+'.txt')

    
    # %% # # Doing PHAs first!
    add_files.sortall(today_date,smalls,'g_small_0.03au_40yr_'+date_short+'.txt')

    
    
    
    
    
    
if __name__ == "__main__":  main()
