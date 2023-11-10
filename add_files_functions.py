#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 11 15:17:06 2023

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










#DONE
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', options=options)
    return driver


#DONE
def get_MPC_1_line(my_list):
    driver = get_driver()
    driver.get("https://minorplanetcenter.net/iau/MPEph/MPEph.html")

    if os.path.exists('/Users/cassandralejoly/Downloads/elements.txt'):
        os.unlink('/Users/cassandralejoly/Downloads/elements.txt')
    reset = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@type='reset']")))
    submit = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@type='submit']")))
    text_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
    MPC_1_line = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@value='-1']")))

    reset.click()
    for i in my_list:
        text_box.send_keys(i+"\n")
    MPC_1_line.click()
    submit.click()


    file_path = '/Users/cassandralejoly/Downloads/elements.txt'
    while not os.path.exists(file_path):
        time.sleep(0.5)
    
    columns=[(0,7),(7,13),(14,19), (19,25), (25,35), (35,46), (46,57), (57,68), (68,79),(79,91),(91,103),(103,106), (106,116), (116,122), (122,126), (126,136), (136,141), (141,145), (145,149),(149,160), (160,165), (165,191), (191,202)]

    data=pd.read_fwf(file_path, header=None, colspecs=columns)

    os.unlink('/Users/cassandralejoly/Downloads/elements.txt')
    driver.close()
    
    return data



#DONE
def MPC_Horizons_list(date1, date2, keep_desig):
    MPC_list = []
    for i in range(0, len(keep_desig), 100):
        temp1 = get_MPC_1_line(keep_desig[i:i+100])
        MPC_list.append(temp1)
    MPC = pd.concat(MPC_list)

    object_list=MPC[21][:]


    # Get HORIZONS: 
        
    print('running horizons ...')
    
    horizons_data=pd.DataFrame()
    for i in object_list:
        try:
            print(i)
            #print('test')
            Pos_uncertainty1=Horizons(i, date1)
            Pos_uncertainty2=Horizons(i, date2)
            U,LastObsUse=JPL_U(i)
            temp=pd.DataFrame({'uncert1':[Pos_uncertainty1],'uncert2':[Pos_uncertainty2],'U2':[U],'LastObsUsed':[LastObsUse]})
            data=[horizons_data, temp]
            horizons_data=pd.concat(data, ignore_index=True)
        except:
            pass
    #print(horizons_data)   

    column_mapping = {0: 'Packed desig', 1: 'H', 11: 'U1', 15: 'arc length', 21: 'desig', 22: 'last obs in orbit'}
    MPC.rename(columns=column_mapping, inplace=True)
    
    MPC_keep = MPC.loc[:, ['Packed desig', 'H', 'U1', 'desig', 'last obs in orbit', 'arc length']]

    
    MPC_keep[['arc', 'length']] = MPC_keep['arc length'].str.split('[- ]', expand=True)
        
    sort_dirty = pd.concat([MPC_keep.reset_index(drop=True), horizons_data.reset_index(drop=True)], axis=1, ignore_index=False)
    sort_dirty.to_csv('sort_dirty.csv')
    return sort_dirty  
    

 

#DONE
def Horizons(Object_name, date, max_attempts=3, delay=0.5):
    Telescope = str(691)
    new_object = Object_name.replace(" ", "%20")
    for attempt in range(max_attempts):
        try:
            response = requests.get("https://ssd.jpl.nasa.gov/api/horizons.api?format=json&CENTER="+Telescope+"&TLIST='"+date+"'&TLIST_TYPE=CAL&COMMAND='DES="+new_object+"&QUANTITIES='38'")
            data = pd.DataFrame.from_dict(response.json(), orient="columns")
            new_data = data['result'].str.split('\n', expand=True)
            i = 0
            while i < len(new_data.columns) - 2:
                if new_data[i]['version'] == '$$SOE' and new_data[i + 2]['version'] == '$$EOE':
                    line_of_interest = new_data[i + 1]['version']
                    Pos_uncertainty = float(line_of_interest[30:41])
                i += 1
            attempt=3
        except:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                Pos_uncertainty=4900.0

    return Pos_uncertainty


#DONE
def JPL_U(Object_name):
    try:
        new_object=Object_name.replace(" ","%20")
        response = requests.get("https://ssd-api.jpl.nasa.gov/sbdb.api?sstr="+new_object+"")
        data=pd.DataFrame.from_records(response.json())
        #data.to_csv('test_2.csv')
        U=data['orbit']['condition_code']
        LastObsUse=data['orbit']['last_obs']
    except:
        U=0
        LastObsUse='2000-01-01'
    return U,LastObsUse


#DONE  
def sortall(today_date,sort_dirty,outfile):
    print('Sorting\n')
    min_uncert=float(1.0)   
    today_date_datetime=datetime.datetime.strptime(today_date, '%Y-%m-%d')
    year_from_date=today_date_datetime-datetime.timedelta(days=365.2425)
    Max_uncertainty=float(4800.0) #in arcseconds
 
    print(sort_dirty)
    
    # Convert the columns to float and datetime
    try:
        sort_dirty['uncert1'] = sort_dirty["uncert1"].astype(float)
    except ValueError:
        sort_dirty['uncert1'] = float(4900.0)
    
    try:
        sort_dirty['uncert2'] = sort_dirty["uncert2"].astype(float)
    except ValueError:
        sort_dirty['uncert2']= float(4900.0)
    
    try:
        sort_dirty['U1'] = sort_dirty["U1"].astype(float)
    except ValueError:
        sort_dirty['U1'] = float(10.0)
    
    try:
        sort_dirty['U2'] = sort_dirty["U2"].astype(float)
    except ValueError:
        sort_dirty['U2'] = float(10.0)
    
    try:
        sort_dirty['arc'] = sort_dirty["arc"].astype(float)
    except ValueError:
        sort_dirty['arc'] = float(1000)
    
    try:
        sort_dirty['LastObsUsed'] = pd.to_datetime(sort_dirty["LastObsUsed"], errors='coerce')
    except ValueError:
        sort_dirty['LastObsUsed'] = pd.to_datetime('2000-01-01')
        

    keep = sort_dirty[(sort_dirty['uncert1'] < Max_uncertainty) & (sort_dirty['uncert2'] < Max_uncertainty)]
    keep = keep[((sort_dirty['uncert1'] > min_uncert) | (sort_dirty['uncert2'] > min_uncert)) |
                ((sort_dirty['uncert1'] < min_uncert) & (sort_dirty['uncert2'] < min_uncert) & (sort_dirty['arc'] < 100) & (sort_dirty['LastObsUsed'] < year_from_date))| (((sort_dirty['uncert1'] < min_uncert) & (sort_dirty['uncert2'] < min_uncert))& (((sort_dirty['U1'] != 0) & (sort_dirty['U2'] != 0))|((sort_dirty['U1'] != 1) & (sort_dirty['U2'] != 0))|((sort_dirty['U1'] != 0) & (sort_dirty['U2'] != 1))|((sort_dirty['U1'] != 1) & (sort_dirty['U2'] != 1))))]
    
    desig = keep['desig']
    print(desig)
    desig.to_csv(outfile, header=False, index=False)

    # # remove last line of text file
    # with open(outfile) as f:
    #     lines = f.readlines()
    # with open(outfile, "w") as f:
    #     f.writelines(lines[:-1])
    
    
    
#DONE 
def remove_duplicate(data,packed):
    print(len(data))
    inputlines = data
    targets = []
    if packed.lower() == 'y':
        for x in inputlines:
            if x[0] == 'b':
                x_new = x[1:]
                targets.append(x_new)
            else:
                targets.append(x)
    else:
        for x in inputlines:
            targets.append(PackDesig(x))

    for i in targets:
        if len(i) > 7: raise ValueError('File was not parsed correctly.')
    # Remove duplicates using a set
    keepdesigs = list(set(targets))
    print(len(keepdesigs))

    return keepdesigs    



#DONE
def PackDesig(ProvDesig):
    ProvDesig = ProvDesig.strip()  # strip off any leading or trailing spaces
    century = ProvDesig[0:2]
    year = ProvDesig[2:4]
    MonthCode = ProvDesig[5:7]
    cycle = ProvDesig[7:]
    CycleDigits = len(cycle)
    
    CycleOutStr = cycle.zfill(2)    
    
    if (CycleDigits > 2):
        alphas='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        FinalDigit = cycle[(CycleDigits-1):]
        FirstDigits = int(cycle[0:(CycleDigits-1)])
        CycleOutStr = alphas[FirstDigits - 10] + FinalDigit #fixing incorrect letters
    
    CenturyStr = chr(int(century) - 10 + ord('A'))        
    OutDesig = CenturyStr + year + MonthCode[0] + CycleOutStr + MonthCode[1]
    return(OutDesig)




#DONE
def site_sort(inputpathfile):
    obscode = 'C51'

    columns = [(0, 5), (5, 12), (77, 80)]
    chunksize = 1000000 # number of rows to read at a time
    data = pd.DataFrame()
    
    for chunk in pd.read_fwf(inputpathfile, header=None, colspecs=columns, usecols=[1, 2], chunksize=chunksize):
        print('chunk done')
        data = pd.concat([data, chunk])


    keepdesigs = set()
    for objects, telescope in data.itertuples(index=False):

        if telescope == obscode:
            if objects.startswith(('I', 'J', 'K')):
                keepdesigs.add(objects)
    return list(keepdesigs)


#DONE
def UnpackDesig(PackedDesig):
    CenturyStr = PackedDesig[0]
    #print(CenturyStr)
    CenturyChar = 'IJK'
    century = str(CenturyChar.index(CenturyStr) + 18)
    year = PackedDesig[1:3]
    HalfMonth1 = PackedDesig[3]
    HalfMonth2 = PackedDesig[6]
    Cycle1 = PackedDesig[4]
    Cycle2 = PackedDesig[5]
    CycleChar = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    cycle =str(CycleChar.find(Cycle1) * 10 + int(Cycle2))
    if cycle == '0':
        cycle = ''
    OutDesig = f"{century}{year} {HalfMonth1}{HalfMonth2}{cycle}"
    return OutDesig






def Target_compare(List1,List2):
    target_file = set(List1[0])
    detected_file = set(List2[0])
    observed_targets = target_file & detected_file
    Observedoutputfile = pd.DataFrame(observed_targets, columns=["Objects"])
    return Observedoutputfile













