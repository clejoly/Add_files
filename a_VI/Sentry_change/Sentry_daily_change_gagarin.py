#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 11:27:42 2024

This program checks the Sentry VI list everyday and compares it with the
previous day to show changes.

@author: cassandralejoly
"""

import requests
import json
from datetime import datetime
import sys
import os
from datetime import datetime, timedelta
import time



def get_all_sentry_vis(today_objects_file, directory):
    """ Obtain all object on the VI Sentry List """

    # Send Query to Sentry API
    response = requests.get("https://ssd-api.jpl.nasa.gov/sentry.api?all=1")
    data = response.json()
    
    # Obtain all objects in the list and make a set of them
    des_list = [obj['des'] for obj in data['data']]
    des_set=set(des_list)
    
    # Remove previous instances of the VI_list.txt file if it exists
    if os.path.exists(directory + "/"+ today_objects_file):
        os.unlink(directory + "/"+ today_objects_file)
    
    # Write out the list and save as 'VI_list_datetoday.txt'
    with open(directory + "/"+ today_objects_file, 'w') as f:
        for item in des_set:
            f.write("%s\n" % item)
            

def in_out(today_objects_file, latest_objects_file, changes_file_name, directory, date):
    "Find the differences between today's and yesterday's lists"
    
    # Read contents of the two files  
    today_objects = read_file(directory + "/" + today_objects_file)   
    yesterday_objects =   read_file(directory + "/" + latest_objects_file) 

    # Identify added and removed objects
    added_objects = today_objects - yesterday_objects
    removed_objects = yesterday_objects - today_objects
    
    max_object_length = 10
    
    # Read Existing Content
    existing_content = open(directory+ "/" + changes_file_name, 'r').readlines()
    
    with open(directory + "/" + changes_file_name, 'w') as changes_file:
        changes_file.write(f"Object{' ' * (max_object_length - 6)}\tChange\tDate\n")
                
        for added_object in added_objects:
            changes_file.write(f"{added_object.ljust(max_object_length)}\tIN\t"+ date+ "\n")
        for removed_object in removed_objects:
            changes_file.write(f"{removed_object.ljust(max_object_length)}\tOUT\t"+ date+ "\n")
    
        # write back the existing content
        changes_file.writelines(existing_content[1:])


        
            

def read_file(filepath):
    with open(filepath, 'r') as file:
        return set(line.strip() for line in file)
              
  
    
def get_latest_objects_file(directory):
    # Get a list of files in the specified directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    # Filter files that match the naming pattern (adjust as needed)
    objects_files = [f for f in files if f.startswith("VI_list_")]

    # Sort files by creation time and get the latest one
    latest_objects_file = max(objects_files, key=lambda f: os.path.getctime(os.path.join(directory, f)), default=None)

    return latest_objects_file
            
def main():

    # Get the current date and time
    now = datetime.now()
    
    # Calculate the date for yesterday 
    yesterday = now + timedelta(days=-1)

    # Directory of our files
    directory = "/home/swatch/Cassandra/sentry_monitoring"

    # Format the dates as strings with the time 7:30
    date_today = now.strftime('%Y-%m-%d').replace('-', '')
    # date_yesterday = yesterday.strftime('%Y-%m-%d').replace("-", "")
    latest_objects_file = get_latest_objects_file(directory)
    
    today_objects_file = 'VI_list_'+ date_today +'.txt'

    # get all the objects currently on the VI Sentry list
    get_all_sentry_vis(today_objects_file, directory)

    changes_file_name = "Sentry_change_list.txt"

    

    in_out(today_objects_file, latest_objects_file, changes_file_name, directory, date_today)    

    
    
    
if __name__ == "__main__":  main()
