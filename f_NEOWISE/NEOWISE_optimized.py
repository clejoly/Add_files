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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import requests
from pandas import json_normalize
import json
import datetime
import gc
import add_files_functions as add_files
import urllib.request
import gzip
import shutil
import os
from datetime import date
import requests
from datetime import datetime, timedelta





def get_small_bodies():
    url = "https://cgi.minorplanetcenter.net/cgi-bin/textversion.cgi?f=lists/Atens.html"
    filename = "Atens.txt"
    urllib.request.urlretrieve(url, filename)
    
    # Read in the columns from character (0 to 26) and (27 to 38)

    atens=[]
    with open(filename, "r") as f:
        for line in f:
            col1 = line[0:27].strip()
            col2 = line[27:39].strip()
            
            # Only keep the second column if column 1 is empty
            if col1 == "":
                # Strip the spaces before and after the string in column 2
                col2 = col2.strip()
                if col2!="":
                    atens.append(col2)
                    print(col2)
    

    url2 = "https://cgi.minorplanetcenter.net/cgi-bin/textversion.cgi?f=lists/Apollos.html"
    filename2 = "Apollos.txt"
    urllib.request.urlretrieve(url2, filename2)
    
    # Read in the columns from character (0 to 26) and (27 to 38)
    apollos=[]
    with open(filename2, "r") as f:
        for line in f:
            col3 = line[0:27].strip()
            col4 = line[27:39].strip()
            # Only keep the second column if column 1 is empty
            if col3 == "":
                # Strip the spaces before and after the string in column 2
                col4 = col4.strip()
                if col4 !="":
                    apollos.append(col4)
                    print(col4)

    url3 = "https://cgi.minorplanetcenter.net/cgi-bin/textversion.cgi?f=lists/Amors.html"
    filename3 = "Amors.txt"
    urllib.request.urlretrieve(url3, filename3)
    
    # Read in the columns from character (0 to 26) and (27 to 38)
    amors=[]
    with open(filename3, "r") as f:
        for line in f:
            col5 = line[0:27].strip()
            col6 = line[27:39].strip()
            
            # Only keep the second column if column 1 is empty
            if col5 == "":
                # Strip the spaces before and after the string in column 2
                col6 = col6.strip()
                if col6!="":
                    amors.append(col6)
                    print(col6)

    merged_list = []
    merged_list.extend(atens)
    merged_list.extend(apollos.pop(0))
    merged_list.extend(amors)
    
    


    os.unlink("Atens.txt")
    os.unlink("Amors.txt")
    os.unlink("Apollos.txt")
               
    with open('merged_list.txt', 'w') as f:
        for item in merged_list[:-1]:
            f.write("%s\n" % item)
            
    with open('merged_list.txt', 'r') as f:
        lines = f.readlines()

    # Remove empty lines from list of lines
    lines = [line for line in lines if line.strip()]
    
    with open('small_bodies_list.txt', 'w') as f:
        f.writelines(lines)
    return 'small_bodies_list.txt'
            













def downloading_UnnObs():
    # Set the URL for the file you want to download
    url = 'https://minorplanetcenter.net/iau/ECS/MPCAT-OBS/midmonth/UnnObs.txt.gz'
    
    # Set the output directory where you want to save the file
    output_dir = '/Users/cassandralejoly/Cassandra/Cassandra/Spacewatch/add_files/python_add_files/f_NEOWISE'
    
    
    # Set the output filename to include the current date
    output_filename = 'UnnObs_{}.txt'.format(date.today().strftime('%Y%m%d'))
    
    # Download the file from the URL
    response = urllib.request.urlopen(url)
    
    # Save the downloaded file to disk
    with open(os.path.join(output_dir, 'UnnObs.txt.gz'), 'wb') as outfile:
        outfile.write(response.read())
    
    # Unzip the downloaded file
    with gzip.open(os.path.join(output_dir, 'UnnObs.txt.gz'), 'rb') as infile:
        with open(os.path.join(output_dir, output_filename), 'wb') as outfile:
            shutil.copyfileobj(infile, outfile)
    
    # Delete the original downloaded file
    os.remove(os.path.join(output_dir, 'UnnObs.txt.gz'))
    return output_filename














def main():


    ### Inputs necessary: 
    '''
    date1='2023-05-16 07:30'
    date2='2023-06-01 07:30'
    date_parts = date1.split(' ')
    today_date = date_parts[0]     
    '''
    
    filename=get_small_bodies()
    

    #filename='small_bodies_list.txt'

    print('downloading UnnObs ...')
    #inputpathfile=downloading_UnnObs() 
    inputpathfile='UnnObs_20231031.txt'


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

    
    
    
    
    
    
    
    # %% First doing Site Sort
    print('Starting Site Sort ... \n')
    asteroids_in_C51=add_files.site_sort(inputpathfile)
    print(asteroids_in_C51)
    print('Site Sort done \n')
 
    
 
    unpacked_asteroid_in_C51 = pd.concat([pd.DataFrame({add_files.UnpackDesig(i)}) for i in asteroids_in_C51], ignore_index=True)
    unpacked_asteroid_in_C51.to_csv("unpacked_asteroid_in_C51.txt", index=False, header=False)
    
    print('done')
    list1=pd.read_csv(filename,  header=None)
    list2=pd.read_csv("unpacked_asteroid_in_C51.txt",  header=None)
    
    
    object_list=add_files.Target_compare(list1,list2)
    
    print(object_list)


    object_list.to_csv('observed_out.txt', index=False, header=False)
    del asteroids_in_C51, unpacked_asteroid_in_C51, list1, list2, object_list
    gc.collect()
    
    
    print('Lets go!')


    
    chunksize = 1000000 # number of rows to read at a time
    keep_desig = pd.DataFrame()
    
    for chunk in pd.read_csv('observed_out.txt', header=None, usecols=[0], chunksize=chunksize):
        print('chunk done')
        keep_desig = pd.concat([keep_desig, chunk])

    sort_dirty=add_files.MPC_Horizons_list(date1, date2, keep_desig[0])
    sort_dirty.to_csv('sort_dirty.csv',index=False)


    
    add_files.sortall(today_date,sort_dirty,'f_NEOWISE_'+date_short+'.txt')
    

    
    
    
if __name__ == "__main__":  main()
