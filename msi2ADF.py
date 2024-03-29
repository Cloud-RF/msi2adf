#!/usr/bin/python3
#
# MSI to ADF antenna pattern conversion utility
#
# Copyright (c) 2023 Farrant Consulting Ltd T/A CloudRF
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

import csv
import sys
import numpy as np
from scipy.interpolate import make_interp_spline, BSpline
import os
from collections import deque
from datetime import datetime

horizontal = []
vertical = []

# Change me
oem=""
model=""
limit=90 # db threshold for QC
targetPlane = "Vertical"# Horizontal | Vertical | Total
extraRotation = 90 # Some OEMs align north 0, others East 90, others south 180...

if len(sys.argv) < 2:
    print("Usage: python3 msi2adf.py {pattern.msi}")
    quit()

def rotate(l, n):
    return l[n:] + l[:n]

def writeADF(filename,oem,model,frequencyMHz,gainDBi,horizontal,vertical,extraRotation):
    filename = filename +".adf"
    print(filename)

    # WARNING - This makes an assumption based on data from a few OEMs. Data in the wild may vary!

    horizontal = deque(horizontal)
    horizontal.rotate(180)

    vertical = deque(vertical)
    vertical.rotate(180+extraRotation)

    yearMonthDay = datetime.today().strftime("%Y%m%d")

    adf = open(filename,"w")
    adf.write("REVNUM:,TIA/EIA-804-B\r\n")
    adf.write("REVDAT:,"+yearMonthDay+"\r\n")
    adf.write("COMNT1:,Standard TIA/EIA Antenna Pattern Data\r\n")
    adf.write("ANTMAN:,"+oem+"\r\n")
    adf.write("MODNUM:,"+model+"\r\n")
    adf.write("DESCR1:,"+str(frequencyMHz)+"MHz\r\n")
    adf.write("DESCR2:,Converted at CloudRF.com\r\n")
    adf.write("DTDATA:,"+yearMonthDay+"\r\n")
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

            # Handle pretentious 0.1 increments by only using angles > 0.95
            if abs(angle-last) > 0.95:
                vertical.append(gain)
                last=angle

        pos+=1
        r+=1

    writeADF(sys.argv[1],oem,model,frequencyMHz,gainDBi,horizontal,vertical,extraRotation)