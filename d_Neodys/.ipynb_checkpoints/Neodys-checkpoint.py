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




def add_space(list_object):
    list_object[0] = list_object[0].str[:4] + ' ' + list_object[0].str[4:]    
    return list_object

def get_MPC_1_line(my_list):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = ChromeService(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://minorplanetcenter.net/iau/MPEph/MPEph.html")   
    if os.path.exists('/Users/cassandralejoly/Downloads/elements.txt'):
        os.unlink('/Users/cassandralejoly/Downloads/elements.txt')       
    reset=driver.find_element(by=By.XPATH, value="//input[@type='reset']")
    submit=driver.find_element(by=By.XPATH, value="//input[@type='submit']")
    text_box=driver.find_element(by=By.TAG_NAME, value="textarea")
    MPC_1_line=driver.find_element(by=By.XPATH, value="//input[@value='-1']")
    reset.click()
    text_box.send_keys(my_list)
    MPC_1_line.click()
    submit.click()
    time.sleep(5)
    columns=[(0,7),(7,13),(14,19), (19,25), (25,35), (35,46), (46,57), (57,68), (68,79),(79,91),(91,103),(103,106), (106,116), (116,122), (122,126), (126,136), (136,141), (141,145), (145,149),(149,160), (160,165), (165,191), (191,202)]
    data=pd.read_fwf('~/Downloads/elements.txt', header=None, colspecs=columns)
    os.unlink('/Users/cassandralejoly/Downloads/elements.txt')
    driver.close()   
    return data

def Horizons(Object_name,date):
    Telescope=str(691)
    new_object=Object_name.replace(" ","%20")
    #print(new_object)
    response = requests.get("https://ssd.jpl.nasa.gov/api/horizons.api?format=json&CENTER="+Telescope+"&TLIST='"+date+"'&TLIST_TYPE=CAL&COMMAND='DES="+new_object+"&QUANTITIES='38'")
    #print(response.json())
    data=pd.DataFrame.from_dict(response.json(),orient="columns")
    #print(data)
    new_data=data['result'].str.split('\n', expand=True)
    i=0
    while i<(len(new_data.columns)):
        temp=new_data[i]['version']
        if temp[1:5]=='2022':
            try:
                float(temp[32:41])
            except:
                Pos_uncertainty=float(4900.0)
            else:
                Pos_uncertainty=float(temp[32:41])           
        i+=1
    return Pos_uncertainty

def JPL_U(Object_name):

    new_object=Object_name.replace(" ","%20")
    response = requests.get("https://ssd-api.jpl.nasa.gov/sbdb.api?sstr="+new_object+"")
    data=pd.DataFrame.from_records(response.json())
    #data.to_csv('test_2.csv')
    U=data['orbit'][13]
    #print('U')
    #print(U)
    LastObsUse=data['orbit'][31]
    return U,LastObsUse


  
def sortall(today_date,sort_dirty,outfile):
    print('Sorting\n')
    min_uncert=float(1.0)   
    today_date_datetime=datetime.datetime.strptime(today_date, '%Y-%m-%d')
    year_from_date=today_date_datetime-datetime.timedelta(days=365.2425)
    PHA_all = sort_dirty
    Max_uncertainty=float(4800.0) #in arcseconds
    keep=pd.DataFrame()
    i=0
    while i<len(PHA_all["uncert1"]):
        print(i)
        try:
            Date_obs_temp=datetime.datetime.strptime(PHA_all["LastObsUsed"][i], '%Y-%m-%d')
        except:
            Date_obs_temp=datetime.datetime.strptime(PHA_all["LastObsUsed"][i], '%m/%d/%y')
           
            
        if float(PHA_all["uncert1"][i])<Max_uncertainty and float(PHA_all["uncert2"][i])<Max_uncertainty:
            if float(PHA_all["uncert1"][i])>min_uncert or float(PHA_all["uncert2"][i])>min_uncert:
                temp=pd.DataFrame([PHA_all.loc[i,:]])
                temp2=[keep, temp]
                keep=pd.concat(temp2)
                print('Kept1')

            elif float(PHA_all["uncert1"][i])<min_uncert and float(PHA_all["uncert2"][i])<min_uncert and float(PHA_all["arc"][i])<float(100) and Date_obs_temp < year_from_date:
                temp=pd.DataFrame([PHA_all.loc[i,:]])
                temp2=[keep, temp]
                keep=pd.concat(temp2)
                print('kept2')

            elif float(PHA_all["uncert1"][i])<min_uncert and float(PHA_all["uncert2"][i])<min_uncert :
                if (float(PHA_all["U1"][i]) in [0,1]) and (float(PHA_all["U2"][i]) in [0,1]):
                    print("not kept")
                else:                
                    temp=pd.DataFrame([PHA_all.loc[i,:]])
                    temp2=[keep, temp]
                    keep=pd.concat(temp2)
                    print("kept3")
            else:
                print("not kept")
        else:
            print('not kept')
        i+=1
    #print(keep)
    desig=keep['desig']    
    #print(desig)
    desig.to_csv(outfile,sep='\n',header=False,index=False)
    
    
    #remove last line of text file
    fd=open(outfile,"r")
    d=fd.read()
    fd.close()
    m=d.split("\n")
    s="\n".join(m[:-1])
    fd=open(outfile,"w+")
    for i in range(len(s)):
        fd.write(s[i])
    fd.close()



def main():

    filename=input("What is the file name (must be in same directory as code)? ex: neodys_list_date.txt   ")

    date1='2022-10-07 07:30' #input("What is the first date and time? ex: 2022-03-29 07:30 ")
    date2='2022-10-11 07:30' #input("what is the second date and time? ex: 2022-04-10 07:30 ")
    today_date='2022-10-07' #input("What is today's date? ex: 2022-02-14   ")



    file=pd.read_csv(filename, header=None)
    file=add_space(file)
    file.to_csv(r'space_'+filename,header=None, index=None, sep='\n')



    #remove last line of text file
    fd=open('space_'+filename,"r")
    d=fd.read()
    fd.close()
    m=d.split("\n")
    s="\n".join(m[:-1])
    fd=open('space_'+filename,"w+")
    for i in range(len(s)):
        fd.write(s[i])
    fd.close()




    with open('space_'+filename) as f:
        lines = f.readlines()
    data=pd.DataFrame()
    
    
    #Get MPC 100 lines at a time
    i=0
    for i in range(0, len(lines), 100):
        temp=get_MPC_1_line(lines[i:i+100])
        data1=[data, temp]
        data=pd.concat(data1)


    # Get HORIZONS: 
    horizons_data=pd.DataFrame()
    for i in lines:
        print(i)
        Pos_uncertainty1=Horizons(i, date1)
        Pos_uncertainty2=Horizons(i, date2)
        U,LastObsUse=JPL_U(i)
        temp=pd.DataFrame({'uncert1':[Pos_uncertainty1],'uncert2':[Pos_uncertainty2],'U2':[U],'LastObsUsed':[LastObsUse]})
        data3=[horizons_data, temp]
        horizons_data=pd.concat(data3, ignore_index=True)
    print(horizons_data)   
    
    data.rename(columns={0: 'packed desig', 11: 'U1', 15:'arc length', 21: 'desig', 22:'last obs in orbit' }, inplace=True)

    MPC_keep=data[['packed desig','U1','desig', 'last obs in orbit']]
    
    tmpDF = pd.DataFrame(columns=['arc','length'])
    tmpDF[['arc','length']] = data['arc length'].str.split('[- ]', expand=True)
    #print(tmpDF)
    
    tmpDF.reset_index(inplace=True)
    MPC_keep.reset_index(inplace=True) 
    horizons_data.reset_index(inplace=True)

    sort_dirty=pd.concat([MPC_keep,horizons_data,tmpDF], axis=1)
    #print(sort_dirty)
    sort_dirty.to_csv('sort_dirty.csv',index=False)



    input(' Correct for LastObsUsed \n Press enter when ready')


    Neodys_data=pd.read_csv('sort_dirty.csv')

    
    sortall(today_date,Neodys_data,'d_NEODYS_sorted.txt')

    

    
        
    
    
    
    
    
if __name__ == "__main__":  main()
