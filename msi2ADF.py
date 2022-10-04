#!/usr/bin/python3
#
# MSI to ADF antenna pattern conversion utility
#
# Copyright 2022 Farrant Consulting Ltd
# CloudRF.com

import csv
import sys
import numpy as np
from scipy.interpolate import make_interp_spline, BSpline
import os
from collections import deque

horizontal = []
vertical = []

# Change me
oem=""
model=""
limit=90 # db threshold for QC
targetPlane = "Vertical"# Horizontal | Vertical | Total

if len(sys.argv) < 2:
    print("Usage: python3 msi2adf.py {ets.csv}")
    quit()

def rotate(l, n):
    return l[n:] + l[:n]

def writeADF(filename,oem,model,frequencyMHz,gainDBi,horizontal,vertical):
    filename = filename +".adf"
    print(filename)

    horizontal = deque(horizontal)
    horizontal.rotate(180)

    vertical = deque(vertical)
    vertical.rotate(180)

    adf = open(filename,"w")
    adf.write("REVNUM:,TIA/EIA-804-B\r\n")
    adf.write("REVDAT:,20221004\r\n")
    adf.write("COMNT1:,Standard TIA/EIA Antenna Pattern Data\r\n")
    adf.write("ANTMAN:,"+oem+"\r\n")
    adf.write("MODNUM:,"+model+"\r\n")
    adf.write("DESCR1:,"+str(frequencyMHz)+"MHz\r\n")
    adf.write("DESCR2:,Made with love at CloudRF.com\r\n")
    adf.write("DTDATA:,20221004\r\n")
    adf.write("LOWFRQ:,"+str(frequencyMHz-100)+"\r\n")
    adf.write("HGHFRQ:,"+str(frequencyMHz+100)+"\r\n")
    adf.write("GUNITS:,DBI/DBR\r\n")
    adf.write("MDGAIN:,"+str(gainDBi)+"\r\n")
    adf.write("AZWIDT:,360\r\n")
    adf.write("ELWIDT:,360\r\n")
    #adf.write("CONTYP:,\r\n")
    adf.write("ATVSWR:,1.5\r\n")
    adf.write("FRTOBA:,0\r\n")
    adf.write("ELTILT:,0\r\n")
    #adf.write("MAXPOW:,\r\n")
    #adf.write("ANTLEN:,\r\n")
    #adf.write("ANTWID:,\r\n")
    #adf.write("ANTWGT:,\r\n")
    adf.write("PATTYP:,Typical\r\n")
    adf.write("NOFREQ:,1\r\n")
    adf.write("PATFRE:,"+str(frequencyMHz)+"\r\n")
    adf.write("NUMCUT:,2\r\n")
    adf.write("PATCUT:,H\r\n")
    adf.write("POLARI:,V/V\r\n")
    adf.write("NUPOIN:,360\r\n")
    adf.write("FSTLST:,-179,180\r\n")
    a=-179
    for h in horizontal:
        adf.write(str(a)+","+str(round(h,3))+"\r\n")
        a+=1
    adf.write("PATCUT:,V\r\n")
    adf.write("POLARI:,V/V\r\n")
    adf.write("NUPOIN:,360\r\n")
    adf.write("FSTLST:,-179,180\r\n")
    a=-179
    for v in vertical:
        adf.write(str(a)+","+str(round(v,3))+"\r\n")
        a+=1
    adf.write("ENDFIL:,EOF\r\n")
    adf.close()

with open(sys.argv[1]) as csvfile:
    # First pass: Find best column and row
    reader = csv.reader(csvfile, delimiter=' ')
    bestColumn=0
    bestRow=0
    r=1
    pos=0
    rowZero=360
    horizontalRows=720
    verticalRows=720
    rowOneSixFive=-1
    frequencyMHz=0
    count=1
    plane=""
    gainDBi=0
    last=-1

    for row in reader:
        if row[0] == "NAME":
            size = len(row)
            n = 1 
            while n < size:
                model += row[n] + " "
                n += 1

        if row[0] == "MAKE":
            size = len(row)
            n = 1 
            while n < size:
                oem += row[n] + " "
                n += 1

        if row[0] == "HORIZONTAL":
            plane=row[0] # Horizontal | Vertical | Total
            print(plane, pos)
            horizontalRows = pos

        if row[0] == "VERTICAL":
            plane=row[0] # Horizontal | Vertical | Total
            print(plane, pos)
            verticalRows = pos

        if row[0] == "FREQUENCY":
            frequencyMHz=float(row[1])

        if row[0] == "GAIN":
            gainDBi=float(row[1])

        if pos > horizontalRows and pos < verticalRows and row[0] != "VERTICAL":
            angle = float(row[0])
            gain = round(float(row[1]) * -1,3)
            horizontal.append(gain)

        if pos > verticalRows and row[0] != "HORIZONTAL":
            angle = float(row[0])
            gain = round(float(row[1]) * -1,3)

            # Handle stupid 0.1 increments
            if abs(angle-last) > 0.95:
                vertical.append(gain)
                last=angle

        pos+=1
        r+=1

    writeADF(sys.argv[1],oem,model,frequencyMHz,gainDBi,horizontal,vertical)