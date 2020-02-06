## def acolite_guii
##
## written by Quinten Vanhellemont, RBINS
## 2017-2018
## modifications: 2018-03-07 (QV) added *args
##                2018-07-18 (QV) changed acolite import name
##                2018-09-12 (QV) updated relative path to default settings
##                2019-03-13 (QV) happy new year!

def acolite_gui(*args, version=None):
    import os
    import argparse
    parser = argparse.ArgumentParser(description='ACOLITE GUI')
    parser.add_argument('--settings', help='settings file')
    parser.add_argument('--images', help='list of images')
    ##args = parser.parse_args()
    args, unknown = parser.parse_known_args()

    import tkinter as tk
    #from tkinter import *
    from tkinter import END, IntVar, StringVar
    from tkinter import filedialog
    import threading

    import sys
    import time, datetime

    import acolite
    from acolite.acolite import acolite_run, settings_read, settings_write

    mp_platforms = ['linux','darwin']

    ## Process class that returns exceptions
    import multiprocessing as mp
    import traceback
    class Process(mp.Process):
        def __init__(self, *args, **kwargs):
            mp.Process.__init__(self, *args, **kwargs)
            self._pconn, self._cconn = mp.Pipe()
            self._exception = None

        def run(self):
            try:
                mp.Process.run(self)
                self._cconn.send(None)
            except Exception as e:
                tb = traceback.format_exc()
                self._cconn.send((e, tb))
                raise e

        @property
        def exception(self):
            if self._pconn.poll():
                self._exception = self._pconn.recv()
            return self._exception


    class acgui(tk.Tk):
        def __init__(self):
            self.version = version
            self.keep_running=True
            self.process = None
            self.setup()

            ### redirect stdout prints to GUI
            ## to be disabled when running processing with multiprocessing
            self.logging = WidgetTee(self.text)

            if args.settings is not None:
                self.restore(args.settings)
            else:
                ## restore acolite_python_settings file if in same directory
                if os.path.exists('acolite_python_settings.txt'):
                    self.settings_file = 'acolite_python_settings.txt'
                else:
                    self.settings_file = acolite.acolite.config['acolite_defaults']
                self.restore(self.settings_file)
                self.settings_file = 'acolite_python_settings.txt'

        def setup(self):
            ## set up GUI
            tk.Tk.__init__(self)
            if self.version is None:
                self.title('ACOLITE Python (unknown version)')
            else:
                self.title('ACOLITE Python (v{})'.format(self.version))

            self.resizable(False,False)

            ## empties
            self.inputfile=('')
            self.output=('')
            self.processingRunning=False
            self.settings_file=''

            ## set up containers
            inputframe=tk.Frame(self, width=600, height=100, pady=3)
            roiframe=tk.Frame(self, width=600, height=100, pady=3)
            optframe=tk.Frame(self, width=600, height=100, pady=3)
            saveframe=tk.Frame(self, width=600, height=100, pady=3)
            runframe=tk.Frame(self, width=600, height=100, pady=3)

            self.grid_columnconfigure(0, weight=1)

            inputframe.grid(row=0, sticky='ew')
            roiframe.grid(row=1, sticky='ew')
            optframe.grid(row=2, sticky='ew')
            saveframe.grid(row=3, sticky='ew')
            runframe.grid(row=4, sticky='ew')

            ### input and output
            l = tk.Label(inputframe, text='Input and output')

            ## make sure label is in the middle by setting the weight of its r/c to 1
            inputframe.grid_columnconfigure(0,weight=1)
            l.grid(row=0, column=0)

            ## make frame for io buttons
            ioframe = tk.Frame(inputframe)
            ioframe.grid(row=1, column=0)

            l = tk.Label(ioframe, text='Input:')
            l.grid(row=1,column=0)
            self.tinput = tk.Text(ioframe, height=1, width=40,
                                   borderwidth=1, relief='sunken')
            self.tinput.insert(END,self.inputfile)
            self.tinput.bind("<Tab>", self.focus_fw)
            self.tinput.grid(row=1, column=1)
            binput = tk.Button(ioframe, text='Select input...', command=self.select_input)
            binput.grid(row=1, column=2)

            l = tk.Label(ioframe, text='Output:')
            l.grid(row=2,column=0)
            self.toutput = tk.Text(ioframe, height=1, width=40,
                                   borderwidth=1, relief='sunken')
            self.toutput.insert(END,self.output)
            self.toutput.bind("<Tab>", self.focus_fw)
            self.toutput.grid(row=2, column=1)
            boutput = tk.Button(ioframe, text='Select output...', command=self.select_output)
            boutput.grid(row=2, column=2)
            ###

            #### frame for ROI
            roiframe.grid_columnconfigure(0, weight=1)
            l = tk.Label(roiframe, text='Region of interest (decimal degrees)')
            roiframe.grid_columnconfigure(0,weight=1)
            l.grid(row=0, column=0)
            roi = tk.Frame(roiframe)
            roi.grid(row=1,column=0)
            l = tk.Label(roi, text='South').grid(row=0, column=0)
            l = tk.Label(roi, text='North').grid(row=0, column=1)
            l = tk.Label(roi, text='West').grid(row=0, column=2)
            l = tk.Label(roi, text='East').grid(row=0, column=3)
            self.sbox = tk.Text(roi, height=1, width=10, borderwidth=1, relief='sunken')
            self.sbox.bind("<Tab>", self.focus_fw)
            self.sbox.grid(row=1, column=0)
            self.nbox = tk.Text(roi, height=1, width=10, borderwidth=1, relief='sunken')
            self.nbox.bind("<Tab>", self.focus_fw)
            self.nbox.grid(row=1, column=1)
            self.wbox = tk.Text(roi, height=1, width=10, borderwidth=1, relief='sunken')
            self.wbox.bind("<Tab>", self.focus_fw)
            self.wbox.grid(row=1, column=2)
            self.ebox = tk.Text(roi, height=1, width=10, borderwidth=1, relief='sunken')
            self.ebox.bind("<Tab>", self.focus_fw)
            self.ebox.grid(row=1, column=3)

            bclear = tk.Button(roi, text='Clear', command=self.clear_ROI)
            bclear.grid(row=1, column=4)
            ###


            ### frame for output options
            optframe.grid_columnconfigure(0,weight=1)
            l = tk.Label(optframe, text='Output options')
            l.grid(row=0, column=0)
            ##
            ### L2W parameters
            l2wframe=tk.Frame(optframe)

            l2wframe.grid(column=0, row=1)
            l=tk.Label(l2wframe, text='L2W parameters:')
            l.grid(column=0, row=0, sticky='w')
            self.tl2wpar = tk.Text(l2wframe, height=1, width=40,
                                   borderwidth=1, relief='sunken')
            self.tl2wpar.grid(column=1, row=0)
            ###
            ## RGB output
            rgbframe=tk.Frame(optframe)

            rgbframe.grid(column=0, row=2)
            l=tk.Label(rgbframe, text='PNG outputs:')
            l.grid(column=0, row=0)
            self.rgb_rhot=IntVar()
            self.rgb_rhot.set(1)
            c = tk.Checkbutton(rgbframe, text="RGB RHOT", variable=self.rgb_rhot)
            c.grid(column=1, row=0)
            self.rgb_rhos=IntVar()
            self.rgb_rhos.set(1)
            c = tk.Checkbutton(rgbframe, text="RGB RHOS", variable=self.rgb_rhos)
            c.grid(column=2, row=0)
            self.map_l2w=IntVar()
            self.map_l2w.set(1)
            c = tk.Checkbutton(rgbframe, text="L2W parameters", variable=self.map_l2w)
            c.grid(column=3, row=0)
            ###

            ### save and restore buttons
            l=tk.Label(saveframe, text='Save or restore settings:')
            l.grid(row=0, column=0, sticky='w')
            bsave = tk.Button(saveframe, text='Save', command=lambda: self.save())
            bsave.grid(row=0, column=1)
            brestore = tk.Button(saveframe, text='Restore', command=lambda: self.restore())
            brestore.grid(row=0, column=2)
            ###

            ### run and exit buttons
            ## use threading to be able to interrupt processing
            runframe.grid_columnconfigure(0, weight=1)
            runcol = tk.Frame(runframe)
            runcol.grid(row=0, column=0)
            if sys.platform in mp_platforms:
                brun = tk.Button(runcol, text='Run processing', width=24, command=lambda: threading.Thread(target=self.startRun).start())
            else:
                brun = tk.Button(runcol, text='Run processing', width=24, command=self.startRun)
            brun.grid(row=0, column=0)

            if sys.platform in mp_platforms:
                bstop = tk.Button(runcol, text='Stop processing', width=24, command=lambda: self.stopRun())
                bstop.grid(row=0, column=1)

            bexit = tk.Button(runframe, text="Exit", width=50, command=self.stopExit)
            bexit.grid(row=1, column=0)
            ###

            ### frame for output text
            textframe = tk.Frame(self)
            textframe.grid(row=6, column=0, sticky='s')
            l = tk.Label(textframe, text='Logging output')
            l.grid(row=0, column=0)
            self.text = tk.Text(textframe, height=10, width=80,
                                borderwidth=3, relief="sunken")#, wrap="word")
            self.vsb = tk.Scrollbar(textframe, orient='vertical', command=self.text.yview)
            self.text.configure(yscrollcommand=self.vsb.set)

            self.vsb.grid(row=1, column=0, columnspan=1, sticky='e')
            self.text.bind("<Tab>", self.focus_fw)
            self.text.grid(row=1, column=0, rowspan=1, columnspan=1)
            ####

            ### copyright label
            l = tk.Label(self, text='(c) 2014-2019 RBINS')
            l.grid(row=7, column=0, sticky='e')
            ###

        ## focus next element
        def focus_fw(self,event):
            event.widget.tk_focusNext().focus()
            return("break")

        ## focus previous element
        def focus_bw(self,event):
            event.widget.tk_focusPrevious().focus()
            return("break")

        ## select input file
        def select_input(self):
            initial_file = self.tinput.get(1.0, END).strip()
            initial_dir = os.path.dirname(initial_file)
            inputfile = filedialog.askdirectory(title='Select input scene directory.', initialdir=initial_dir)
            if len(inputfile)>0:
                self.inputfile=inputfile
                print('Selected {} as input file.'.format(self.inputfile))
                ## add to input field
                self.tinput.delete(1.0, END)
                self.tinput.insert(END,self.inputfile)

        ## select output file
        def select_output(self):
            initial_output = self.toutput.get(1.0, END).strip()
            initial_dir = os.path.dirname(initial_output)
            output = filedialog.askdirectory(title='Select output directory.', initialdir=initial_dir)
            if len(output)>0:
                 self.output = output
                 print('Selected {} as output directory.'.format(self.output))
                 ## add to output field
                 self.toutput.delete(1.0, END)
                 self.toutput.insert(END,self.output)

        ## clear ROI boxes
        def clear_ROI(self):
            self.sbox.delete(1.0, END)
            self.nbox.delete(1.0, END)
            self.wbox.delete(1.0, END)
            self.ebox.delete(1.0, END)

        def update_settings(self):
            ## set limit from boxes here
            limit = [self.sbox.get(1.0, END).strip(),
                     self.wbox.get(1.0, END).strip(),
                     self.nbox.get(1.0, END).strip(),
                     self.ebox.get(1.0, END).strip()]
            if all([len(i) > 0 for i in limit]):
                limit = [float(i) for i in limit]
                self.acolite_settings['limit']=limit
            else:
                if 'limit' in self.acolite_settings: del self.acolite_settings['limit']
            ## get inputfile and output directory
            self.acolite_settings['inputfile']=self.tinput.get(1.0,END).strip()
            self.acolite_settings['output']=self.toutput.get(1.0,END).strip()

            ## get l2w parameters
            l2w_parameters=self.tl2wpar.get(1.0,END).strip().split(',')
            if (len(l2w_parameters) == 1) and (l2w_parameters[0]==''):
                l2w_parameters = None
            else: l2w_parameters = [i.strip() for i in l2w_parameters]
            self.acolite_settings['l2w_parameters']=l2w_parameters

            ## set RGB buttons
            self.acolite_settings['rgb_rhot']=True if self.rgb_rhot.get() == 1 else False
            self.acolite_settings['rgb_rhos']=True if self.rgb_rhos.get() == 1 else False
            self.acolite_settings['map_l2w']=True if self.map_l2w.get() == 1 else False

        ## save settings to file
        def save(self):
            initial_dir=os.path.dirname(self.settings_file)
            initial_file=os.path.basename(self.settings_file)
            if sys.platform == 'darwin':
                initial_dir=None
                initial_file=None

            settings_file = filedialog.asksaveasfilename(title='Select where to save settings.', initialdir=initial_dir, initialfile=initial_file)
            if len(settings_file) > 0:
                self.settings_file = settings_file
                settings_write(settings_file, self.acolite_settings)
                try:
                    self.update_settings()
                    settings_write(settings_file, self.acolite_settings)
                    print('Wrote settings file {}'.format(settings_file))
                except:
                    print('Could not write settings file {}'.format(settings_file))

        ## restore selected settings file
        def restore(self, settings_file=None):
            if settings_file is None:
                initial_dir=os.path.dirname(self.settings_file)
                initial_file=os.path.basename(self.settings_file)
                settings_file = filedialog.askopenfilename(title='Select settings file to restore.', initialdir=initial_dir, initialfile=initial_file)
            if len(settings_file) > 0:
                self.settings_file = settings_file
                try:
                    self.setimport = settings_read(settings_file)
                    self.acolite_settings = self.setimport
                except:
                    print('Could not restore settings from {}'.format(settings_file))

                try:
                    ## clear ROI
                    self.sbox.delete(1.0, END)
                    self.nbox.delete(1.0, END)
                    self.wbox.delete(1.0, END)
                    self.ebox.delete(1.0, END)
                    ## set ROI if in settings file
                    if 'limit' in self.acolite_settings:
                        if len(self.acolite_settings['limit'])==4:
                            self.sbox.insert(1.0, self.acolite_settings['limit'][0])
                            self.nbox.insert(1.0, self.acolite_settings['limit'][2])
                            self.wbox.insert(1.0, self.acolite_settings['limit'][1])
                            self.ebox.insert(1.0, self.acolite_settings['limit'][3])
                    ## clear and set inputfile
                    self.tinput.delete(1.0, END)
                    if 'inputfile' not in self.acolite_settings: self.acolite_settings['inputfile'] = ''
                    self.tinput.insert(END,self.acolite_settings['inputfile'])

                    ## clear and set output
                    self.toutput.delete(1.0, END)
                    if 'output' not in self.acolite_settings: self.acolite_settings['output'] = ''
                    self.toutput.insert(END,self.acolite_settings['output'])

                    ##
                    if 'l2w_parameters' in self.acolite_settings:
                        self.tl2wpar.delete(1.0,END)
                        l2wpar=self.acolite_settings['l2w_parameters']
                        if type(l2wpar) is list: l2wpar = ','.join(l2wpar)
                        self.tl2wpar.insert(1.0, l2wpar)

                    ## restore RGB buttons
                    v = 1
                    tag = 'rgb_rhot'
                    if tag in self.acolite_settings: v = 1 if self.acolite_settings[tag] else 0
                    self.rgb_rhot.set(v)
                    v = 1
                    tag = 'rgb_rhos'
                    if tag in self.acolite_settings: v = 1 if self.acolite_settings[tag] else 0
                    self.rgb_rhos.set(v)
                    v = 1
                    tag = 'map_l2w'
                    if tag in self.acolite_settings: v = 1 if self.acolite_settings[tag] else 0
                    self.map_l2w.set(v)

                    ## done restoring settings
                    print('Restored settings file {}'.format(settings_file))
                    #print(self.acolite_settings)
                except:
                    print('Failed to restore settings.')

        ## run processing
        def startRun(self):
            time.sleep(0.2)
            if sys.platform not in mp_platforms:
                  self.processingRunning=False

            if self.processingRunning:
                print('Processing already running.')
            elif self.processingRunning==False:
                self.update_settings()
                if os.path.exists(self.acolite_settings['inputfile']):
                    self.processingRunning=True
                    self.processingComplete=False

                    ## test output directory
                    if os.path.exists(self.acolite_settings['output']) is False:
                         try:
                             os.makedirs(self.acolite_settings['output'])
                         except:
                             print('Could not make output directory {}'.format(self.acolite_settings['output']))
                             self.processingRunning=False

                    ## test logfile
                    if 'runid' not in self.acolite_settings:
                        self.acolite_settings['runid'] = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

                    logfile = '{}/{}'.format(self.acolite_settings['output'],'acolite_run_{}_log.txt'.format(self.acolite_settings['runid']))

                    try:
                        with open(logfile, 'w') as f: f.write('')
                    except:
                        print('Cannot write to output directory {}'.format(self.acolite_settings['output']))
                        self.processingRunning=False


                    if self.processingRunning:
                        print('Running ACOLITE processing')
                        print('Logging to file {}'.format(logfile))
                        ## Running acolite directly works - but no interruption possible
                        #acolite(settings=self.acolite_settings)

                        if sys.platform in mp_platforms:
                            ## stop stdout redirection - otherwise Process doesn't finish
                            ## probably a conflict between multithreading and the GUI loop or the button threading
                            ## too confusing to figure out right now
                            print('Logging disabled in GUI window until processing is complete.')
                            self.logging.__del__()
                            self.logging = None
                            self.logging=LogTee(logfile)

                            ## use custom Process class that returns exceptions
                            self.process = Process(target=acolite_run, kwargs={'settings':self.acolite_settings, 'gui':True})
                            self.process.start()

                            ## run processing until finished or interrupted
                            while(self.process.join() and self.processingRunning):
                                time.sleep(0.1)
                                self.update()
                                if not self.process.is_alive(): self.processingRunning=False
                        else: # windows/mac
                            print('Running ACOLITE processing on Mac/Windows.')
                            acolite_run(settings=self.acolite_settings, gui=True)


                        ## processing running has stopped
                        self.processingRunning=False

                        ## redirect stdout to the GUI again
                        if (sys.platform in mp_platforms):
                            if (not self.processingRunning):
                                self.logging.__del__()
                                self.logging = None
                                self.logging=WidgetTee(self.text)
                                #self.wt.__init__(self.text)

                        ## did we finish normally or did the user interrupt?
                        if sys.platform in mp_platforms:
                        #if True:
                            if self.process.exitcode == 0:
                                self.processingComplete=True
                                print('Finished processing.')
                            else:
                                self.processingComplete=False
                                if(self.process.exitcode == -15):
                                     print('Processing interrupted by user.')
                                else:
                                     if self.process.exception is None:
                                         print('Processing error, see log file for details.')
                                     else:
                                         print('Processing error:')
                                         for i in self.process.exception: print(i)
                        else:
                            #self.processingComplete=True
                            print('Finished processing.')
                            #self.update()
                    else:
                        print('Could not start ACOLITE processing.')

        ## halt processing
        def stopRun(self):
            if sys.platform not in mp_platforms:
                print('ACOLITE processing on Windows is currently not interruptible.')
            else:
                if self.processingRunning:
                    print(self.process)
                    self.processingRunning=False
                    if self.process is not None:
                        if self.process.is_alive(): self.process.terminate()
                        print("Processing stopped by user.")
                    self.update()
                    time.sleep(1)
                else: print("No processing running.")

        ## stop and exit
        def stopExit(self):
            if self.processingRunning: self.stopRun()
            print('Exiting.')
            self.update()
            time.sleep(0.25)
            self.destroy()


    ## object for copying stdout to widget text element for GUI logging
    class WidgetTee(object):
        def __init__(self, widget):
            self.widget = widget
            self.stdout = sys.stdout
            sys.stdout = self
        def __del__(self):
            sys.stdout = self.stdout
        def write(self, data):
            self.stdout.write(data)
            self.widget.configure(state="normal") ## make writable
            self.widget.insert(END, data) #, (self.tag,)
            self.widget.configure(state="disabled") ## lock writing
            self.widget.see(END)
        def flush(self):
            pass

    ## object for logging stdout to log file when processing
    class LogTee(object):
        def __init__(self, name):
            self.name=name
            ## make new file
            self.file = open(self.name, 'w')
            self.file.close()
            self.mode='a'
            self.stdout = sys.stdout
            sys.stdout = self
        def __del__(self):
            sys.stdout = self.stdout
        def write(self, data):
            self.stdout.write(data)
            data = data.strip()
            if len(data) > 0:
                self.file = open(self.name, self.mode)
                self.file.write('{}: {}\n'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),data))
                self.file.close()
        def flush(self):
            pass

    root=acgui()
    root.mainloop()
    #print('End.')

## start and run GUI
if __name__ == "__main__":
    ret = acolite_gui()
