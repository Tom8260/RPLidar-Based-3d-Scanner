# by chris martin 12/6/2020
# Python Script is for Python 3
# Changed to run on a Raspberry Pi by Tom Watts
import os #needed to create the scans directory if it doesn't exist
import select # Not sure what features this library all has
import time # maybe better to use Gevent. eventually
import subprocess #allows command line to be used in the program
import math #math and trig functions
import pi_scanner_support_functions as sf
from pi_Stepper_Motor_Control_2 import motorcontrol  #motor class
from pyrplidar import PyRPlidar #python rplidar library from https://github.com/Hyun-je (modified slightly for this application)
#CONSTANTS / initialize
pi=math.pi #pi constant
intensity="150" #strength of the laser return, turns out this is only availible if the scanner is in legacy mode.
zaxisangle=0 #initialize zaxis angle 
counter_scan_loops=-5
status = "Ready"
progress_bar = 0
progress = 0
posangle = 0
total_vertex = 0
status1 = "Ready"

#SET UP Z-AXIS

frequency=860 #pwm frequency
direction=0 # Scanner operates clockwise viewed from top
m1=0 # Legacy mode stepper driver step selection
m2=1 # Legacy mode stepper driver step selection
motorsteps=400 #steps full steps per rev
driveratio=128/16 #driven 128th/ drive 16th




#***********************************************************************************************
# Functions
#***************************************************************************************************
def scanner_loop(Nscancycles, distancelimit):
    global progress
    global progress_bar
    global scan
    global outfile1
    global outfile2
    global intensity
    global posangle
    global total_vertex
    progress = 0
    progress_bar = 0
    last_progress = 0
    loopend = 0
    counter_scan_loops=0
    oneshot=False  
    flag=0
    rollover=0
    calczaxisangle=0
    while not loopend:
        
        rawangle=spi.getangle()  #get stepper motor angle
    
        if not oneshot:  #zero out steppper motor angle
            startangle=rawangle
            lastangle=rawangle
            startangleprime=360-startangle
            
        if lastangle<rawangle and rawangle>300 and lastangle<40 and flag==0: #stepper turns 8 times for every time the scanner turns once 
            rollover +=1
            flag=1
        if flag ==1 and rawangle<320.0 and rawangle>40: flag=0    
        angleprime=360-rawangle
        
        posangle=(angleprime-startangleprime+360*rollover)/driveratio  #calculate zaxis angle
        lastangle=rawangle
        if not oneshot:
            startposangle=posangle
            oneshot=True
        
        
        zaxisangle=math.radians(posangle) # convert to radians
        lidar.clear_buffer() #the scanner is scanning all the time, this forces it erase anything in its memory and start sending data agfain from 0 degrees
        time.sleep(.005) #timer to clear buffer seems to work fine with out the wait maybe not needed.
        
        for count, scan in enumerate(scan_generator()): # this takes the scan data and adds a count to the start of each measurement
            if scan[0]==True: # gives true a the start of each full revolution measured.
                counter_scan_loops = counter_scan_loops + 1
            
            distance=scan[3] #measured distance
            angle=math.radians(scan[2])+RPLIDARanglecorrection #measured angle realtive to horizontal corrected for error in mounting
            cosalpha=math.cos(angle) # cosine
            sinalpha=math.sin(angle) # sine
            costheta=math.cos(zaxisangle) # cosine zaxis rotation
            sintheta=math.sin(zaxisangle) # cosine zaxis rotation
                 
            # rotate about y axis first y stays constant
            xprime=(distance*cosalpha)
            zprime=(-distance*sinalpha)
            yprime=0
               
            #rotate about z axis second z stays constant
            x=1*(xprime*costheta)
            y=-1*(xprime*sintheta)
            z=(zprime)
            if scan[1]>0 and scan[3]<distancelimit: # check scan quality for 0 (bad measure) and that it is in range
                if scan[1]>255: intensity='150' # keep intesity in range (doesnt do anything, just in case)
                #else: intensity=255-int((scan[3]/distancelimit)*255)  # set intensity to be based on distance (could color code it)
                
                if angle <=pi/2 or angle >= 3*pi/2:
                    print(str(x),str(y),str(z),intensity,intensity,intensity, '\r', file=outfile) # print data to file.
                    total_vertex +=1
                # there appears to be some paralax in the rplidar sensing. plan was to scan 180 deg on the z axis to get 360 deg coverage
                #, but the seams would not reconcile. the error appears to be the width of the laser dot so to speak 
                # so now it creates two point cloud files using the front and back scanned hemisphere
            
            if counter_scan_loops == (Nscancycles+1): 
                #print("count:", (str(count)).zfill(5),end='\n ')
                break
        counter_scan_loops=0 # rest counter for scan looops
        
        print ("cal angle: ",'{:10.4f}'.format(math.degrees(calczaxisangle)),"    measured angle:",'{:10.4f}'.format(posangle), end='\n')       
        calczaxisangle=calczaxisangle+zaxisanglestep #count up zaxis revolutions
        progress = (posangle/3.6)
        if progress > last_progress + 1:
                print("Progress ", round(progress), "%")
                last_progress = progress
                progress_bar = round(progress)                      
         
        if zaxisangle > (startposangle+(2*pi)):
            loopend=1
        mc.zaxis(direction,1,frequency,m1,m2,50, zaxisruntime) #lock zaxis duty=100)
    return total_vertex        
def lidar_warmup():
    counter_scan_loops = 0
    for count, scan in enumerate(scan_generator()): # this takes the scan data and adds a count to the start of each measurement
        if scan[0]==True: # gives true a the start of each full revolution measured.
            counter_scan_loops = counter_scan_loops + 1
        if counter_scan_loops == 4: 
            break #"warm up scanner give it a chance to stabilize"
#******************************************************************************************************************
# Main scanning program
#*****************************************************************************************************************            
def start_scan(zaxisindex, distancelimit, filenameprefix, Nscancycles):
    global progress_bar
    global status
    global status1
    global scan_generator
    global lidar 
    global outfile
    global RPLIDARanglecorrection
    global zaxisanglestep
    global zaxisruntime
    global timeperrev
    global start_time
    global posangle
    global total_vertex
    global mc
    global spi
    mc=motorcontrol() # mc stepper motor
    spi = sf.anglesensor(0,0,1) #angle sensor on spi bus0,device0, spi mode 1    
    zaxisangle=0 #initialize zaxis angle 
    counter_scan_loops=-5
    status = "Initialising"
    status1 = "Ready"
    progress_bar = 0
    progress = 0
    posangle = 0
    total_vertex = 0
    #RUNTIME VARIBLES
    #zaxisindex = int(input("Input number of scans, usual range is 1000 to 6000  "))
    #zaxisindex=360 # number of scans to take on the zaxis tested up to 6000 so far with angle sensor
    #Nscancycles=1 # rplidar scan rotations the rplidar module does not always give the same angles for measurements, a higher number here
    # results in more points collected 10 times around gives a high density of points but take longer
    #distancelimit = int(input("Input distance limit in mm, usual range is up to 4500mm  "))                                                
    #distancelimit=4500 # throw away points that are too far out.
    RPLIDARanglecorrection=0.01745329*1.00 #.98  #1 DEG*FACTOR - the rplidar x axis "0 degrees"  this horizontal this adgusts the plane. 
    zaxiscorrection = math.radians(0.0)#
    
    #SET UP Z AXIS STEP SIZE AND STEPPER MOTOR RUN TIME (NO ANGLE SENSOR)
    zaxisanglestep=2*pi/zaxisindex  # 360degrees divided by how many steps to take
    zaxisruntime=sf.getzaxisruntime(frequency,motorsteps,driveratio,m1,m2,zaxisindex,Nscancycles)
    timeperrev=zaxisruntime*zaxisindex # this is used to bring the scanner back home after scannning will use it to tune the stepper driver too
    status = "Running" 
    start_time = time.time() #Save the current time                           
    # SET UP RPLIDAR
    lidar = PyRPlidar()
    lidar.connect(port="/dev/ttyUSB0", baudrate=115200, timeout=5)  #USB also can set up uart pins if desired
    lidar.reset()
    time.sleep(1.5)
    lidar.set_motor_pwm(1000) # not needed for RPLIDAR A1 AS YOU CAN'T CHANGE THE SPEED.
    time.sleep(0.5)
    lidar.clear_buffer()
    time.sleep(0.5)
    scan_generator = lidar.start_scan_express(0,"raw") # raw if using typed data from scanner, not raw for data packed in string
    #0,1,2 is the scan type 0 is the express scan it gives 4000 measurements around generally the slower the better the accuracy appears to be
    time.sleep(2) # wait for rplidar to finish set up
    total_vertex = 0
    if not os.path.exists('scans'):
        os.makedirs('scans')
    filenamea=(str(filenameprefix)+".ply")
    outfile = open("scans/"+filenamea, 'w')
    sf.ply_write_header(outfile, total_vertex, zaxisindex, distancelimit, Nscancycles) # writes the ply header with zero vertex to output file to start with
    print("Scanner output will be to", filenamea, "file",)
    time.sleep(1)
    #scanning routine
    lidar_warmup()
    # Specifications state max distance is 6m either way, 12m total
    if distancelimit > 6000:
        distancelimit = 6000
    total_vertex = scanner_loop(Nscancycles, distancelimit)
    # Close down after scan has completed
    sf.ply_vertex_update(outfile, total_vertex, zaxisindex, distancelimit, Nscancycles) # Write updated header with number of entries (vertex) in the file
    outfile.close() #close xyz files

    progress = 100
    progress_bar = 100    
    lidar.set_motor_pwm(0)  
    mc.zaxis(1,1,frequency*4,m1,m2,50, (timeperrev+(zaxisruntime*3))/8) #zaxis return to start
    mc.cutpower()  #close out 
    spi.close() #close out 
    status = "Finished"
    status1 = "Finished"
    lidar.stop()#close out 
    lidar.disconnect() #close out
    return 
    
    
if __name__ == "__main__":
        scans = 0
        while scans == 0:
                zaxisindex = int(input("Input the number of scans required    "))
                filenameprefix=input("Input filename prefix :- ")
                distancelimit=int(input("input distance limit :- "))
                Nscancycles=int(input("input revs per scan:- "))
                scans = zaxisindex
        # requires zaxisindex, distancelimit, filenameprefix, Nscancycles
        start_scan(zaxisindex, distancelimit, filenameprefix, Nscancycles)    
