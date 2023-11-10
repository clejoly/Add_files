#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 08:59:39 2022

Code for running RADAR


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
from datetime import datetime, timedelta
import add_files_functions as add_files


    


def main():


    ### Inputs necessary: 
    filename='radar_list.txt'
    '''
    date1='2023-05-16 07:30'
    date2='2023-06-01 07:30'
    date_parts = date1.split(' ')
    today_date = date_parts[0]  # '2023-03-11'
    '''
    
    
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
    
    
    
    
    
    
    file=pd.read_csv(filename, header=None)
    print(file)


    RADAR_data=add_files.MPC_Horizons_list(date1, date2, file[0])

    
    add_files.sortall(today_date,RADAR_data,'e_Radar_'+date_short+'.txt')

    
    
    
    
    
    
    
if __name__ == "__main__":  main()
