#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 18 14:02:07 2022

Python program to measure priority factor based on Marsden Purgatory factor
Will include the synodical period calculation as well
Meant to replace the fortran routine 

@author: cassandralejoly
"""


import numpy as np
import pandas as pd
from pathlib import Path
import astropy.time
import dateutil.parser
from datetime import datetime, timezone, timedelta
from PyAstronomy import pyasl
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import requests
import time
from os import path
import json
import sys
import add_files_functions


pd.options.mode.chained_assignment = None





def P_sid(a):
    """ Calculates the sidereal Period (P) given the semimajor axis (a)"""
    P=np.sqrt(a**3)
    return P


def P_syn(a):
    """ Calculates the synodic Period (P) given the semimajor axis (a)"""
    P=1/np.abs((1/P_sid(a))-1)
    return P


def Opposition(a):
    """
    This function determines the number of oppositions until the next time
    the object comes close to Opposition, as well as its synodic and sidereal
    period. 
    
    Inputs:
        a: The semimajor axis, in au, as a float.
    Outputs: 
        Psid: The sidereal period in Years, as a float.
        Psyn: The synodic period in years, as a float.
        Nsid: The number of sidereal periods needed such that the Object is at
            its next opposition (within 0.05%) as an integer.
        Msyd: The number of synodic periods needed such that the Object is at
            its next opposition (within 0.05%) as an integer.
        P_periopp: The number of years between oppositions of the Object wrt
            Earth, as a float.
    """
    
    # Calculate the sidereal and synodic period of the Object
    Psid=P_sid(a)
    Psyn=P_syn(a)
    
    # Make arrays of 100 integers (1-100) to set up the Synodic and Sidereal
    # number of orbits needed
    length=100
    Nlist=list(np.arange(1,length))
    Mlist=list(np.arange(1,length))

    # Initialize parameters, including a Nsid_Msyn array where the original
    # number of periods is 10,000 (just as a large baseline)
    i=0
    Nsid_Msyn=[[10000,10000]] 
    
    # Iterates through both Nlist and Mlist to find the combination where the
    # the oppositions occur, i. e. where the sidereal and synodic rotation
    # are within 5% of each other. Creates array of all the occurences.
    while i<length-1:
        j=0
        while j<length-1:
            if np.abs(((Nlist[i]*Psid)-(Mlist[j]*Psyn))/Psid)<0.05:
                temp_array=[Nlist[i], Mlist[j]]
                Nsid_Msyn.append(temp_array)
            j+=1
        i+=1 
    
    # Tries same process again but with more number of periods, if first one
    # didn't find any match.
    if len(Nsid_Msyn)==1:
        length2=200
        Nlist=list(np.arange(1,length2))
        Mlist=list(np.arange(1,length2))
        i=0
        while i<length2-1:
            j=0
            while j<length2-1:
                if np.abs(((Nlist[i]*Psid)-(Mlist[j]*Psyn))/Psid)<0.5:
                    temp_array=[Nlist[i], Mlist[j]]
                    Nsid_Msyn.append(temp_array)
                j+=1
            i+=1 
    # If no match has been found, this creates an unreasonable number of
    # rotations necessary.
    if len(Nsid_Msyn)==1:
        Nsid_Msyn.append([1000,1000])
         
    # Find the minimum possible opposition by summing Nsid and Msyn and
    # minimizing that number.
    best_opp_sum=Nsid_Msyn[1][0]+Nsid_Msyn[1][1]
    k_best= Nsid_Msyn[1]
    for k in Nsid_Msyn:
        if k[0]+k[1]<best_opp_sum: 
            k_best =k
            best_opp_sum=k[0]+k[1]
    
    # Chooses the best Nsid and Msyn from previous minimization
    Nsid=k_best[0]
    Msyn=k_best[1] 
    
    #calculates the opposition period based on the Nsid and Psid.
    P_periopp=Nsid*Psid    
    return Psid, Psyn, Nsid, Msyn, P_periopp


def Purgatorio(arc,first_impact,JD_now):
    """ Calculates the Purgatorio Ratio"""
    Time_left=first_impact-JD_now-365.25
    purg=arc/Time_left
    return purg


def Urgency(Cum_prob, first_impact, JD_now):
    """ Calculates the Urgency Factor """
    Time_left=first_impact-JD_now-365.25
    urg=(10.0+np.log10(Cum_prob))/(Time_left/365.25)
    return urg


def accesshorizons2(targets, Telescope, start_time, stop_times):
    """
    Retrieve the date of minimum Vmag and create a dataframe that returns that
    date as well as the target name, the V_min, the start date for the search,
    the end date for the search, and the H_mag of the object
    
    Inputs:
        targets: a list of targets, in unpacked provisional designation, 
            for which to extract the Horizons data as a single column from a 
            dataframe.
        Telescope: The telescope observatory code to use for the function as a
            string.
        start_time: The date 9 months from now as a string
        stop_times: A list of date that represent the next impact probability
            minus 1, plus the synodic period, given as a single column 
            dataframe.
    Output:
        Vmin_data: a Dataframe containing the Object name, the start date, 
            the end date, the H_magnitude, the Vmin in the time range, and 
            the date that Vmin occurs.
    
    """
    
    # Define important information for Horizon's ephemerides retrieval
    step_size = 1440 # in Minutes ==> 1 day    
    
    # Defining output dataframe
    Vmin_data=pd.DataFrame(columns=['Object', 
                                    'start_date', 
                                    'end_date', 
                                    'H_mag' ,
                                    'Vmin', 
                                    'Vmin_date' ])
    
    # Run through all objects in targets (list)
    for object_name, end_time in zip(targets, stop_times):
        print(object_name)
        max_attempts = 3
        i=0
        while i < max_attempts:
            try:
                # Obtaining data from Horizons
                new_object=object_name.replace(" ","%20")
                new_end_time=end_time.replace(" ","%20")
                response = requests.get(
                    "https://ssd.jpl.nasa.gov/api/horizons.api?"
                    "format=json"
                    "&COMMAND='DES="+new_object
                    +"'&OBJ_DATA='YES'"
                    "&MAKE_EPHEM='YES'"
                    "&EPHEM_TYPE='OBSERVER'"
                    "&CENTER="+Telescope
                    +"&START_TIME="+start_time
                    +"&STOP_TIME='"+str(new_end_time)
                    +"'&STEP_SIZE='"+str(step_size)+"%20min'"
                    "&TLIST_TYPE=CAL"
                    "&QUANTITIES='9'")
                data=pd.DataFrame.from_dict(response.json(),orient="columns")
                new_data=data['result'].str.split('\n', expand=True)
                        
                
                # Obtaining Vmag and date for Vmag
                observable=pd.DataFrame(columns=['date', 'Vmag'])
                i=0
                H_mag = 0.0
                while i < (len(new_data.columns)): 
                    try:
                        temp = new_data[i]['version']
                        if " H= " in temp:
                            index_H = temp.find(" H= ")
                            H_mag = float(temp[index_H 
                                               + len(" H= "):index_H 
                                               + len(" H= ") + 5])
                       
                        if temp[1:3]=='20' or temp[1:4]=='21':
                            date_time=temp[1:18]
                            Vmag=float(temp[24:30])
                            observable.loc[len(observable)]=[date_time, Vmag]
                        i+=1 
                    except:
                        print('no horizon data obtained')
                        i+=1
                    
                # Finding the minimum Vmag, and the corresponding date
                Vmin_index = observable["Vmag"].idxmin()
                Vmin = observable["Vmag"][Vmin_index]
                date_Vmin = observable["date"][Vmin_index]
                
                # Populate dataframe for each object
                Vmin_data.loc[len(Vmin_data)]=[object_name, 
                                               str(start_time), 
                                               str(end_time), 
                                               H_mag, 
                                               Vmin, 
                                               date_Vmin]
                i=3
            except:
                if i < max_attempts - 1:
                    time.sleep(0.25)
                    i+=1
                else:
                    "No Horizon's data"

    return Vmin_data


def get_top_40_VIs():
    """ 
    Obtain the latest 40 VIs on the sentry list and sorts them in the proper
    format for the Priority factor calculations.
    

    Outputs: 
        data: the data of the VI file from sentry list keeping only the top
            40 elements.
    """

    # Send Query to Sentry API
    response = requests.get("https://ssd-api.jpl.nasa.gov/sentry.api")
    data = pd.json_normalize(response.json()["data"])
    
    # format data to only keep latest 40 objects (and exclude numbered objects)
    data = data[data["des"].str.contains(" ")]
    data = data.sort_values(by="des", ascending=False)
    data = data.head(40)

    return data


def get_specific_VIs(object_list):
    """ 
    Obtain the given objects on the object_list from the sentry list and sorts 
    them in the proper format for the Priority factor calculations.
    
    Input:
        object_list: A list of object for which to calculate the PF
    Outputs: 
        data: the data of the VI file from sentry list keeping only the objects
            requested in the object_list.
    """

    # Send Query to Sentry API
    response = requests.get("https://ssd-api.jpl.nasa.gov/sentry.api")
    data = pd.json_normalize(response.json()["data"])
    
    # format data to only keep latest 40 objects (and exclude numbered objects)
    data = data[data["des"].isin(object_list)]

    return data

    
def PF_data(data_all):
    """
    Calculates all the values for the priority factor calculations and returns
    a dataframe with those newly calculated values.
    
    Input:
        data_all: the dataframe of the combined sentry VIs and MPC 1-line
            requests obtained
    Output:
        VIoutput: The dataframe containing all the PF calculations and 
            important information from data_all
    """
    
    #Obtaining today's date in JD
    ts=pd.Timestamp(datetime.now(timezone.utc))
    JD_now=ts.to_julian_date()

    # Calculating the resulting data for the Priority Factor calculation

    # Create a new data frame to put all the results    
    column_names=['IP',
                  'PSid',
                  'PSyn', 
                  'Nsid', 
                  'Msyn', 
                  'P_PeriOpp', 
                  'Urgency', 
                  'Log(Pr*Urg.)', 
                  'P. R.']
    new_data=pd.DataFrame(columns=column_names)

    i=0
    while i< len(data_all['a']):
        #Obtaining the synodic and sideral period
        Psid, Psyn, Nsid, Msyn, P_periopp = Opposition(data_all['a'][i])
        First_impact_JD=((data_all['First_impact'][i]-2000)*365.25)+2451545

        
        # Calculating Impact Priority, if it is lower than when it comes back
        # to opposition, it has a priority of 1.
        if (First_impact_JD - Psyn*365.25) < JD_now:
            IP=1;
        else:
            IP=0;
        
        #Calculating the Purgatorio Value
        Purgatorio_ratio = Purgatorio(data_all['arc_length'][i], 
                                      First_impact_JD, 
                                      JD_now)
        
        #Caluculate the Urgency
        Urgency_value= Urgency(float(data_all['ip'][i]), 
                               First_impact_JD, 
                               JD_now)

        
        #Calculate the Priority Factor
        Priority_factor= np.log10(Purgatorio_ratio*Urgency_value)

        # Fill out the "new_data" dataframe
        temp=pd.DataFrame({'IP' : IP, 
                           'PSid' : Psid, 
                           'PSyn': Psyn, 
                           'Nsid':Nsid, 
                           'Msyn':Msyn, 
                           'P_PeriOpp': P_periopp, 
                           'Urgency': Urgency_value, 
                           'Log(Pr*Urg.)': Priority_factor, 
                           'P. R.': Purgatorio_ratio}, 
                          index=[0])
        new_data=pd.concat([new_data, temp],ignore_index=True)
        i+=1  
    
    # Concatinate data_all and New_data to form VIoutput
    data_out=[data_all['desig'], 
              data_all['First_impact'], 
              data_all['last_impact'], 
              data_all['n_imp'], 
              data_all['ip'], 
              data_all['H'], 
              data_all['des'],
              new_data['IP'], 
              new_data['P. R.'], 
              new_data['PSid'], 
              new_data['PSyn'], 
              new_data['Nsid'], 
              new_data['Msyn'], 
              new_data['P_PeriOpp'], 
              new_data['Urgency'], 
              new_data['Log(Pr*Urg.)'], 
              data_all['arc length'], 
              data_all['ps_cum'] ]
    headers=['Prov. Des.', 
             'Year', 
             'Range', 
             '#Impacts', 
             'Cum Prob', 
             'H mag', 
             'Packed Des', 
             'IP', 
             'P. R.', 
             'Psid', 
             'PSyn', 
             'Nsid', 
             'MSyn', 
             'P_PeriOpp', 
             'Urgency', 
             'Log(PR*Urg.)', 
             'ObsArc(d)', 
             'Cum Palermo']
    VIoutput = pd.concat(data_out, axis=1, keys=headers)
    
    return VIoutput


def years_VI_impact(VIoutput):
    """
    Calculating number of years until impact plus 1 minus the synodic period
    """
    
    next_year = datetime.now() + timedelta(days=365)
    next_year_year = next_year.year
    
    column_names=['S','T','stop_time']
    temp=pd.DataFrame(columns=column_names)
    i=0
    while i< len(VIoutput['Prov. Des.']):
        S_value=VIoutput['Year'][i]+1-VIoutput['PSyn'][i]
        if S_value > next_year_year:
            S = S_value
        else:
            S = next_year_year
        T=(S-1900)*365.2425

        #converting

        U=pyasl.decimalYearGregorianDate(S, "yyyy-mm-dd hh:mm:ss")
        
        temp.loc[len(temp)]=[S,T,U]
        #print(dt.strftime("%Y-%m-%d %H:%M"))
        
        i+=1
    
    new_VIoutput=pd.concat([VIoutput,temp],axis=1)
    return new_VIoutput


def clean_arc_length(data_all):
    # Splitting necessary Columns such that we have a measured arc_length
    data_all['range'] = data_all['range'].values.astype(str)
    data_all[['First_impact','last_impact']] = data_all['range'].str.split(
        '-', n=2, expand=True)
    data_all['First_impact'] = data_all['First_impact'].values.astype(int)
    
    # Filling the "arc_length") newly created column with foo data
    data_all['arc_length'] = data_all['First_impact'].values.astype(int)

    # Changing the arc_length to either a number of days (as int) or taking 
    # it from the range of years (as float). If there is no given range, we 
    # assume a very small arc range of 0.2 days.
    i=0
    while i < len(data_all['arc length']):
        if '-' in data_all['arc length'][i]:
            templist=data_all['arc length'][i].split('-',1)
            data_all['arc_length'][i]=((float(templist[1])
                                        -float(templist[0])) * 365.2425)
        else:   
            templist=data_all['arc length'][i].split(' ',1)    
            data_all['arc_length'][i]=int(templist[0])
        if data_all['arc_length'][i]==0:
            data_all['arc_length'][i]=0.2
        i+=1
    return data_all


def main():


    # Obtaining latest 40 VI from sentry's VI list or from a given list
    # of objects. Chose one of the two options below:
   
        
    #########
    # #   Option 1 --> weekly PF calculations:
    # data_sentry = get_top_40_VIs()
    #########
    
    
    ###########
    #   Option 2 --> Getting specific VIs to calculate:
    filename = 'VI_list.txt'
    # Open the file in read mode
    with open(filename, 'r') as file:
        # Read the content of the file
        content = file.read()    

        # Split the content into lines and create a list
        object_list = content.splitlines()
    data_sentry = get_specific_VIs(object_list)
    ###########

    
    # Preamble (set up time, and chose parameters)
    now = datetime.now()
    nine_month = now + timedelta(days=274)
    date_today = now.strftime('%Y-%m-%d')
    start_time = nine_month.strftime('%Y-%m-%d')   
    date = date_today.replace('-', '')
    date_short = date[2:]
    obscode = '691'



    # Obtaining MPC 1-line for data, then merging it with data_sentry
    data_MPC_1_line = add_files_functions.get_MPC_1_line(data_sentry["des"])
    column_titles = ["packed desig", 
                     "H", 
                     "G", 
                     "ephoch", 
                     "mean anom", 
                     "arg perihel (deg)", 
                     "long asc node (Deg)", 
                     "i", 
                     "e", 
                     "mean daily motion (Deg)", 
                     "a", 
                     "U", 
                     "ref", 
                     "#obs", 
                     "#opp", 
                     "arc length", 
                     "rms resid", 
                     "course indicator", 
                     "precise indicator of perturbers", 
                     "computer", 
                     "class", 
                     "desig", 
                     "last obs in orbit sol'n"]
    data_MPC_1_line.columns = column_titles
    
    data_all = pd.merge(data_sentry, 
                        data_MPC_1_line, 
                        left_on="des", 
                        right_on="desig", 
                        how='outer')
    # data_all.to_csv("test.csv", index=False)
    
    data_all_new = clean_arc_length(data_all)


    # Calculating the PF values
    VIoutput = PF_data(data_all_new)
    
    # adding years until impact
    new_VIoutput = years_VI_impact(VIoutput)

    # Measuring the minimum Vmag and the dates using Horizons
    Vmin_data = accesshorizons2(new_VIoutput["Prov. Des."],
                                obscode,
                                start_time,
                                new_VIoutput["stop_time"])

    # Create final dataframe, and save it to CSV
    final_data = pd.merge(new_VIoutput, 
                          Vmin_data, 
                          left_on="Prov. Des.", 
                          right_on="Object", 
                          how='outer')
    # Change the format of the stop_time to a string with quotes around it.
    i = 0
    while i < len(final_data['stop_time']):
        final_data['stop_time'][i]=(f"'{final_data['stop_time'][i]}'")
        i+=1
    
    
    
    final_data.to_csv("Finished_VI_PF_" + date_short + ".csv",  
                      index=False, 
                      header=False)

    
    
if __name__ == "__main__":  main() 