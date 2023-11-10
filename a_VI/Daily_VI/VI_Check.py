#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 17 07:06:19 2023


Program to check which object is observable until which date for each of the three telescope we check each time in VI dailies

@author: cassandralejoly
"""


import numpy as np
import pandas as pd
import requests
from pandas import json_normalize
import json
import datetime
from datetime import timezone
import sys


def mjd_to_date(mjd):
    base_date = datetime.datetime(1858, 11, 17)
    delta = datetime.timedelta(days=mjd)
    target_date = base_date + delta
    return target_date



def Horizons_import(Object_name,start_time,end_time,step_size_min,Telescope):
    
    new_object=Object_name.replace(" ","%20")
    
    #for asteroid
    response = requests.get("https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND='DES="+new_object+"&OBJ_DATA='YES'&MAKE_EPHEM='YES'&EPHEM_TYPE='OBSERVER'&CENTER="+Telescope+"&START_TIME="+start_time+"&STOP_TIME="+end_time+"&STEP_SIZE='"+str(step_size_min)+"%20min'&SKIP_DAYLT='YES'&TLIST_TYPE=CAL&AIRMASS='2.9'&QUANTITIES='1,3,9,25,38'")
    #print(response.json())
    data=pd.DataFrame.from_dict(response.json(),orient="columns")
    #print(data)
    new_data=data['result'].str.split('\n', expand=True)
    #print(new_data)
    new_data.to_csv('test.csv',index=False)
    observable=pd.DataFrame(columns=['MJD','RA', 'DEC', 'RA_rate', 'DEC_rate', 'Brightness', 'lunar_distance', 'POS_3sig', 'Twilight'])
    i=0
    while i<(len(new_data.columns)): 
        try:
            temp=new_data[i]['version']
            #print(temp)
            if temp[1:4]=='202' or temp[1:4]=='201' or temp[1:4]=='200':
                date=temp[1:12]
                if date[5:8]=='Jan':
                    month=1
                elif date[5:8]=='Feb':
                    month=2
                elif date[5:8]=='Mar':
                    month=3
                elif date[5:8]=='Apr':
                    month=4
                elif date[5:8]=='May':
                    month=5
                elif date[5:8]=='Jun':
                    month=6
                elif date[5:8]=='Jul':
                    month=7
                elif date[5:8]=='Aug':
                    month=8
                elif date[5:8]=='Sep':
                    month=9
                elif date[5:8]=='Oct':
                    month=10
                elif date[5:8]=='Nov':
                    month=11
                elif date[5:8]=='Dec':
                    month=12 
                time=temp[13:18]
                MJD=datetime.date(int(date[0:4]),month,int(date[9:11])).toordinal()+(int(time[0:2])/24)+(int(time[3:5])/(24*60))+1721424.50000
                RA=temp[23:34]   
                RA_good=float(RA[0:2])+(float(RA[3:5])/60)+(float(RA[6:11])/3600) #Ra in decimal hours
                DEC=temp[35:46]
                if float(DEC[0:3]) > 0:
                    DEC_good=float(DEC[0:3])+(float(DEC[4:6])/60)+(float(DEC[7:12])/3600)
                elif float(DEC[0:3]) < 0:
                    DEC_good=float(DEC[0:3])-(float(DEC[4:6])/60)-(float(DEC[7:12])/3600)
                RA_rate=float(temp[47:56])
                DEC_rate=float(temp[57:66])
                Brightness=float(temp[69:75])
                Lunar_distance=float(temp[86:91])
                POS_3sig=float(temp[102:112])
                twilight=str(temp[19:20])
                observable.loc[len(observable)]=[MJD,RA_good,DEC_good,RA_rate,DEC_rate,Brightness,Lunar_distance,POS_3sig,twilight]
            i+=1 
        except:
            print('no horizon data obtained')
            #print(i)
            i+=1
    #observable.rename(columns={0:'MJD', 1:'RA', 2:'DEC', 3:'RA_rate', 4:'DEC_rate', 5:'Brightness', 6:'POS_3sig'}, inplace=True)
    # RA and Dec in degrees, MJD in days
    #print(observable)
    return observable





def Check_observability(Object_ephem,Mag_max,lunar_elong_max,rates_max,uncert_max):
    observable_VIs=pd.DataFrame(columns=['MJD','RA', 'DEC', 'RA_rate', 'DEC_rate', 'Brightness', 'lunar_distance', 'POS_3sig','Twilight'])
    i=0
    while i<len(Object_ephem['MJD']):
        if Object_ephem['Twilight'][i]==" ":
            if Object_ephem['Brightness'][i]<Mag_max and Object_ephem['POS_3sig'][i]<uncert_max and abs(Object_ephem['RA_rate'][i])<rates_max and abs(Object_ephem['DEC_rate'][i])<rates_max and Object_ephem['lunar_distance'][i]>lunar_elong_max:
                 observable_VIs.loc[len(observable_VIs)]=[Object_ephem['MJD'][i],Object_ephem['RA'][i],Object_ephem['DEC'][i],Object_ephem['RA_rate'][i],Object_ephem['DEC_rate'][i],Object_ephem['Brightness'][i],Object_ephem['lunar_distance'][i],Object_ephem['POS_3sig'][i],Object_ephem['Twilight'][i]]   

        i+=1
    try:
        return observable_VIs
    except:
        pass


def jd_to_utc(jd):
    jd_base = 2440587.5
    timestamp = (jd - jd_base) * (24 * 60 * 60)
    utc_datetime = datetime.datetime.utcfromtimestamp(timestamp)
    return utc_datetime



def main():
    
    filename='VI_list.txt'
    Telescope=['691','W84','T16'] 
    #Telescope=['691','W84','I11','568']


    # Get the current date and time
    now = datetime.datetime.now()
    
    # Calculate the dates for tomorrow and the day after
    tomorrow = now + datetime.timedelta(days=1)
    six_month = now + datetime.timedelta(days=182)

    
    
    
    
    # Format the dates as strings with the time 7:30
    date_today=now.strftime('%Y-%m-%d')
    start_time = tomorrow.strftime('%Y-%m-%d')
    end_time = six_month.strftime('%Y-%m-%d')
    #print(start_time)
    
    
    

    
    #parameters 
    #start_time='2023-06-07'
    #end_time='2023-06-08'
    step_size_min=60 #in minutes
    Mag_max=[23,24,25]
    lunar_elong_max=65 #degrees
    rates_max=600   #arcsec/hour
    uncert_max=3600 #arcsec
    list_of_Observable_VI=[]

    with open(filename) as f:
        Object_name = f.readlines()
        
    for VI in Object_name:
        
        print('\n \n object name')
        print(VI)
        i=0
            
        while i<len(Telescope):
            
            max_attempts=3
            attempts=0
            
            while attempts < max_attempts:
            
                try: 
                    Object_ephem=Horizons_import(VI, start_time, end_time, step_size_min, Telescope[i])

                    break
                except Exception as e:
                    attempts += 1
                    print(f'Attempt {attempts} failed with error: {e}')

            else:
                print(f"All attempts fail for telescope {Telescope}. Moving on.")

                    
            observable_VIs=Check_observability(Object_ephem, Mag_max[i], lunar_elong_max, rates_max, uncert_max)
            print('Telescope: '+ Telescope[i])
            try:
                print(jd_to_utc(float(observable_VIs['MJD'].tail(3).iloc[0])))
                print(jd_to_utc(float(observable_VIs['MJD'].tail(3).iloc[1])))
                print(jd_to_utc(float(observable_VIs['MJD'].tail(3).iloc[2])))
                print(observable_VIs.tail(1).iloc[:,3:])
            except:
                print("No Observations found")


            i+=1
        #print(list_of_Observable_VI)
        print('\n\n\n')
    
    


    
if __name__ == "__main__":  main()