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
import requests
import sys
import io
import add_files_functions as add_files
from datetime import datetime, timedelta




def get_neodys_list(date):
    response = requests.get("https://newton.spacedys.com/neodys/priority_list/PLfile.txt")
    with open("PLfile.txt", "wb") as file:
        file.write(response.content)
    PL_file = pd.read_csv("PLfile.txt")
    PL_file=PL_file[2:]
    PL_file.columns = ['neodys_1']
    PL_file['urgency']=PL_file['neodys_1'].str.slice(start=12, stop=24)
    PL_file['neodys_1']=PL_file['neodys_1'].str.slice(stop=12)
    PL_file['neodys_1']=PL_file['neodys_1'].str.strip()
    PL_file['urgency']=PL_file['urgency'].str.strip()
    PL_file['neodys_1']=add_space(PL_file['neodys_1'])
    PL_file=PL_file.reset_index()
    #print(PL_file)

    i=0
    with open('neodys_full_list_'+date+'.txt', 'w') as file:
        pass
    while i<len(PL_file['neodys_1']):
        if PL_file['urgency'][i]!='LOW':
            with open('neodys_full_list_'+date+'.txt','a') as f:
                print(PL_file['neodys_1'][i],file=f)           
        i+=1
        
    response = requests.get("https://newton.spacedys.com/neodys/priority_list/FOfile.txt")
    with open("FOfile.txt", "wb") as file:
        file.write(response.content)
    FO_file = pd.read_csv("FOfile.txt")
    FO_file=FO_file[2:]
    FO_file.columns = ['neodys_2']
    FO_file['urgency']=FO_file['neodys_2'].str.slice(start=12, stop=24)
    FO_file['neodys_2']=FO_file['neodys_2'].str.slice(stop=12)
    FO_file['neodys_2']=FO_file['neodys_2'].str.strip()
    FO_file['urgency']=FO_file['urgency'].str.strip()
    FO_file['urgency']=FO_file['urgency'].str.strip()
    FO_file['neodys_2']=add_space(FO_file['neodys_2'])
    FO_file=FO_file.reset_index()
    #print(FO_file)

    i=0
    while i < len(FO_file['neodys_2']):
        if FO_file['urgency'][i].strip() != 'LOW':
            if FO_file['urgency'][i].strip() != 'USEFUL':
                line = FO_file['neodys_2'][i].strip()  # remove leading/trailing whitespace
                if line:  # check if the line is not empty
                    with open('neodys_full_list_'+date+'.txt', 'a') as f:
                        print(line, file=f)
        i += 1

    return str('neodys_full_list_'+date+'.txt')
    



def add_space(list_object):
    new_list=[]
    for i in list_object:
        i = i[:4] + ' ' + i[4:] 
        new_list.append(i)
    return new_list





def main():

    # Get the current date and time
    now = datetime.now()
    
    # Calculate the dates for tomorrow and the day after
    tomorrow = now + timedelta(days=1)
    day_after_tomorrow = now + timedelta(days=2)
    
    # Format the dates as strings with the time 7:30
    date_today=now.strftime('%Y-%m-%d')
    date1 = tomorrow.strftime('%Y-%m-%d') + ' 07:30'
    date2 = day_after_tomorrow.strftime('%Y-%m-%d') + ' 07:30'
    



    #date1='2023-04-25 07:30' #input("What is the first date and time? ex: 2022-03-29 07:30 ")
    #date2='2023-04-26 07:30' #input("what is the second date and time? ex: 2022-04-10 07:30 ")
    date = date_today.replace('-', '')
    date_short = date[2:]



    filename=get_neodys_list(date)
    

    
    with open(filename) as f:
        lines = [line.strip() for line in f.readlines()[:-1]]

    
    
    Neodys_data=add_files.MPC_Horizons_list(date1, date2, lines)
    
    #print('Sorting files now ...')
    add_files.sortall(date_today, Neodys_data, 'd_NEODYS_'+date_short+'.txt')


    
    
    
if __name__ == "__main__":  main()
