#!/usr/bin/python3
# Scanner code by Chris Martin 12/6/2020, web interface code by Tom Watts with lots of help from Iain Malcolm.
import pathlib
import os
import time, sys
import flaskextras, netinf
from flask import redirect, send_from_directory, render_template
import area_3d_scanner_web as scanner

class webbaby(flaskextras.webify):
    """
    This class extends the original app with some basic web helping methods (from wimpleweb.webify)
    and provides the method 'get_updates' which is called by the webserver whenever a page is requested
    which is an 'app_page' (see serverdef below)
    
    It also adds a property to help provide a clean web interface (op_select), and another property to 
    demo a simple progress bar.
    
    This approach means there is only 1 copy of the app running, so if multiple web browsers access
    the web server they all see the same values.
    """
    def __init__(self):
        """
        in addition to constructing the base classes, initialise a couple of variables used to run the 
        progress bar.
        """
        #This sets the default values on the web page
        # the variable names used in the scanner program are in brackets
        self.target_ops = 360
        self.scans = 1000# int, number of scans per rev (zaxisindex)
        self.cycles = "2" #int, Revolutions per scan (Nscancycles), minimum of 2
        self.distancelimit = 4000 # int, distance limit (distancelimit)
        self.filename = "area_image" # string, Output filename (filenameprefix)
        self.download_path = "scans/"
        self.full_filename = (self.download_path + self.filename)
        updateindex={'index': self.index_updates}
        self.operation_LIST = {'display': self.valid_ops()}
        updateindex={'index': self.index_updates}
        flaskextras.webify.__init__(self, __name__, updateindex)       
        #super().__init__(__name__, updateindex)

        

    def index_updates(self):
        """
        called at regular intervals from the web server code for an active page with fields that need updating.
        
        There is only 1 page in this app ('index') and it provides updates for 3 fields (only fields which
        have actually changed value since the last update are sent to the web browser).
        """
        full_filename = (self.download_path + self.filename)
        if scanner.status1 == "Finished":
                button_colour = "green"
        else:
                button_colour = "white" 
            
        if scanner.status =="Running":
                  
                runmin, runsec = divmod((scanner.time.time() - scanner.start_time),60)
                runhour, runmin = divmod(runmin, 60)
                runhour = "%02d" % int(runhour)
                runmin = "%02d" % int(runmin)
                runsec = "%02d" % round(runsec)
                position = '{0:3d}'.format(round(scanner.posangle))
       
                return [
                ('prog_bar', {'value':str(self.current_ops) }),
                ('progress_number', {'value':str(scanner.progress_bar) }),
                ('status', {'value':str(scanner.status)} ),
                ('total_vertex', {'value':str(scanner.total_vertex) }),
                ('runhour', {'value':runhour }),                               
                ('runmin', {'value':runmin }),
                ('runsec', {'value':runsec }),
                ('position', {'value':position }),
                ('position1', {'value':position }),
                ('position_bar', {'value':str(self.current_ops1)} ), 
                ('button1', {'value':'Scanning', 'bgcolor':'red', 'disabled':True}),
                ('button2', {'value':self.filename + ".ply download", 'bgcolor':button_colour, 'disabled':True}),
                ('#progress', {'value': str(self.current_ops1)}),
                                                            
                ]
        else:
                return [
                ('prog_bar', {'value':str(self.current_ops)} ),
                ('progress_number', {'value':str(scanner.progress_bar) }),
                ('status', {'value':str(scanner.status)} ),
                ('total_vertex', {'value':str(scanner.total_vertex) }),
                ('position', {'value':0 }),
                ('button1', {'value':' Start Scan ','bgcolor':'green', 'disabled': False},),
                ('button2', {'value':self.filename + ".ply download",'bgcolor':button_colour, 'disabled': False},),
                ('#progress', {'value': str(0)}),
                ]



    @property
    def op_select(self):
        """
        The builds the html for the operator selection so it shows the app's current value (for example if the page
        is reloaded or a fresh browser page is opened).
        """
        return flaskextras.make_subselect(
                values=self.valid_ops(),
                selected=self.cycles)

    @property
    def current_ops(self):
        """
        provide an attribute getter that simulates a progress bar
        """
        return scanner.progress_bar
    @property
    def current_ops1(self):
        """
        provide an attribute getter that simulates a progress bar
        """
        return int(scanner.posangle)

        
    def valid_ops(self):
        return ("2", "3", "4", "5", "6", "7", "8", "9", "10")
     



# Code to start the scanner scanning
    def startscan(self, id):
        self.cycles = int(self.cycles)    
        print("number of cycles", self.cycles)
        scanner.start_scan(self.scans,self.distancelimit, self.filename, self.cycles)
        rdat = ((id, {
                    'value':'Finished', 
                    'bgcolor':'green',
                    'disabled':False}),)
         
        return [(rdat)]
        


app = webbaby()
# Setup the path to the scans folder
scansfolder=pathlib.Path('./scans')
@app.route('/')
def redir():
    return redirect(url_for('index'))

@app.route('/index')
def index():
    with open('templates/index.html', 'r') as tfile:
        template=tfile.read()
    return template.format(app=app)   
@app.route('/scans')
def scannedfiles(): #Show a page with a list of files
        scans = [(afile) for afile in scansfolder.iterdir() if afile.is_file() and afile.suffix == '.ply']
        return render_template('files.html', scanfiles=scans, header="Available scans for download")    
@app.route('/scans/<filename>')
def savedscans(filename):
        target=os.path.basename(filename)
        return send_from_directory(directory=str(scansfolder), filename=target, as_attachment=True)
            
if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000 )     
    
