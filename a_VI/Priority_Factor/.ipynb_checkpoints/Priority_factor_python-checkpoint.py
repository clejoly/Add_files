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

    


def main():
    targetpathfile=input("What is the targetpath filename? Ex. cassandra/new_table.xlsx   ") 
    output_name=input("What is the output filename? Ex. VIoutput_date.csv   ") 

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
    VIoutput.to_csv(output_name,  index=False)

    
if __name__ == "__main__":  main() 