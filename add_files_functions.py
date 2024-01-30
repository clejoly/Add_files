#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 11 15:17:06 2023

@author: cassandralejoly

Series of functions created to be used by the add_file functions to create the set of add file documents.
"""

import os
import requests
import json
import datetime
import time
from pathlib import Path

from pandas import json_normalize
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def get_driver():
    """ Sets the chromedriver location """
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', 
                              options=options)
    return driver


def get_MPC_1_line(my_list):
    """
    Returns the MPC one-line elements for a set of objects
    
    Inputs: 
        my_list: a list of strings representing objects for which MPC 
                one-line elements need to be obtained.
    Outputs:
        data: a pandas dataframe containing the MPC one-line elements for
              for all the objects on my_list seperated by columns. 
    
    """

    file_path = '/Users/cassandralejoly/Downloads/elements.txt'


    # Obtain the driver to the Minor Planet Center    
    driver = get_driver()
    driver.get("https://minorplanetcenter.net/iau/MPEph/MPEph.html")

    # Remove previous instances of the elements.txt file if they exist
    if os.path.exists(file_path):
        os.unlink(file_path)

    # Declare all buttons to be used on the webpage
    reset = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.XPATH, "//input[@type='reset']"
            )))
    submit = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.XPATH, "//input[@type='submit']"
            )))
    text_box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.TAG_NAME, "textarea"
            )))
    MPC_1_line = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.XPATH, "//input[@value='-1']"
            )))

    # Interact with webpage
    reset.click()
    for i in my_list:
        text_box.send_keys(i+"\n")
    MPC_1_line.click()
    submit.click()

    # Wait for file to download (it can take a few seconds)
    while not os.path.exists(file_path):
        time.sleep(0.5)    

    # Separate text file into columns
    columns=[(0,7),(7,13),(14,19), (19,25), (25,35), (35,46), 
             (46,57), (57,68), (68,79),(79,91),(91,103),
             (103,106), (106,116), (116,122), (122,126), 
             (126,136), (136,141), (141,145), (145,149),
             (149,160), (160,165), (165,191), (191,202)]

    # Read file into Panda dataframe and remove downloaded text file
    data=pd.read_fwf(file_path, header=None, colspecs=columns)
    os.unlink('/Users/cassandralejoly/Downloads/elements.txt')
    driver.close()
    
    return data


def MPC_Horizons_list(date1, date2, designations):
    """
    Returns the positional uncertainties at different times, the U value, and 
    the last observed date
    
    Inputs:
        date1: a date for the first measurement. Must be given in the 
               datetime.strftime() format: .strftime('%Y-%m-%d') + ' hh:mm'
        date2: the second date measurement (usually 6 months later) in the 
               same format: .strftime('%Y-%m-%d') + ' hh:mm' 
        designations: a list of object names for which to obtain measurements
    Outputs:
        Horizon_data: a pandas dataframe that includes the object name, H, U1,
               arc length (split into 2 columns), desig, and last observation.
    
    """   
    
    # Obtaining the MPC one-line elements (100 elements at a time is the limit)
    MPC_list = []
    for i in range(0, len(designations), 100):
        temp1 = get_MPC_1_line(designations[i:i+100])
        MPC_list.append(temp1)
    MPC = pd.concat(MPC_list)

    # Retrieving the Object list in the correct format
    object_list=MPC[21][:]

    # Rearranging and renaming columns
    column_mapping = {0: 'Packed desig', 1: 'H', 11: 'U1', 15: 
                      'arc length', 21: 'desig', 22: 'last obs in orbit'}
    MPC.rename(columns=column_mapping, inplace=True)    
    MPC_keep = MPC.loc[:, ['Packed desig', 'H', 'U1', 'desig', 
                           'last obs in orbit', 'arc length']]
    MPC_keep[['arc', 'length']] = MPC_keep['arc length'].str.split('[- ]', 
                                                                   expand=True)

    # Printing progress to command line   
    print('running horizons ...')

    # Obtaining Horizon's information for objects in list
    horizons_data=pd.DataFrame()
    kept_objects=[]
    for i in object_list:
        print(i)
        try:
            Pos_uncertainty1=Horizons(i, date1)
            Pos_uncertainty2=Horizons(i, date2)
            U,LastObsUse=JPL_U(i)
            temp=pd.DataFrame({'uncert1':[Pos_uncertainty1],
                               'uncert2':[Pos_uncertainty2],
                               'U2':[U],
                               'LastObsUsed':[LastObsUse]})
            data=[horizons_data, temp]
            horizons_data=pd.concat(data, ignore_index=True)
            kept_objects.append(i)
        except:
            print(i + " not found")
            pass #when data is missing for an object, it is skipped
    
    
    # Keeping only objects that have Horizon measurements
    MPC_keep = MPC_keep[MPC_keep['desig'].isin(kept_objects)]
    Horizon_data = pd.concat([MPC_keep.reset_index(drop=True), 
                              horizons_data.reset_index(drop=True)], 
                             axis=1, ignore_index=False)
    return Horizon_data  
    

def Horizons(Object_name, date, max_attempts=3, delay=0.25):
    """
    Queries the Horizon's JPL API based on the object's name and the given 
    date to return the Ephemerides at 691 and extract the positional 
    uncertainty in arcseconds
    
    Inputs: 
        Object_name: the unpacked name of an asteroid as a string
        date: The date and time to query the ephemerides.Must be given in the 
               datetime.strftime() format: .strftime('%Y-%m-%d') + ' hh:mm'
    Output:
        Pos_uncertainty: The positional uncertainty of the asteroid at the 
        given date and time in arcseconds given as a float.
        
    """
    
    # Parameters: 691 - 0.9m Spacewatch telescope
    Telescope = str(691)
    
    # Rewrite object name to fit in query format, and replace the space
    new_object = Object_name.replace(" ", "%20")
    
    # Querying Horizons to retrieve positional uncertainty
    # It queries it up to three times because Horizons has a tendency to 
    # time out every once in a while. In the case when Horizon's times out
    # more than 3 times in a row, or the positional uncertainty is not 
    # available, a value of 4900 is given.
    for attempt in range(max_attempts):
        try:
            response = requests.get(
                "https://ssd.jpl.nasa.gov/api/horizons.api?format=json"
                "&CENTER="+Telescope
                +"&TLIST='"+date
                +"'&TLIST_TYPE=CAL"
                "&COMMAND='DES="+new_object
                +"'&QUANTITIES='38'")
            data = pd.DataFrame.from_dict(response.json(), orient="columns")
            new_data = data['result'].str.split('\n', expand=True)
            i = 0
            while i < len(new_data.columns) - 2:
                if (new_data[i]['version'] == '$$SOE' 
                        and new_data[i + 2]['version'] == '$$EOE'):
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


def JPL_U(Object_name):
    """
    Queries the JPL small body Database API for the U value and the last 
    date it was observed for a given asteroid
    
    Input:
        Object_name: The unpacked name of the asteroid as a string.
    Output:
        U: the condition_code (U value) of the asteroid as obtained from the 
            JPL small body database given as a float
        LastObsUse: The date of the last observation used in the orbit
            calculation given as a string in the format 'YYYY-MM-DD'    
    """
    
    # Querying the small body database to obtain the U value. If the U value
    # and Last observed date query fails, an automatic value is set as U=0, 
    # and date = '2000-01-01'
    try:
        new_object=Object_name.replace(" ","%20")
        response = requests.get("https://ssd-api.jpl.nasa.gov/sbdb.api?sstr="
                                +new_object+"")
        data=pd.DataFrame.from_records(response.json())
        #data.to_csv('test_2.csv')
        U=data['orbit']['condition_code']
        LastObsUse=data['orbit']['last_obs']
    except:
        U=0
        LastObsUse='2000-01-01'
    return U,LastObsUse

 
def sortall(today_date,data_table,outfile):
    """
    Sorts the objects to decide which ones to keep based on 691's parameters. 
    This takes the list of objects with their parameters, and returns a 
    text file with all the objects kept, named as provided in the function.
    
    Inputs:
        today_date: The current date, given as a string in the format
            'YYYY-mm-dd'
        data_table: a list of objects, with the necessary Horizon's information
            as a pandas dataframe.
        outfile: The name of the file in which the objects that will be kept
            are saved into.
    Outputs:
        None from function, but a text file with objects kept is saved as
            outfile.
    """
    

    # Parameters set up, for what to keep in the list.
    min_uncert=float(1.0)   
    today_date_datetime=datetime.datetime.strptime(today_date, '%Y-%m-%d')
    year_from_date=today_date_datetime-datetime.timedelta(days=365.2425)
    Max_uncertainty=float(4800.0) #in arcseconds
 
    
    
    # Convert the columns to float and datetime
    try:
        data_table['uncert1'] = data_table["uncert1"].astype(float)
    except ValueError:
        data_table['uncert1'] = float(4900.0)
    
    try:
        data_table['uncert2'] = data_table["uncert2"].astype(float)
    except ValueError:
        data_table['uncert2']= float(4900.0)
    
    try:
        data_table['U1'] = data_table["U1"].astype(float)
    except ValueError:
        data_table['U1'] = float(10.0)
    
    try:
        data_table['U2'] = data_table["U2"].astype(float)
    except ValueError:
        data_table['U2'] = float(10.0)
    
    try:
        data_table['arc'] = data_table["arc"].astype(float)
    except ValueError:
        data_table['arc'] = float(1000)
    
    try:
        data_table['LastObsUsed'] = pd.to_datetime(
            data_table["LastObsUsed"], 
            errors='coerce')
    except ValueError:
        data_table['LastObsUsed'] = pd.to_datetime('2000-01-01')
        

    # From data_table, keep only the objects with the uncertainties less than
    # the max uncertainty. 
    keep = data_table[(
        (data_table['uncert1'] < Max_uncertainty) 
        & (data_table['uncert2'] < Max_uncertainty))]
    
    # From data left, keep objects where:
    #   1) the one uncertainty is greater than the minimum uncertainty OR
    #   2) Where both uncertainties are less than the minimum uncertainty AND
    #      the observing arc is less than 100 days AND the last observed date
    #      is less than a year ago from today OR
    #   3) The uncertainties are less than the minimum uncertainty AND the U1
    #      and U2 parameters do not equal zero or one.
    keep = keep[(((data_table['uncert1'] > min_uncert) 
                  | (data_table['uncert2'] > min_uncert)) 
                 |((data_table['uncert1'] < min_uncert) 
                   & (data_table['uncert2'] < min_uncert) 
                   & (data_table['arc'] < 100) 
                   & (data_table['LastObsUsed'] < year_from_date))
                 | (((data_table['uncert1'] < min_uncert) 
                     & (data_table['uncert2'] < min_uncert))
                    & (((data_table['U1'] != 0) 
                        & (data_table['U2'] != 0))
                       |((data_table['U1'] != 1) 
                         & (data_table['U2'] != 0))
                       |((data_table['U1'] != 0) 
                         & (data_table['U2'] != 1))
                       |((data_table['U1'] != 1) 
                         & (data_table['U2'] != 1)))))]
    
    # Keep only the designation from the sorted file and save to text file.
    desig = keep['desig']
    desig.to_csv(outfile, header=False, index=False)
    
    
def remove_duplicate(data,packed):
    """
    This removes duplicate objects in a list of objects, given that they
    are in packed or unpacked format.
    
    Inputs:
        data: the list of objects to remove duplicates from. It can be in
            packed or unpacked format.
        packed: a string with either 'y' or 'n' to determine if the objects 
            are given in packed or unpacked designation.
    Outputs:
        keepdesigs: a list of objects that are not duplicated, given as a 
            series of strings.
    """
    
    # Set up arrays to fill.
    inputlines = data
    targets = []
    
    # Determines if the objects are in packed or unpacked format, and either
    # keeps them or changes them to packed designation
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

    # Checks that all objects have been packed correctly and raises an 
    # error if they were not.
    for i in targets:
        if len(i) > 7: raise ValueError('File was not parsed correctly.')
    
    # Remove duplicates using a set and return it.
    keepdesigs = list(set(targets))
    return keepdesigs    



def PackDesig(ProvDesig):
    """
    Changes the provisional designation of objects to a Packed designation.
    
    Input:
        ProvDesig: The provisional designation of an object as a string.
    Output: 
        Outdesig: The packed designation of the same object as a string.
    """

    # Strip off ann leading or trailing spaces.
    ProvDesig = ProvDesig.strip()
    
    # Break up the string into its corresponding components
    century = ProvDesig[0:2]
    year = ProvDesig[2:4]
    MonthCode = ProvDesig[5:7]
    cycle = ProvDesig[7:]
    CycleDigits = len(cycle)
    
    # Fills the cycle character with leading zeros such that it is at least 2 
    # characters long.
    CycleOutStr = cycle.zfill(2)    
    
    # if there are more than 2 characters in the cycle string, it changes
    # the characters to the correct packed designation cycle number output.
    if (CycleDigits > 2):
        alphas='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        FinalDigit = cycle[(CycleDigits-1):]
        FirstDigits = int(cycle[0:(CycleDigits-1)])
        CycleOutStr = alphas[FirstDigits - 10] + FinalDigit
    
    # Picks the correct letter for the century with J=1900 and K=2000 
    CenturyStr = chr(int(century) - 10 + ord('A'))  

    # Writes out the packed designation and returns it.      
    OutDesig = CenturyStr + year + MonthCode[0] + CycleOutStr + MonthCode[1]
    return(OutDesig)



def site_sort(inputpathfile):
    """
    This sorts the unobs file such that it only keeps the Objects observed by
    C51 (NEOWISE) that are not numbered and from 1800 - present
    
    Input:
        inputpathfile: the location of the unobs file as a string.
    Output:
        keepdesigs: A list of objects that were observed by C51 and from
            1800 - present.
    """
    
    # Determine the obscode of NEOWISE
    obscode = 'C51'

    # Choose which character corresponds to which column, and only keep the 
    # designation and the OBSCODE. Then reads in the file in chuncks as it is
    # a really large data set
    columns = [(0, 5), (5, 12), (77, 80)]
    chunksize = 1000000
    data = pd.DataFrame()
    
    # Reads in the data in chunks, keeping only the object name, and the 
    # OBSCODE.
    for chunk in pd.read_fwf(inputpathfile, 
                             header=None, 
                             colspecs=columns, 
                             usecols=[1, 2], 
                             chunksize=chunksize):
        print('chunk done')
        data = pd.concat([data, chunk])


    # Keep only the objects with Observatory code as given, and that start
    # with 'I', 'J', or 'K', representing either 1800s, 1900s, or 2000s, then
    # returns the list of objects only.
    keepdesigs = set()
    for objects, telescope in data.itertuples(index=False):

        if telescope == obscode:
            if objects.startswith(('I', 'J', 'K')):
                keepdesigs.add(objects)
    return list(keepdesigs)


def UnpackDesig(PackedDesig):
    """
    Unpacks a packed designation to change it to a provisional designation.
    
    Input:
        PackedDesig: an object in packed designation given as a string.
    Output:
        OutDesig: The same object given in a provisional designation.
    """
    
    # Picks out the century character and changes it to the correct first 2
    # characters representing the century.
    CenturyStr = PackedDesig[0]
    CenturyChar = 'IJK'
    century = str(CenturyChar.index(CenturyStr) + 18)
    
    # Picks out the year in short-form (ie: YY).
    year = PackedDesig[1:3]
    
    # Picks out the two characters representing the half-month portion of the
    # designation
    HalfMonth1 = PackedDesig[3]
    HalfMonth2 = PackedDesig[6]
    
    # Picks out the cycle characters, then changes it to the appropriate cycle
    # format. This includes finding the index of the first character, 
    # multiplying it by 10 to put it in the correct format, then adding the 
    # second character.
    Cycle1 = PackedDesig[4]
    Cycle2 = PackedDesig[5]
    CycleChar = ("0123456789"
                 "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                 "abcdefghijklmnopqrstuvwxyz")
    cycle =str(CycleChar.find(Cycle1) * 10 + int(Cycle2))
    if cycle == '0':
        cycle = ''

    # Formats the unpacked designatiion as a string and returns the new name.
    OutDesig = f"{century}{year} {HalfMonth1}{HalfMonth2}{cycle}"
    return OutDesig


def Target_compare(List1,List2):
    """ Finds the object in two lists, and returns the common ones. """
    target_file = set(List1[0])
    detected_file = set(List2[0])
    observed_targets = target_file & detected_file
    Observedoutputfile = pd.DataFrame(observed_targets, columns=["Objects"])
    return Observedoutputfile













