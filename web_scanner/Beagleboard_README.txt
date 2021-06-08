**********To run on a Beagleboard*******
1. Change the imports for motorcontrol and support functions to the Beagle functions
2. Delete __del__ from the motor control or it fails on the second and subsequent attempts. Add a simple cutpower which disables the motor, see pi_stepper_motor_control_2.py for an example.
3. Repeated tests gave me GPIO.setmode(GPIO.BCM) errors on a raspberry Pi, not sure what beagleboard GPIO will do. I had to move GPIO.setmode(GPIO.BCM) to the class init. 
4. Copy the ply writing functions to the beagleboard support functions.
5. Import os in the main app so it can create a scans directory if it doesn't exist. This is where the .ply scan files are saved.
6. The main code is almost the same except it is in two main functions so that it can be imported into the 3d_scanner_frontend.py program which controls the web interface. It will still run standalone.
7. Uses flask for the web interface. This is installed by default on most Raspberry Pi releases but may need to be installed on a beagleboard.
8. To run the web interface run 
	python3 3d_scanner_frontend.py