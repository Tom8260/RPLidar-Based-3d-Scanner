# by chris martin 12/6/2020
#Modified for the raspberry pi.
#The angle sensor is on the spi bus 0, device 0
#It uses GPIO ports 10 (pin 19) MOSI which is set to one for readonly mode
#GPIO port 9 (pin 21) MISO and GPIO 8 (pin 24) for CE (active low)
#Run raspi-config to enable the SPI bus
#
#
#
import time
import math
import subprocess
import spidev
import RPi.GPIO as GPIO     
GPIO.setmode(GPIO.BCM)
#TMC2209 MS2, MS1: 00: 1/8, 01: 1/32, 10: 1/64 11: 1/16
def getzaxisruntime(frequency,motorsteps,driveratio,m1,m2,zaxisindex, Nscancycles):
    pi=math.pi #pi constant
    #factor =1.021
    #factor = 1+(.0000060*zaxisindex) #.0000100 works for 1500 steps/rev
    #factor = 1+(.0000050*zaxisindex) #.0000050 works for 4500 steps/rev
    factor = 1+(.0000052*zaxisindex) #.0000050 works for 6000 steps/rev
    if m2 == 0 and m1 == 0: #1/8 step
        multiplier=8
    if m2==0 and m1 == 1: #1/2 step
        multiplier=32  
    if m2==1 and m1 == 0: #1/4 step
        multiplier=64
    if m2==1 and m1 == 1: #1/16 step
        multiplier=16
    Nstepsperrev=driveratio*motorsteps*multiplier # physical steps per rev 1.8 deg stepper motor drive ratio is 8*200*16 (3200*)
    timeperrev=Nstepsperrev/frequency
    zaxisanglestep=2*pi/zaxisindex 
    zaxisruntime=factor*timeperrev/zaxisindex
    return zaxisruntime

class anglesensor:
    
    def __init__(self, bus, device, spimode):
        self.spi=spidev.SpiDev()
        self.spi.open(bus,device)
        self.spi.mode=spimode
        self.spi.max_speed_hz = 1000000
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(10, GPIO.OUT) #mosi set to 1 for 3 wire mode
        GPIO.output(10, 1) # set so sensor is readonly
        print("SPI Angle Sensor initialized")

    def close(self):
        self.spi.close()
    
    def getangle(self):
        anglestep=0.02197265625 #degrees per count
        vread=self.spi.readbytes(2) #Throw away first reading
        vread=self.spi.readbytes(2)        
        #vread=self.spi.xfer(dummy)
        angle=int.from_bytes(vread, "big")% 2**14
        return round((angle*anglestep),2)    

# This writes a PLY header to the output files, using ASCII format.
# Total_vertex is the total number for xyz entries.
# Set to zero to start and updated once the scan has completed. 
def ply_write_header(ply, total_vertex, scan_count, max_distance, Nscancycles):
    ply.write('ply\n')
    ply.write('format ascii 1.0\n')
    ply.write('comment Produced using a Raspberry Pi 3d scanner\n')
    ply.write('comment In PLY format with %s scans at %s mm maximum distance using %s lidar rotations\n' % (scan_count, max_distance, Nscancycles))
    ply.write('element vertex %08d\n' % (total_vertex))
    ply.write('property float x\n')
    ply.write('property float y\n')
    ply.write('property float z\n')
    ply.write('property float nx\n')
    ply.write('property float ny\n')
    ply.write('property float nz\n')
    ply.write('element face ')
    ply.write('%s\n' % (0))    
    ply.write('property list uchar float vertex_indices\n')    
    ply.write('end_header\n')
    return
#End of writing PLY header
#
# Once the scan has finished, we need to update the PLY header with the total
# number of xyz entries, called element vertex, in the file
def ply_vertex_update(ply, total_vertex, scan_count, max_distance, Nscancycles):
    ply.seek(0) # go to beginning of file
    ply.write('ply\n')
    ply.write('format ascii 1.0\n')
    ply.write('comment Produced using a Raspberry Pi 3d scanner\n')
    ply.write('comment In PLY format with %s scans at %s mm maximum distance using %s lidar rotations\n' % (scan_count, max_distance, Nscancycles))
    ply.write('element vertex %08d\n' % (total_vertex))
    #print("PLY file updated")
    return
#end of writing header update
   

