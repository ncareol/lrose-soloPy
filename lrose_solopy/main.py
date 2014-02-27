# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
# ** Copyright UCAR (c) 1992 - 2014 
# ** University Corporation for Atmospheric Research(UCAR) 
# ** National Center for Atmospheric Research(NCAR) 
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA 
# ** See LICENSE.TXT for license details
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
#/usr/bin/python

from PySide import QtGui as gui
from PySide import QtCore as core

import sys
import os,os.path

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from RadialDisplay import RadialDisplay,MyFrame,MplCanvas,MplCanvasBSCAN
from CfRadial import CfRadial
from Config import Config
from ColorMap import ColorMap
from Logger import Logger
from utility import determine_pkg_path
import argparse
VERSION="SoloPy 0.5"

class DisplayParams:
    pass

class MainWindow(gui.QMainWindow):

    BSCANMODE = "BSCAN"
    BASICMODE = "BASIC"
    

    """ Main application window """
    def __init__(self, parent=None, config_file=None, data_dir=None, colormap_dir=None):
        """ create a new MainWindow """
        super(MainWindow, self).__init__(parent) 

        ## read config.xml to retrieve default information
        try:
            self.cfg = Config(config_file)
        except RuntimeError, e:
            print e
            sys.exit(1)

        ## nc file dir
        self.versionStr = VERSION
        self.data_dir = data_dir
        if self.data_dir is None:
            self.data_dir = self.cfg.config['data-dir']

        ## locate the color map dir
        if colormap_dir is None:
            # caller didn't provide - try user specified directory
            colormap_dir = os.path.expanduser(self.cfg.config['colorfile-dir'])
            if not os.path.exists(colormap_dir):
                # can't find user specified colormaps - use defaults
                colormap_dir = os.path.join(determine_pkg_path(), "color_scales")
        self.colormap = ColorMap(self.cfg.config['colorfiles'],
                                 colormap_dir)

        # initialize window size and position
        width = self.cfg.config['window-size'][0]
        height = self.cfg.config['window-size'][1]
        self.resize(width, height) # size
        self.mode = self.cfg.config['plot-mode']

        self.setMinimumSize(width, height) # minimum size
        self.move(200, 200) # position window frame at top left
        self.setWindowTitle(self.versionStr)

        self.main_ = gui.QFrame(self)
        self.filename = None
        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                                           gui.QKeySequence.Open, "fileopen","Open CfRadial File")
        fileQuitAction = self.createAction("&Quit", gui.qApp.quit,
                                           "Ctrl+Q", "filequit", "Close the application")
        exportAction = self.createAction('&Export PNG File', self.exportAction,'Ctrl+E','export','Export PNG File')

        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenuActions = (fileOpenAction, exportAction, fileQuitAction)
        self.fileMenu.addActions(self.fileMenuActions)
        self.connect(self.fileMenu, core.SIGNAL("aboutToShow()"),
                     self.updateFileMenu)
        settings = core.QSettings()

        # add unZoom button on menu bar
        unzoomAction = gui.QAction('&Unzoom', self)
        unzoomAction.setShortcut('Ctrl+U')
        unzoomAction.setStatusTip('Unzoom')
        unzoomAction.triggered.connect(self.unzoomButtonAction)
        self.menuBar().addAction(unzoomAction)

        # add BackZoom on menu bar
        backAction = gui.QAction('&ZoomBack', self)
        backAction.setShortcut('Ctrl+B')
        backAction.setStatusTip('ZoomBack')
        backAction.triggered.connect(self.backButtonAction)
        self.menuBar().addAction(backAction)

        # submenu to Options
        rangeRingAction = gui.QAction('&Range Rings', self,checkable=True)
        rangeRingAction.setShortcut('Ctrl+Z')
        rangeRingAction.setStatusTip('Range Rings')
        rangeRingAction.triggered.connect(self.rangeRingAction)

        azimuthAction = gui.QAction('&Azimuth Lines', self,checkable=True)
        azimuthAction.setShortcut('Ctrl+A')
        azimuthAction.setStatusTip('Azimuth')
        azimuthAction.triggered.connect(self.azimuthAction)

        pickerAction = gui.QAction('&Picker Label', self,checkable=True)
        pickerAction.setShortcut('Ctrl+P')
        pickerAction.setStatusTip('Picker Label')
        pickerAction.triggered.connect(self.pickerLabelAction)

        colorbarAction = gui.QAction('&ColorBar', self,checkable=True)
        colorbarAction.setShortcut('Ctrl+C')
        colorbarAction.setStatusTip('Color Bar')
        colorbarAction.setChecked(True)
        colorbarAction.setEnabled(False) ## disable changing for the current being
        colorbarAction.triggered.connect(self.colorbarAction)

        # add Options on meun bar
        optionMenu = self.menuBar().addMenu('Options')
        optionMenu.addAction(rangeRingAction)
        optionMenu.addAction(azimuthAction)
        optionMenu.addAction(pickerAction)
        optionMenu.addAction(colorbarAction)
        
        # add help menu
        helpAction = gui.QAction(gui.QIcon('help.png'), '&Help Content', self)        
        helpAction.setShortcut('Ctrl+H')
        helpAction.setStatusTip('Help')
        helpAction.triggered.connect(self.helpOpen)

        aboutAction = gui.QAction(gui.QIcon('about.png'), '&About', self)
        aboutAction.setShortcut('Ctrl+A')
        aboutAction.setStatusTip('About')
        aboutAction.triggered.connect(self.helpAbout)

        helpMenu = self.menuBar().addMenu('&Help')
        helpMenu.addAction(helpAction)
        helpMenu.addSeparator()
        helpMenu.addAction(aboutAction)
        
        rf = settings.value("RecentFiles")
        self.recentFiles = []
        if rf:
            self.recentFiles = rf.toStringList()

        self.updateFileMenu()
        params = DisplayParams()
        params.background_color = 'Red'


        ''' mpl plot variables from nc file'''
        '''
        frame = MyFrame(self.main_)
        frame.setSizePolicy(gui.QSizePolicy.Expanding, gui.QSizePolicy.Expanding)
        self.radialDisplay = RadialDisplay(params, frame)
        frame.connectSizeChanged(self.radialDisplay.resize)
        self.radialDisplay.show()
        self.setCentralWidget(frame)
        '''

        # create an area to contain the radiobuttons used to select fields
        self.fieldDock = gui.QDockWidget("Field Selection")
        self.fieldDock.setAllowedAreas(core.Qt.LeftDockWidgetArea |
                                       core.Qt.RightDockWidgetArea)
        self.fieldDock.setFeatures(gui.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(core.Qt.LeftDockWidgetArea, self.fieldDock)

#        self.createFieldSelection(['Default', ])

        self.msgLabel = gui.QLabel()
        self.msgLabel.setFrameStyle(gui.QFrame.StyledPanel|gui.QFrame.Sunken)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.msgLabel)
        status.showMessage("Ready", 5000)

        # create an area to contain the radiobuttons used to select sweep
        self.fieldDockSweep = gui.QDockWidget("Elevation Selection")
        self.fieldDockSweep.setAllowedAreas(core.Qt.RightDockWidgetArea)
        self.fieldDockSweep.setFeatures(gui.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(core.Qt.RightDockWidgetArea, self.fieldDockSweep)

        self.selected_var = None
        self.last_var = None
        self.selected_sweep = None
        self.selected_sweep_index = 0
        self.last_sweep = None

        self.main_.setFocus()
        self.startField = self.cfg.config['start-field']
        try:
            self.filename = self.getDefaultFile(self.data_dir)
        except RuntimeError, e:
            print e
            sys.exit(1)

        self.cf = CfRadial(self.filename)
        tmp = [v.lower() for v in self.cf.variables]

        try:
            if self.startField.lower() not in tmp:
                raise RuntimeError( "Start field \"%s\" not found in configuration file" % self.startField)
                sys.exit(1)
        except RuntimeError, e:
            print e
            sys.exit(1)
    
        if self.mode == self.BSCANMODE:
            self.mpl = MplCanvasBSCAN("", None, parent=self.main_, width=3, height=3, dpi=100)
        else:
            self.mpl = MplCanvas(self.cfg.config['header-label'], self.colormap, parent=self.main_, width=3, height=3, dpi=100)

        self.setCentralWidget(self.mpl)

        ## display the defalut file
        self.display()

    def getDefaultFile(self,path):
        """ get the first nc file under specified directory as default """
        files = []
        for r,d,f in os.walk(os.path.expanduser(path)):
            for fn in f:
                if fn.endswith(".nc"):
                    files.append( os.path.join(r,fn) )
        if files == []:
            msgBox = gui.QMessageBox()
            msgBox.setText(
            """Could not find any data files in %s
            Please edit your configuration file ('~/solopy_config.xml') or
            supply a '-I data_file_dir' command line argument
            """ % path)
            msgBox.exec_()
            raise RuntimeError("Could not find any data files in %s" % path)
                               
        return files[0]

    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        """ create a QAction with optional slot, shortcut, icon, and tip"""
        action = gui.QAction(text, self)
        if icon is not None:
            action.setIcon(gui.QIcon(":/{0}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, core.SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def createFieldSelection( self, fieldNames ): 
        """ create a set of radio buttons to select one from 'fieldName' """
        groupBox = gui.QGroupBox("Variables")
        vbox = gui.QVBoxLayout();
        groupBox.setLayout(vbox)

        scrollWidget = gui.QScrollArea()
        scrollWidget.setWidget(groupBox)
        scrollWidget.setWidgetResizable(True)  # Set to make the inner widget resize with scroll area
        self.fieldDock.setWidget(scrollWidget)

        self.fieldButtons = {}
        for f in fieldNames:
            rb = gui.QRadioButton(f)
            core.QObject.connect(rb,core.SIGNAL('toggled(bool)'),self.repaintCfRadialVar)
            self.fieldButtons[f] = rb
            vbox.addWidget(rb)

        if self.startField and self.startField.strip()!="":
            ## check the startField as default if setup in config.xml file
            ## startField in config.xml must be exactly the same as the variable name read from nc file - key of dict
            self.fieldButtons[self.startField].setChecked(True)
        else:
            ## check the first one as default
            self.fieldButtons[fieldNames[0]].setChecked(True)

    def createFieldSweepSelection( self, fieldNames): 
        """ create a set of radio buttons to select sweep """
        fieldNames = self.sweep_index = [str(f) for f in fieldNames]

        groupBox = gui.QGroupBox("Elevation")
        vbox = gui.QVBoxLayout();
        groupBox.setLayout(vbox)

        scrollWidget = gui.QScrollArea()
        scrollWidget.setWidget(groupBox)
        scrollWidget.setWidgetResizable(True)  # Set to make the inner widget resize with scroll area
        self.fieldDockSweep.setWidget(scrollWidget)

        self.fieldButtonSweep = {}
        for f in fieldNames:
            rb = gui.QRadioButton(f)
            core.QObject.connect(rb,core.SIGNAL('toggled(bool)'),self.repaintSweep)
            self.fieldButtonSweep[f] = rb
            vbox.addWidget(rb)

        self.fieldButtonSweep[fieldNames[0]].setChecked(True)

    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def updateFileMenu(self):
        """ utility to maintain file menu """
        self.fileMenu.clear()
        self.addActions(self.fileMenu, self.fileMenuActions[:-1])
        current = (self.filename if self.filename is not None else None)
        recentFiles = []
        for fname in self.recentFiles:
            if fname != current and QFile.exists(fname):
                recentFiles.append(fname)
        if recentFiles:
            self.fileMenu.addSeparator()
            for i, fname in enumerate(recentFiles):
                action = gui.QAction(gui.QIcon(":/icon.png"),
                                     "&{0} {1}".format(i + 1, QFileInfo(
                                         fname).fileName()), self)
                action.setData(fname)
                self.connect(action, SIGNAL("triggered()"),
                             self.loadFile)
                self.fileMenu.addAction(action)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.fileMenuActions[-1])

    def drawSweeps(self, sweeps,var_list, index):
        """ draw a set of sweeps - stubbed to draw a single sweep """
        print 'drawSweeps  index = ',index
        ##TODO - draw multiple sweeps
        try:
            self.mpl.drawSweep(sweeps[index],var_list[0], 1.0)
        except RuntimeError, e:
            print e
            sys.exit(1)

    def repaintCfRadialVar(self):
        print "repaintCfRadialVar"
        """ retrieve CfRadial variables and repaint - support only one variable so far"""
        flagRepaint = False
        self.var_list = []
        for k,v in self.fieldButtons.items():
            if v.isChecked():
                if k != self.selected_var:
                    print k
                    flagRepaint = True
                    self.last_var = self.selected_var ## store last selected var
                    self.selected_var = k
        self.var_list = [self.selected_var]
        if flagRepaint == True:
            #self.mpl.resetFactors() ## don't reset, keep using the current zoom window
            #self.mpl = MplCanvas(self.filename, self.main_, width=3, height=3, dpi=100)
            self.drawSweeps(self.sweeps,self.var_list,self.selected_sweep_index)

    def repaintSweep(self):
        print "repaintSweep"
        """ repaint sweep after selection change """
        flagRepaint = False
        for k,v in self.fieldButtonSweep.items():
            if v.isChecked():
                if k != self.selected_sweep:
                    flagRepaint = True
                    self.last_sweep = self.selected_sweep ## store last selected sweep
                    self.selected_sweep = k ## current sweep
        self.selected_sweep_index = self.sweep_index.index(self.selected_sweep) ## get the index of the selected sweep
        if flagRepaint == True:
            self.drawSweeps(self.sweeps,self.var_list,self.selected_sweep_index)

    def keyPressEvent(self, event):
        key = event.key()
        if key == 46: # '.', toggle between last and current fields
            if self.last_var != None:
                tmp = self.last_var
                self.last_var = self.selected_var
                self.selected_var = tmp
                self.fieldButtons[self.selected_var].setChecked(True) # update selection on Gui
                self.drawSweeps(self.sweeps,[self.selected_var],self.selected_sweep_index)
                
    def fileOpen(self):
        """ callback for File->Open menu action """
        result = gui.QFileDialog.getOpenFileName(self, "Open Data File", self.data_dir, "netCDF data files (*.nc)")
        # result is a tuple, just want the filename
        self.filename = result[0]
        self.selected_var = None
        self.last_var = None
        self.selected_sweep = None
        self.selected_sweep_index = 0
        self.last_sweep = None
        self.display()

    def display(self):
        self.cf = CfRadial(self.filename)
        self.sweeps = self.cf.readFile()

        self.createFieldSelection(self.cf.variables)
        if self.mode == self.BASICMODE:
            self.createFieldSweepSelection(self.cf.sweepElevation)
        #self.drawSweeps(self.sweeps,[self.cf.variables[0]])

    def helpOpen(self):
        """ display help content """
        string = "Clicking the left mouse button to move the center of the plot. \n"
        string = string + "Clicking key 'c' to reset plotting parameters. \n"
        self.label = gui.QLabel(string)
        self.label.setGeometry(core.QRect(300, 200, 400, 100))
        self.label.setWindowTitle("Help")
        self.label.show()

    def helpAbout(self):
        """ display about information """
        string = self.versionStr
        string = string + "\nSept 5, 2013 \n"
        self.labelabout = gui.QLabel(string)
        self.labelabout.setGeometry(core.QRect(300, 200, 200, 100))
        self.labelabout.setWindowTitle("About")
        self.labelabout.show()

    def closeEvent(self, event):
        """ close window """
        gui.QMainWindow.closeEvent(self, event)

    def clearButtonAction(self):
        """ reset all params for plotting """
        self.mpl.resetFactors()
#        self.drawSweeps(self.sweeps,self.var_list)
#        self.mpl.update()

    def unzoomButtonAction(self):
        """ unzoom and reset plotting to origin"""
        self.mpl.changeZoomerPointer(-1)

    def backButtonAction(self):
        self.mpl.changeZoomerPointer()

    def resizeEvent(self, event):
        self.update()

    def rangeRingAction(self):
        """ change zenith indicator """
        if self.mpl:
            self.mpl.RANGE_RING = not self.mpl.RANGE_RING
            self.mpl.update_figure()

    def azimuthAction(self):
        """ change azimuth indicator """
        if self.mpl:
            self.mpl.AZIMUTH = not self.mpl.AZIMUTH
            self.mpl.update_figure()

    def pickerLabelAction(self):
        if self.mpl:
            self.mpl.PICKER_LABEL = not self.mpl.PICKER_LABEL

    def colorbarAction(self):
        """ change azimuth indicator """
        if self.mpl:
            self.mpl.COLORBAR = not self.mpl.COLORBAR
            self.mpl.update_figure()

    def exportAction(self):
        """ export current display to png file """
        if self.mpl:
            filename = gui.QFileDialog.getSaveFileName(self,
                                                       "Save plots as PNG file",self.data_dir,"PNG File (*.png)")
            self.mpl.fig.savefig(filename)

def parse_arg():
    """ parse command line options """
    """ usage: -p params_file -I input_dir -c colormap_dir -d debug_level """
    dir_ncfile = None
    dir_colorfile = None
    config_file = None

    parser = argparse.ArgumentParser(description='SoloPy 0.5')
    parser.add_argument("-p","--params", 
                        help="setup the dir of configuration file")
    parser.add_argument("-I","--input_dir", 
                        help="setup the default dir for looking up data file")
    parser.add_argument("-c","--colormap_dir", 
                        help="setup the default dir for looking up color scale files")
    parser.add_argument("-d","--debug", type=int, #choices=xrange(0, 10),
                        help="setup debug level")
    args = parser.parse_args()

    ## config file setup
    if args.params:
        print ("config : %s" % args.params)
        if os.path.isfile(args.params):
            config_file = args.params
        else:
            raise parser.error( "Invalid params_file: %s." % args.params )

    ## data file dir setup
    if args.input_dir:
        print ("input_dir : %s" % args.input_dir)
        if os.path.isdir(args.input_dir):
            files = []
            for r,d,f in os.walk(os.path.expanduser(args.input_dir)):
                for fn in f:
                    if fn.endswith(".nc"):
                        files.append( os.path.join(r,fn) )
            if len(files) > 0:
                dir_ncfile = args.input_dir
            else:
                raise parser.error( "No data file found in %s and and its sub directory." % args.input_dir )
        else:
            raise parser.error( "Invalid input_dir: %s." % args.input_dir )

    ## color file dir setup
    if args.colormap_dir:
        print ("colormap_dir : %s" % args.colormap_dir)
        if os.path.isdir(args.colormap_dir):
            files = [f for f in os.listdir(args.colormap_dir) if f.endswith('.colors')]
            if len(files) > 0:
                ## rewrite the value in config.xml ##
                dir_colorfile = args.colormap_dir            
            else:
                ## error message to
                raise parser.error( "No color file found in %s." % args.colormap_dir)
        else:
            raise parser.error( "Invalid colormap_dir: %s." % args.colormap_dir)

    ## debug level setup
    if args.debug:
        print ("debug_level : %s" % args.debug)
        if args.debug > 0:
            pysolo_logger = Logger(args.debug)
        else:
            raise argparse.ArgumentTypeError( "Invalid debug_level dir: %s." % args.debug)

    return config_file, dir_ncfile, dir_colorfile

def main(argv):
    ## parse command line options
    config_file, data_dir, colormap_dir = parse_arg()

    app = gui.QApplication(argv)
    app.setApplicationName(VERSION)
    form = MainWindow(config_file=config_file,data_dir=data_dir,colormap_dir = colormap_dir)
    form.show()
    try:
        sys.exit(app.exec_())
    except RuntimeError, e:
        print e
        sys.exit(1)    
    
def start():
    """ entry point called by run_solopy script """
    main(sys.argv)

if __name__ == '__main__':
    main(sys.argv)
