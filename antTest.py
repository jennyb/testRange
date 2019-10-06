#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
#from datetime import datetime, timedelta
import RFExplorer
import Hamlib

def PrintPeak(objAnalazyer, azimuth, f):
    """This function prints the amplitude and frequency peak of the latest received sweep
    """
    nIndex = objAnalazyer.SweepData.Count-1
    objSweepTemp = objAnalazyer.SweepData.GetData(nIndex)
    nStep = objSweepTemp.GetPeakStep()      #Get index of the peak
    fAmplitudeDBM = objSweepTemp.GetAmplitude_DBM(nStep)    #Get amplitude of the peak
    fCenterFreq = objSweepTemp.GetFrequencyMHZ(nStep)   #Get frequency of the peak

    print("Sweep[" + str(nIndex)+"]: Peak: " + "{0:.3f}".format(fCenterFreq) + "MHz  " + str(fAmplitudeDBM) + "dBm")

    f = open("results.csv","a")
    f.write(str(azimuth)+","+str(fAmplitudeDBM)+","+str(fCenterFreq)+"\n")
    f.close()

def initRFE(objRFE):
    objRFE.GetConnectedPorts()
    #Connect to available port
    if (objRFE.ConnectPort(RFE_SERIAL_PORT, BAUDRATE)):
        #Reset the unit to start fresh
        objRFE.SendCommand("r")
        #Wait for unit to notify reset completed
        while(objRFE.IsResetEvent):
            pass
        #Wait for unit to stabilize
        time.sleep(3)
        objRFE.eMode = 0 #spectrum analyser

        #Request RF Explorer configuration
        objRFE.SendCommand_RequestConfigData()
        #Wait to receive configuration and model details
        while(objRFE.ActiveModel == RFExplorer.RFE_Common.eModel.MODEL_NONE):
            objRFE.ProcessReceivedString(True)    #Process the received configuration
            #print(dir(objRFE)) #.m_sLineString))
            time.sleep(0.1)
        time.sleep(3)
    else:
        print("Failed to connect objRFE port=" + RFE_SERIAL_PORT+"  Baud="+str(BAUDRATE))
        objRFE.Close()
        quit()

def getSweep(objRFE, azimuth, f):
    time.sleep(0.1)
    #objRFE.ResetInternalBuffers()
    #objRFE.UpdateDeviceConfig(1295,1297)
    while not (objRFE.ProcessReceivedString(True)[0]):
        print(".",end="",flush=True)
        #Process all received data from device
        print("Count = " + str(objRFE.SweepData.Count))
    
    time.sleep(0.1)
    print("")
    PrintPeak(objRFE, azimuth, f)
    if (objRFE.SweepData.Count > 10):
        objRFE.m_SweepDataContainer.CleanAll()
        print("cleaned")  


def initRotator(my_rot):
    print("Initialising Rotator")

    Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)

    # Init RIG_MODEL_DUMMY
    my_rot.set_conf("rot_pathname", ROTATOR_SERIAL_PORT)
    #my_rot.set_conf("speed", "600")

    my_rot.open ()
    my_rot.set_position(0,0)

def setFrequency(objRFE, startFreq, stopFreq):
    print("Setting Frequency")
    objRFE.UpdateDeviceConfig(startFreq, stopFreq)
    objRFE.SendCommand_RequestConfigData()
    while not (objRFE.ProcessReceivedString(True)[0]):
        time.sleep(0.1)
    print("RBW: ", + objRFE.RBW_KHZ)
    print("Start Frequency: ", + objRFE.StartFrequencyMHZ)
    print("Stop Frequency: ", + objRFE.StopFrequencyMHZ)


#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

RFE_SERIAL_PORT = "/dev/ttyUSB1"
ROTATOR_SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 500000

objRFE = RFExplorer.RFECommunicator()     #Initialize object and thread
my_rot = Hamlib.Rot(Hamlib.ROT_MODEL_SPID_ROT2PROG)

## Uncomment to run this script from an in-tree build (or adjust to the
## build directory) without installing the bindings.
#sys.path.append ('.')
#sys.path.append ('.libs')


def StartUp():
    print("%s: Python %s; %s\n" \
          % (sys.argv[0], sys.version.split()[0], Hamlib.cvar.hamlib_version))
    startFreq = 1290
    stopFreq = 1300


    #erase old data
    f = open("results.csv","w")
    f.close()

    initRFE(objRFE)
    time.sleep(0.1)
    initRotator(my_rot)
    print("Calling setFrequency()")
    setFrequency(objRFE,startFreq,stopFreq)

    for deg in range (1,359):
        print ( deg )
        my_rot.set_position(deg,0)
        p=my_rot.get_position()
        print ( p )
        while (abs(p[0]-deg) > .1):
            print ( my_rot.error_status )
            p=my_rot.get_position()
            time.sleep(0.1)
            print ( p )
        getSweep(objRFE,deg, f)

    print("Finished sweep")
    my_rot.set_position(0,0)
    objRFE.Close()

if __name__ == '__main__':
    try:
        StartUp()
    except:
        objRFE.Close()
        raise

    objRFE.Close()
