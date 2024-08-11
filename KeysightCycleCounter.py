### Version 9 MAY 2024
### Copied Structure from ESPEC Cycle Counter
# Works, but requires rewrite when I have time, to make sense

import bisect
import scipy
import math
import sys
import requests,json
import datetime
import os
import codecs
import time,struct,binascii
import numpy as np
import easygui as eg
import subprocess
import threading
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from colorama import Fore,init                   
init(autoreset="True")

nowish = time.time()



Deviation = 0.0

#data points allowed to skip before logging any points 
# 1 -30 #
resolution = 1


def ListFiles(FilePath = "./"):
    
    FileList = []
    
    if FilePath[-1] != '/' and FilePath[-1] != '\\': 
        
        
        
        q = 0
        p = 0
        for i in enumerate(FilePath):
            if "\\" in i:
                p = q
                print(f"{i}\n")
                print(f"{p}\n")
            q +=1 
        print(FilePath[0:p+1])
        FilePath = FilePath[0:p+1]
        
        
        
        
    ListOfFiles = os.listdir(FilePath)
    for items in ListOfFiles:
        if '.csv' in items or '.xlsx' in items or '.xls' in items:
            
            FileList.append(FilePath + items)
            
    return FileList
    
    
def LoadColumns(FileList):
    
    Legend = ""
    file_start = 0
    with open(FileList,"r") as r:
        while ("Scan Sweep Time" not in Legend):
            file_start+=1
            Legend = r.readline()
        Legend = Legend.replace("\n","")
        
        Legend = Legend.split(",")
    Axis_List = {}
    Axis_List.clear()
    try:
        Axis_List = {"timeStamp" : Legend.index("Scan Sweep Time (Sec)")}
    except:
        Axis_List = {"Order" : Legend.index("Scan Number")}
        
    control_list = []
    for i in Legend:   
        if ("C" in i):
            Axis_List[f"{i[:3]}temp__process_value"] = Legend.index(i)
            control_list.append(f"{i[:3]}temp__process_value")
             
    return Axis_List,file_start,control_list
            
CSV_List = ListFiles()
FileNumber =0

# Todo Sanitise float input
cold_setpoint = float(input(f"{Fore.CYAN}Cold Setpoint: "))
hot_setpoint = float(input(f"{Fore.RED}Hot Setpoint: "))

for items in CSV_List:
    #print(CSV_List)
    SetTag = ''
    ProcessTag = ''
    ProdTag = ''
    try:
        Axis_Dict.clear()
    except:
        pass
    Axis_Dict,file_start,control_list = LoadColumns(CSV_List[FileNumber])
    print(json.dumps(Axis_Dict,indent=4))
    print("This log contains columns for")
    Yaxis = dict()
    Xaxis = []
    for i in Axis_Dict:
        print(f"{Fore.GREEN}{i}{Fore.WHITE} in column {Fore.YELLOW}{Axis_Dict[i]}")
        Yaxis[i] = []

    
    if True:
        
        with open(CSV_List[FileNumber],"r") as r:
            inc = 1
            datadata = r.readline()
            while(datadata):
                data = []
                datadata = r.readline()
                if(datadata == ''):
                    break
                datadata = datadata.replace("\n","")
                datadata = datadata.split(",")
                
                for i in Axis_Dict:
                    if "product" in i:
                        ProdTag = True
                        
                    if('timeStamp' not in i and "Date" not in i and "Time" not in i):
                        if("value" in i):
                            try:
                                Yaxis[i] += [  float(  datadata[  Axis_Dict[ i ]  ]  )  ]
                            except IndexError:    
                                break
                            except:
                                print(f"{Axis_Dict[i]} \t| {len(datadata)}")

                                Yaxis[i] += [datadata[Axis_Dict[i]]]
                        else:
                            Yaxis[i] += [datadata[Axis_Dict[i]]]
                            
                    if('timeStamp' in i):
                        Xaxis.append(datadata[Axis_Dict['timeStamp']])
                        
                    if(i == "Date"):
                        Xaxis.append(inc)
                    
                    
                    
                    
                inc+=1
        length_of_file = inc


    Xaxis=Xaxis[file_start:-1]
    for i in control_list:
        Yaxis[f"{i}"] = Yaxis[f"{i}"][file_start:]
    
    
    fig1 = go.Figure()
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    temp = 0
    Step_Cycles = 0
    inc = 0
    for i in Axis_Dict:
        # print(f"{i} in Axis_Dict")
        
        if ("process" in i) and (ProcessTag == ''):
            ProcessTag = i
        if('value' in i):
            
          
            #fig1.add_trace(go.Scatter(x = Xaxis, y=Yaxis[i],name=f"{i}",mode='markers', marker={'size':1}),secondary_y=False)
            fig1['layout']['yaxis'].update(autorange = True)
    ############################################################################################################################
    # No Steps in Keysight logs
    ############################################################################################################################

    for i in control_list:
        try:
            Peaky= []
            minusPeaky= []
            peakx = []
            minuspeakx = []
            
            
            if True:
                #                                          Yaxis process key    prominence      distance between points should be 
                #                                                                               minimum 75% of cycle time in sec /10
                #                                                                               Value should be minutes*6
    
                peaks,properties = scipy.signal.find_peaks(Yaxis[i],            prominence=60,   distance=15)
                minuspeaks,properties = scipy.signal.find_peaks(np.negative(Yaxis[i]),            prominence=60,   distance=15)
                
                for p in peaks:
                    if (Yaxis[i][p]>hot_setpoint-Deviation):
                        Peaky.append(p)
                        
                        if control_list.index(i) == 0:
                            peakx.append(Xaxis[p-file_start])
                
                for p in minuspeaks:
                    if (Yaxis[i][p]<cold_setpoint+Deviation):
                        minusPeaky.append( p)
                        if control_list.index(i) == 0:
                            minuspeakx.append(Xaxis[p])
                
                        
            peakgraph = []
            xpeakgraph = []
            rang = 0
            inc = 0
            dataloss = 0
            for ii in Xaxis:
                
                if rang in peakx:
                    peakgraph.append(Yaxis[i][rang])
                    xpeakgraph.append(ii)
                    dataloss = 0
                if rang in minuspeakx:
                    peakgraph.append(Yaxis[i][rang])
                    xpeakgraph.append(ii)
                    dataloss = 0
                if rang not in minuspeakx and rang not in peakx:
                    dataloss +=1
                if (dataloss >= resolution):
                    peakgraph.append(Yaxis[i][rang])
                    xpeakgraph.append(ii)
                    dataloss = 0
                    
                rang+=1
                
            
            XTrendPeak = []
            YTrendPeak = []       
            inc = 0
            rang = 0
            for ii in Xaxis:
                XTrendPeak.append(ii)
                rang+=1
                if rang in Peaky:
                    inc+=1
                YTrendPeak.append(inc)
            #Draw Peak TrendLine
            fig1.add_trace(go.Scatter(x=XTrendPeak,y=YTrendPeak,mode="lines", name=f"{i[:3]} Reached High Set Point <b>{max(YTrendPeak)}</b> Times",),secondary_y=True)
            print(f"{max(YTrendPeak)}:{Fore.RED} By Reaching High Setpoints")
            #Draw Peaks of process value          
            fig1.add_trace(go.Scatter(x=xpeakgraph[::resolution],y=peakgraph[::resolution],name=f"{i[:3]} Process Value",mode='lines'),secondary_y=False)

            XTrendPeak = []
            YTrendPeak = []       
            inc = 0
            rang = 0
            for ii in Xaxis:
                XTrendPeak.append(ii)
                rang+=1
                if rang in minusPeaky:
                    
                    inc+=1
                YTrendPeak.append(inc)
            #Draw -Peak TrendLine
            fig1.add_trace(go.Scatter(x=XTrendPeak,y=YTrendPeak,name=f"{i[:3]} Reached Low Set Point <b>{max(YTrendPeak)}</b> Times",),secondary_y=True)
            print(f"{max(YTrendPeak)}:{Fore.CYAN} By Reaching Low Setpoints")
        except KeyError:
            print("string is not a peak")
    #Draw Low Peaks
    #fig1.add_trace(go.Scatter(x=[minuspeakx,peakx],y=[minusPeaky["Peaks"],Peaky["Peaks"]],name=f"{len(minuspeakx)} -Peaks of Process Value",mode='markers', marker={'size':2}),secondary_y=False)
    ############################################################################################################################


    fig1['layout']['yaxis'].update(autorange = True)

    fig1.update_yaxes(title_text="<b>Chamber Set Points</b>", secondary_y=False)
    fig1.update_yaxes(title_text="<b>Total Cycles</b>", secondary_y=True)
    fig1.update_traces(line={'width': 1})
    fig1.update_layout(title=f"Total Cycles")



    fig1.write_html(f"{items[0:3]}fig{FileNumber}.html")
    fig1.show()
    print("\n\n")
    FileNumber +=1 