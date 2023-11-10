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
from datetime import datetime,timezone
from PyAstronomy import pyasl
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import requests
import time
from os import path
pd.options.mode.chained_assignment = None





def P_sid(a):
    P=np.sqrt(a**3)
    return P


def P_syn(a):
    P=1/np.abs((1/P_sid(a))-1)
    return P

def Opposition(a):
    Psid=P_sid(a)
    Psyn=P_syn(a)
    length=100
    Nlist=list(np.arange(1,length))
    Mlist=list(np.arange(1,length))
    i=0
    Nsid_Msyn=[[10000,10000]] 
    while i<length-1:
        j=0
        while j<length-1:
#            print(((Nlist[i]*Psid)-(Mlist[j]*Psyn)/Psid))
            if np.abs(((Nlist[i]*Psid)-(Mlist[j]*Psyn))/Psid)<0.05:
                temp_array=[Nlist[i], Mlist[j]]
                Nsid_Msyn.append(temp_array)
            j+=1
        i+=1 
    #print(len(Nsid_Msyn))
    if len(Nsid_Msyn)==1:
        length2=200
        Nlist=list(np.arange(1,length2))
        Mlist=list(np.arange(1,length2))
        i=0
        while i<length2-1:
            j=0
            while j<length2-1:
                #print(((Nlist[i]*Psid)-(Mlist[j]*Psyn)/Psid))
                if np.abs(((Nlist[i]*Psid)-(Mlist[j]*Psyn))/Psid)<0.5:
                    temp_array=[Nlist[i], Mlist[j]]
                    Nsid_Msyn.append(temp_array)
                j+=1
            i+=1 
    if len(Nsid_Msyn)==1:
        Nsid_Msyn.append([1000,1000])
         
    
    best_opp_sum=Nsid_Msyn[1][0]+Nsid_Msyn[1][1]
    k_best= Nsid_Msyn[1]
    for k in Nsid_Msyn:
        if k[0]+k[1]<best_opp_sum: 
            k_best =k
            best_opp_sum=k[0]+k[1]
        
    Nsid=k_best[0]
    Msyn=k_best[1] 
    P_periopp=Nsid*Psid    
    return Psid, Psyn, Nsid, Msyn, P_periopp


def Purgatorio(arc,first_impact,JD_now):
    Time_left=first_impact-JD_now-365.25
    purg=arc/Time_left
    return purg


def Urgency(Cum_prob, first_impact, JD_now):
    Time_left=first_impact-JD_now-365.25
    urg=(10.0+np.log10(Cum_prob))/(Time_left/365.25)
    return urg

    


def accesshorizons(targets, targetpathfile, obscode, start_time, stop_times):
    print("number of targets: ", len(targets), " length of 1st target name: ", len(targets[0]))
    for i in targets:
        if len(i) > 10: raise ValueError('File was not read correctly.')
    j=0
    while j<len(targets):        
        #targets[j]= targets[j].replace(b'\r', ' ')  #remove hard stop from close approach table objects -->may not be necessary anymore with python3
#        targlist.append("'DES= "+targets[j].replace('_',' ')+"'")
        j +=1

    s=targetpathfile.rsplit('.txt')
# create a file for asteroid names and JPL H, V, uncert, U code, date of last obs used in orbit sol'n, orbital classification 
    outputpathfile = s[0] + "_Vmin_Data_" + obscode + ".txt"  #HVUncertULastObsClass
    outVminfile = open(outputpathfile, 'w')
    header = '{:15}{:20}{:20}{:10}{:10}{:35} \n'.format('Target','start time','stop time','Hmag','Vmin','Vmin Date           Time Step=1d')
    outVminfile.write(header)
    
#    outstatusfile = open(s[0] + "_status.txt", 'w')    
    
    header="!$$SOF\n"
    footer="!$$EOF"
    step1="COMMAND="
    step2="\nMAKE_EPHEM='YES'\nTABLE_TYPE='OBSERVER'\nCENTER='"+obscode
    step3="'\nSTART_TIME="+start_time+"\nSTOP_TIME="
    step4="\nSTEP_SIZE='1 d'\nQUANTITIES='1,3,8,9,19,20,24,25,37,38'\nANG_FORMAT='DEG'\nCSV_FORMAT='YES'\n"


#prepare input to JPL Horizons form
    url="https://ssd.jpl.nasa.gov/api/horizons_file.api"
#    for targ in targlist:  #iterate through target list  


#*****make this a while loop
    i=0
    temp=pd.DataFrame(columns=['asttemp','start_time', 'datetemp', 'Hmag','minV','Vmindate'])
    while i< len(targets):
        asttemp=targets[i]
        datetemp="'"+stop_times[i]+"'"

#          outstatusfile.write(asttemp + '\n')  #added to follow/test progress
        targ="'DES= "+asttemp.replace('_',' ')+"'"
        print(targ)        
#figure out stop time from while
        quants=header+step1+targ+step2+step3+datetemp+step4+footer
        response=requests.post(url,data={'format':'text'},files={'input':quants})
        output=response.text
        the_lines=output.split('\n')   #separate data into individ lines
#        lineabove = [x for x in the_lines if "ROTPER" in x]  #search for html line above Hmag
#        indexabove= the_lines.index(lineabove[0])      #get the index of that line
#        linecontent = the_lines[indexabove+1]      #increment to index of Hmag value
        Hline=the_lines[19]
        absmagplus=Hline.split('=')[1] #strip off the beginning string to Hmag value [was linecontent]
        Hmag=absmagplus.split(' ')[1] 
        #strip off end string, print value to file       
        starteph=0
        counter=0
        date=[]  #declare lists in which to save data from eph lines
        Vmag=[]

        for line in the_lines:  #for each line in ephemeris
            line = line.strip()
            # insert query to grab H     
            if line == "$$SOE":
                #print "Started ephemeris section" #added to follow/test progress
                starteph = 1
            elif line == "$$EOE":
                print("Ended ephemeris section") #added to follow/test progress
                break
            if starteph == 1:
#                print line
                lineparts = line.split(",")
                if len(lineparts) >= 17:   # good line, now parse it  
                    date.append(lineparts[0])
#                    print(float(lineparts[9]))
                    Vmag.append(float(lineparts[9])) #poor approx apparent V
#                    print(repr(lineparts[17]))
#                    print(lineparts[0],'date', lineparts[9], 'mag')
 #                   sys.exit()
                    counter = counter + 1  #lines in the ephemeris

        Vmag=np.array(Vmag)     
        minV = min(Vmag)
        result=np.where(Vmag == minV)  #find where Vmag is equal to Vmin
        IndexArray=result[0]     # tuple of indices where the min V values are found
        indices=np.array(IndexArray)
        Vmindate=date[indices[0]]
        output = '{:15}{:20}{:21}{:10}{:<10}{:20} \n'.format(asttemp,start_time,datetemp,Hmag,minV,Vmindate)
        #make the widths of columns 14char, 8char, etc.
        outVminfile.write(output)
        time.sleep(1)
        i=i+1
        temp.loc[len(temp)]=[asttemp,start_time,datetemp,Hmag,minV,Vmindate]
        
    outVminfile.close()
    return temp
        











def main():
    targetpathfile=input("What is the targetpath filename? Ex. cassandra/new_table.xlsx   ") 
    output_name=input("What is the output filename? Ex. VIoutput_date.csv   ") 




    obscode=input("What is your observatory code?  Example:  691  ")
    start_time=input("What is your start time (9 months in future)?  Example: '2023-04-01 00:00'  ")
    




    data_all = pd.read_excel(targetpathfile)
#    for col in data_all.columns:
#        print(col)
    
    #Splitting necessary Columns
    data_all['Year Range  ']=data_all['Year Range  '].values.astype(str)
    data_all[['First_impact','last_impact']]=data_all['Year Range  '].str.split('-', n=2, expand=True)
    data_all['First_impact']=data_all['First_impact'].values.astype(int)
    data_all['arc_length']=data_all['First_impact'].values.astype(int)

    i=0
    #print(len(data_all['arc length']))

    while i<len(data_all['arc length']):
        if '-' in data_all['arc length'][i]:
            templist=data_all['arc length'][i].split('-',1)
            data_all['arc_length'][i]=(int(templist[1])-int(templist[0]))*365.2425
        else:   
            templist=data_all['arc length'][i].split(' ',1)    
            data_all['arc_length'][i]=int(templist[0])
        if data_all['arc_length'][i]==0:
            data_all['arc_length'][i]=0.2
        i+=1

    #Obtaining today's date in JD
    today=datetime.now(timezone.utc)
    ts=pd.Timestamp(datetime.now(timezone.utc))
    JD_now=ts.to_julian_date()



#######
    #The Following will need to be done for each row in sheet    
    column_names=['IP','PSid','PSyn', 'Nsid', 'Msyn', 'P_PeriOpp', 'Urgency', 'Log(Pr*Urg.)', 'P. R.']
    new_data=pd.DataFrame(columns=column_names)

    i=0
    while i< len(data_all['a']):
        #Obtaining the synodic and sideral period
        Psid, Psyn, Nsid, Msyn, P_periopp = Opposition(data_all['a'][i])
        #print("This part worked")
        #Obtaining the first impact date (year) in JD
        First_impact_JD=((data_all['First_impact'][i]-2000)*365.25)+2451545 #First impact in jD
        #print(First_impact_JD)
        
        #Calculating Impact Priority
        if (First_impact_JD - Psyn*365.25) < JD_now:
            IP=1;
        else:
            IP=0;
        
        
        
        #Calculating the Purgatorio Value
        Purgatorio_ratio = Purgatorio(data_all['arc_length'][i], First_impact_JD, JD_now)
        
        #Caluculate the Urgency
        Urgency_value= Urgency(data_all['Impact Probability (cumulative)'][i], First_impact_JD, JD_now)

        
        #Calculate the Priority Factor
        Priority_factor= np.log10(Purgatorio_ratio*Urgency_value)


        temp=pd.DataFrame({'IP' : IP, 'PSid' : Psid, 'PSyn': Psyn, 'Nsid':Nsid, 'Msyn':Msyn, 'P_PeriOpp': P_periopp, 'Urgency': Urgency_value, 'Log(Pr*Urg.)': Priority_factor, 'P. R.': Purgatorio_ratio}, index=[0])
        new_data=pd.concat([new_data, temp],ignore_index=True)

        i+=1
    



#######
    # Creating the output file
    data_out=[data_all['desig'], data_all['First_impact'], data_all['last_impact'], data_all['Potential Impacts  '], data_all['Impact Probability (cumulative)'], data_all['H'], data_all['Object Designation  '],new_data['IP'], new_data['P. R.'], new_data['PSid'], new_data['PSyn'], new_data['Nsid'], new_data['Msyn'], new_data['P_PeriOpp'], new_data['Urgency'], new_data['Log(Pr*Urg.)'], data_all['arc length'], data_all['Palermo Scale (cum.)'] ]
    headers=['Prov. Des.', 'Year', 'Range', '#Impacts', 'Cum Prob', 'H mag', 'Packed Des', 'IP', 'P. R.', 'Psid', 'PSyn', 'Nsid', 'MSyn', ' P_PeriOpp', 'Urgency', 'Log(PR*Urg.)', 'ObsArc(d)', 'Cum Palermo']
    VIoutput=pd.concat(data_out, axis=1, keys=headers)
    
    #VIoutput.to_csv(output_name,  index=False)
    
    
    
    #### adding lines to new data_frame
    
    column_names=['S','T','U']
    temp=pd.DataFrame(columns=column_names)
    i=0
    while i< len(VIoutput['Prov. Des.']):
        S_value=VIoutput['Year'][i]+1-VIoutput['PSyn'][i]
        if S_value>2024:
            S=S_value
        else:
            S=2024
        T=(S-1900)*365.2425

        #converting

        U=pyasl.decimalYearGregorianDate(S, "yyyy-mm-dd hh:mm:ss")
        
        temp.loc[len(temp)]=[S,T,U]
        #print(dt.strftime("%Y-%m-%d %H:%M"))
        
        i+=1
    
    new_VIoutput=pd.concat([VIoutput,temp],axis=1)
    #clean_scan_data.loc[len(clean_scan_data)]=[scan_data['Path'][i],MJD,RA_good,DEC_good]    
  
    new_VIoutput.to_csv("new_"+output_name,  index=False, header=False)










    ####VI portion:
    targetpathfile='new_'+output_name
    target_dir,filename=path.split(targetpathfile)         
        
    #for input file: open, read, split into lines, then close.
    target_file = open(targetpathfile,'r')    
    temp=target_file.read()
    inputlines=temp.split('\n')  #'\r'
    target_file.close()
        
    # make table [array of arrays] out of VIoutput_.txt input
    inputtable=[]
    for line in inputlines:
#        print line
        if len(line) < 1: continue   #ignore empty lines (the last line is empty)
        linelist=line.split(',')
#        print linelist[0]
        inputtable.append(linelist)
    targets=[]
    firstimpactyr=[]
    SynodicP=[]
    stop_times=[]
    #make arrays of targets, 1st impact yr, and synodic period
    for row in inputtable:  
#        #print row 
#        target1=row.split('\n')[1] #strip off the beginning string to Hmag value
        targets.append(row[0])
        row[1]=row[1].replace('\r','')
        row[1]=row[1].replace(' ','')
        row[1]=row[1].replace('\n','')       
        row[1]=np.array(row[1])
        firstimpactyr.append(float(str(row[1])))
        row[10]=row[10].replace(' ','')
        SynodicP.append(float(row[10]))
        row[20]=row[20].replace('\r','')
        stop_times.append(row[20])    #[18] for orig input format
    print(stop_times)
#    print 'ready to input'
        #calculate stop_time
       # run prov desigs through accesshorizons
    
    outfile = accesshorizons(targets,targetpathfile,obscode,start_time,stop_times)
#    print "Find your VI Vmin output data at " + outfile
    
    final_data=pd.concat([new_VIoutput,outfile],axis=1)

    final_data.to_csv("Finished_data_"+output_name,  index=False, header=False)


    
if __name__ == "__main__":  main() 