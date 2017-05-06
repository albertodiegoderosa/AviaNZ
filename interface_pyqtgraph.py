# Interface.py
#
# This is the main class for the AviaNZ interface
# It's fairly simple, but seems to work OK
# Version 0.10 16/04/17
# Author: Stephen Marsland, with input from Nirosha Priyadarshani

#     <one line to give the program's name and a brief idea of what it does.>
#    Copyright (C) <year>  <name of author>

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os, json  #glob
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import PyQt4.phonon as phonon

import wavio
#from scipy.io import wavfile
import numpy as np

import pyqtgraph as pg
pg.setConfigOption('background','w')
pg.setConfigOption('foreground','k')
pg.setConfigOption('antialias',True)
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.dockarea import *
import pyqtgraph.functions as fn

import SupportClasses as SupportClasses
import Dialogs as Dialogs

import SignalProc
import Segment
#import Features
#import Learning
# ==============
# TODO

# Make the median filter on the spectrogram have params and a dialog. Other options?

# Finish implementation to show individual segments to user and ask for feedback and the other feedback dialogs
# Ditto lots of segments at once
# Also, option to show a species
    # TODO: There is a small problem here that you have to click twice the first time. Is it true on Windows?

# Decide on license

# Finish segmentation
#   Mostly there, need to test them
#   Add a minimum length of time for a segment, debug the segmentation algorithms -> make this a parameter
#   Finish sorting out parameters for median clipping segmentation, energy segmentation
#   Finish cross-correlation to pick out similar bits of spectrogram -> and what other methods?
#   Add something that aggregates them -> needs planning

# Fundamental frequency
#   Finish plotting with line -- need to split into pieces and plot each individually
#   Smoothing?
#   Add shape metric
#   Try the harvest f0
#   Try yaapt or bana (tried yaapt, awful)

# Finish the raven features

# Add in the wavelet segmentation for kiwi, ruru
# Think about nice ways to train them

# Would it be good to smooth the image? Actually, lots of ideas here! Might be nice way to denoise?
    # Median filter, smoothing, consider also grab-cut
    # Continue to play with inverting spectrogram

# Colourmaps
    # HistogramLUTItem

# Mouse location printing -> Is it correct? Better place?

# Make the scrollbar be the same size as the spectrogram -> hard!
# Make the segmented play work with the phonon player? -> hard!

# Context menu different for day and night birds?

# The ruru file is a good one to play with for now

# Show a mini picture of spectrogram images by the bird names in the file, or a cheat sheet or similar

# Is there something weird with spectrogram and denoising? Why are there spikes?
# Should load in the new sound file after denoising and play that

# Have a busy bar when computing?

# Look into ParameterTree for saving the config stuff in particular
# Better loading of files -> paging, not computing whole spectrogram (how to deal with overview? -> coarser spec?)
    # Maybe: check length of file. If > 5 mins, load first 5 only (? how to move to next 5?)

# Implement something for the Classify function:
    # Take the segments that have been given and try to classify them in lots of ways:
    # Cross-correlation, DTW, shape metric, features and learning

# Some bug in denoising? -> tril1

# Needs decent testing

# Option to turn button menu on/off?

# Minor:
# Turn stereo sound into mono using librosa, consider always resampling to 22050Hz (except when it's less in file :) )
# Font size to match segment size -> make it smaller, could also move it up or down as appropriate
# Use intensity of colour to encode certainty?
# Is play all useful? Would need to move the plots as appropriate
# If don't select something in context menu get error -> not critical
# Colours of the segments to be visible with different colourmaps? Not important!
# The updating of the colour of the overview seg has some colour weirdness -- gets darker. Some sort of overlapping? Not a major problem.

# Things to consider:
    # Second spectrogram (currently use right button for interleaving)? My current choice is no as it takes up space
    # Put the labelling (and loading) in a dialog to free up space? -> bigger plots

# Look at raven and praat and luscinia -> what else is actually useful? Other annotations on graphs?

# Given files > 5 mins, split them into 5 mins versions anyway (code is there, make it part of workflow)
# Don't really want to load the whole thing, just 5 mins, and then move through with arrows -> how?
# This is sometimes called paging, I think. (y, sr = librosa.load(filename, offset=15.0, duration=5.0) might help. Doesn't do much for the overview through)

# As well as this version with pictures, will need to be able to call various bits to work offline
# denoising, segmentation, etc. that will then just show some pictures

# Things to remember
    # When adding new classes, make sure to pass new data to them in undoing and loading

# This version has the selection of birds using a context menu and then has removed the radio buttons
# Code is still there, though, just commented out. Add as an option?

# Get suggestions from the others

# Diane:
    # menu
    # for matching, show matched segment, and extended 'guess' (with some overlap)
    # Something to show nesting of segments, such as a number of segments in the top bit
    # Find similar segments in other files -- other birds
    # Group files by species

# Rebecca:
    # x colour spectrogram
    # x add a marker on the overview to show where you have marked segments, with different colours for unknown, possible
    # x reorder the list dynamically by amount of use -> done, but maybe it should be an option?
    # Maybe include day or night differently in the context menu
    # x have a hot key to add the same bird repeatedly
    # Change the visible window width (or just add) magnify/shrink buttons
    # x Add date, time, person, location, would be good to have weather info calculated automatically (wind, rain -> don't bother), broken sound recorder

    # pull out any bird call (useful for if you don't know what a bird sounds like (Fiji petrel) or wind farm monitoring)
    # do bats!
    # Look up David Bryden (kokako data) looking at male, female, juvenile
    # Get all calls of a species
    # Look up freebird and raven and also BatSearch
# ===============

class AviaNZInterface(QMainWindow):
    # Main class for the interface, which contains most of the user interface and plotting code

    def __init__(self,root=None,configfile=None):
        # Main part of the initialisation is loading a configuration file, or creating a new one if it doesn't
        # exist. Also loads an initial file (specified explicitly) and sets up the window.
        # TODO: better way to choose initial file (or don't choose one at all)
        super(AviaNZInterface, self).__init__()
        self.root = root
        if configfile is not None:
            try:
                self.config = json.load(open(configfile))
                self.saveConfig = False
            except:
                print("Failed to load config file")
                self.genConfigFile()
                self.saveConfig = True
            self.configfile = configfile
        else:
            self.genConfigFile()
            self.saveConfig=True
            self.configfile = 'AviaNZconfig.txt'

        # The data structures for the segments
        self.listLabels = []
        self.listRectanglesa1 = []
        self.listRectanglesa2 = []
        self.SegmentRects = []
        self.box1id = -1

        self.lastSpecies = "Don't Know"
        self.resetStorageArrays()

        self.dirName = self.config['dirpath']
        self.previousFile = None
        self.focusRegion = None

        # Make the window and associated widgets
        QMainWindow.__init__(self, root)
        self.setWindowTitle('AviaNZ')

        # Make life easier for now: preload a birdsong
        self.firstFile = 'tril1.wav' #'male1.wav' # 'kiwi.wav'#'
        #self.firstFile = 'kiwi.wav'

        self.createMenu()
        self.createFrame()

        # Some safety checking for paths and files
        if not os.path.isdir(self.dirName):
            print("Directory doesn't exist: making it")
            os.makedirs(self.dirName)
        if not os.path.isfile(self.dirName+'/'+self.firstFile):
            fileName = QtGui.QFileDialog.getOpenFileName(self, 'Choose File', self.dirName, "Wav files (*.wav)")
            if fileName:
                self.firstFile = fileName
        self.loadFile(self.firstFile)

        # Save the segments every minute
        self.timer = QTimer()
        QObject.connect(self.timer, SIGNAL("timeout()"), self.saveSegments)
        self.timer.start(self.config['secsSave']*1000)

    def createMenu(self):
        # Create the menu entries at the top of the screen.

        fileMenu = self.menuBar().addMenu("&File")
        fileMenu.addAction("&Open sound file", self.openFile, "Ctrl+O")
        #fileMenu.addSeparator()
        fileMenu.addAction("Quit",self.quit,"Ctrl+Q")
        fileMenu.addAction("&Quit",self.quit,"Ctrl+Q")

        specMenu = self.menuBar().addMenu("&Interface")

        self.useAmplitudeTick = specMenu.addAction("Show amplitude plot", self.useAmplitudeCheck)
        self.useAmplitudeTick.setCheckable(True)
        self.useAmplitudeTick.setChecked(True)
        self.useAmplitude = True

        self.useFilesTick = specMenu.addAction("Show list of files", self.useFilesCheck)
        self.useFilesTick.setCheckable(True)
        self.useFilesTick.setChecked(True)
        self.useFiles = True

        self.showOverviewSegsTick = specMenu.addAction("Show annotation overview", self.showOverviewSegsCheck)
        self.showOverviewSegsTick.setCheckable(True)
        self.showOverviewSegsTick.setChecked(True)
        self.showOverviewSegs = True

        self.dragRectangles = specMenu.addAction("Drag boxes in spectrogram", self.dragRectanglesCheck)
        self.dragRectangles.setCheckable(True)
        self.dragRectangles.setChecked(False)

        self.showFundamental = specMenu.addAction("Show fundamental frequency", self.showFundamentalFreq)
        self.showFundamental.setCheckable(True)
        self.showFundamental.setChecked(False)

        self.showFundamental2 = specMenu.addAction("Show fundamental frequency2", self.showFundamentalFreq2)
        self.showFundamental2.setCheckable(True)
        self.showFundamental2.setChecked(False)

        self.showInvSpec = specMenu.addAction("Show inverted spectrogram", self.showInvertedSpectrogram)
        self.showInvSpec.setCheckable(True)
        self.showInvSpec.setChecked(False)

        self.redoaxis = specMenu.addAction("Make frequency axis tight", self.redoFreqAxis)

        colMenu = specMenu.addMenu("&Choose colour map")
        colGroup = QActionGroup(self)
        for colour in self.config['ColourList']:
            cm = colMenu.addAction(colour)
            cm.setCheckable(True)
            if colour==self.config['ColourList'][0]:
                cm.setChecked(True)
            receiver = lambda cmap=colour: self.setColourMap(cmap)
            self.connect(cm, SIGNAL("triggered()"), receiver)
            colGroup.addAction(cm)
        specMenu.addAction("Invert colour map",self.invertColourMap)
        self.cmapInverted = False

        specMenu.addSeparator()
        specMenu.addAction("Change spectrogram parameters",self.showSpectrogramDialog)

        actionMenu = self.menuBar().addMenu("&Actions")
        actionMenu.addAction("&Delete all segments", self.deleteAll, "Ctrl+D")
        actionMenu.addAction("Denoise",self.denoiseDialog)
        actionMenu.addAction("Segment",self.segmentationDialog)
        actionMenu.addAction("Find matches",self.findMatches)
        actionMenu.addAction("Filter spectrogram",self.medianFilterSpec)
        actionMenu.addAction("Denoise spectrogram",self.denoiseImage)
        actionMenu.addSeparator()
        actionMenu.addAction("Check segments 1",self.humanClassifyDialog1)
        actionMenu.addAction("Check segments 2",self.humanClassifyDialog2)
        actionMenu.addSeparator()
        actionMenu.addAction("Put docks back",self.dockReplace)

        helpMenu = self.menuBar().addMenu("&Help")
        #aboutAction = QAction("About")
        helpMenu.addAction("About",self.showAbout)
        helpMenu.addAction("About",self.showAbout)
        helpMenu.addAction("Help",self.showHelp)

        #quitAction = QAction("&Quit", self)
        #self.connect(quitAction, SIGNAL("triggered()"), self.quit)
        #self.fileMenu.addAction(quitAction)

    def showAbout(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("The AviaNZ Program, v0.10 (April 2017)")
        msg.setInformativeText("By Stephen Marsland, Massey University (2016--2017). With input from Nirosha Priyadarshani, Isabel Castro, Moira Pryde, Stuart Cockburn, Rebecca Stirnemann. s.r.marsland@massey.ac.nz")
        msg.setWindowTitle("About")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        return

    def showHelp(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Open the pdf file Docs/AvianzManual.pdf")
        msg.setWindowTitle("Help")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        return

    def genConfigFile(self):
        # Generates a configuration file with default values for parameters
        # These are quite hard to change currently (edit text file, or delete the file and make another)
        # TODO: enable parameter changing
        print("Generating new config file")
        self.config = {
            # Params for spectrogram
            'window_width': 256,
            'incr': 128,

            # Params for denoising
            'maxSearchDepth': 20,

            # Params for segmentation
            'minSegment': 50,
            'dirpath': './Sound Files',
            'secsSave': 60,

            # Param for width in seconds of the main representation
            'windowWidth': 10.0,

            # Text offset for labels
            'textoffset': 9,

            # Width of the segment markers in the overview plot (in seconds)
            'widthOverviewSegment': 10.0,

            # These are the contrast parameters for the spectrogram
            #'colourStart': 0.25,
            #'colourEnd': 0.75,
            'brightness': 50,
            'contrast': 50,
            'coloursInverted': False,

            # Params for cross-correlation and related
            'corrThr': 0.4,
            # Amount of overlap for 2 segments to be counted as the same
            'overlap_allowed': 5,

            'BirdButtons1': ["Bellbird", "Bittern", "Cuckoo", "Fantail", "Hihi", "Kakapo", "Kereru", "Kiwi (F)", "Kiwi (M)",
                             "Petrel"],
            'BirdButtons2': ["Rifleman", "Ruru", "Saddleback", "Silvereye", "Tomtit", "Tui", "Warbler", "Not Bird",
                             "Don't Know", "Other"],
            'ListBirdsEntries': ['Albatross', 'Avocet', 'Blackbird', 'Bunting', 'Chaffinch', 'Egret', 'Gannet', 'Godwit',
                                 'Gull', 'Kahu', 'Kaka', 'Kea', 'Kingfisher', 'Kokako', 'Lark', 'Magpie', 'Plover',
                                 'Pukeko', "Rooster" 'Rook', 'Thrush', 'Warbler', 'Whio'],
            'BirdList': ["Bellbird", "Bittern", "Cuckoo", "Fantail", "Hihi", "Kakapo", "Kereru", "Kiwi (F)", "Kiwi (M)","Petrel","Rifleman", "Ruru", "Saddleback", "Silvereye", "Tomtit", "Tui", "Warbler", "Not Bird", "Don't Know",'Albatross', 'Avocet', 'Blackbird', 'Bunting', 'Chaffinch', 'Egret', 'Gannet', 'Godwit','Gull', 'Kahu', 'Kaka', 'Kea', 'Kingfisher', 'Kokako', 'Lark', 'Magpie', 'Plover','Pukeko', "Rooster" 'Rook', 'Thrush', 'Warbler', 'Whio'],

            'ColourList': ['Grey','Viridis', 'Inferno', 'Plasma', 'Autumn', 'Cool', 'Bone', 'Copper', 'Hot', 'Jet','Thermal','Flame','Yellowy','Bipolar','Spectrum'],
            # The colours for the segment boxes
            'ColourNone': (0, 0, 255, 100), # Blue
            'ColourSelected': (0, 255, 0, 100), # Green
            'ColourNamed': (255, 0, 0, 100), # Red
            'ColourPossible': (255, 255, 0, 100), # Yellow

            'cmap': 'Grey'
        }

    def createFrame(self):
        # This creates the actual interface. Some Qt, some PyQtGraph

        # Make the window and set its size
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.resize(1240,600)
        self.move(100,50)

        # Make the docks
        self.d_overview = Dock("Overview",size = (1200,150))
        self.d_ampl = Dock("Amplitude",size=(1200,150))
        self.d_spec = Dock("Spectrogram",size=(1200,300))
        self.d_controls = Dock("Controls",size=(40,100))
        self.d_files = Dock("Files",size=(40,200))
        #self.d_buttons = Dock("Buttons",size=(800,100))

        #self.area.addDock(self.d_files,'left',self.d_overview)
        self.area.addDock(self.d_files,'left')
        #self.area.addDock(self.d_overview,'top')
        self.area.addDock(self.d_overview,'right',self.d_files)
        self.area.addDock(self.d_ampl,'bottom',self.d_overview)
        self.area.addDock(self.d_spec,'bottom',self.d_ampl)
        self.area.addDock(self.d_controls,'bottom',self.d_files)
        #self.area.addDock(self.d_buttons,'bottom',self.d_controls)

        # Put content widgets in the docks
        self.w_overview = pg.LayoutWidget()
        self.d_overview.addWidget(self.w_overview)
        self.w_overview1 = pg.GraphicsLayoutWidget()
        self.w_overview.addWidget(self.w_overview1)
        self.p_overview = self.w_overview1.addViewBox(enableMouse=False,enableMenu=False,row=0,col=0)
        self.p_overview2 = self.w_overview1.addViewBox(enableMouse=False, enableMenu=False, row=1, col=0)
        self.p_overview2.setXLink(self.p_overview)

        self.w_ampl = pg.GraphicsLayoutWidget()
        self.p_ampl = self.w_ampl.addViewBox(enableMouse=False,enableMenu=False)
        self.w_ampl.addItem(self.p_ampl,row=0,col=1)
        self.d_ampl.addWidget(self.w_ampl)

        # The axes
        self.timeaxis = SupportClasses.TimeAxis(orientation='bottom')
        self.timeaxis.linkToView(self.p_ampl)
        self.timeaxis.setLabel('Time',units='mm:ss')

        self.ampaxis = pg.AxisItem(orientation='left')
        self.w_ampl.addItem(self.ampaxis,row=0,col=0)
        self.ampaxis.linkToView(self.p_ampl)

        self.w_spec = pg.GraphicsLayoutWidget()
        self.p_spec = SupportClasses.DragViewBox(enableMouse=False,enableMenu=False)
        self.w_spec.addItem(self.p_spec,row=0,col=1)
        self.w_spec.addItem(self.timeaxis,row=1,col=1)

        #self.plot_spec = pg.PlotItem(enableMouse=False,enableMenu=False)
        #self.w_spec.addItem(self.plot_spec,row=0,col=1)
        #self.annot_spec = pg.ScatterPlotItem(size=10,pen=pg.mkPen(None), brush=pg.mkBrush(255, 0, 0, 255),enableMouse=False,enableMenu=False)
        #self.annot_spec.addPoints([0,0.1,20,30],[0,0.1,20,30])
        #self.plot_spec.addItem(self.annot_spec)
        self.d_spec.addWidget(self.w_spec)
        #proxy = pg.SignalProxy(self.p_spec.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.p_spec.scene().sigMouseMoved.connect(self.mouseMoved)

        self.pointData = pg.TextItem(color=(255,0,0),anchor=(0,0))
        self.p_spec.addItem(self.pointData)

        self.specaxis = pg.AxisItem(orientation='left')
        self.w_spec.addItem(self.specaxis,row=0,col=0)
        self.specaxis.linkToView(self.p_spec)

        self.overviewImage = pg.ImageItem(enableMouse=False)
        self.p_overview.addItem(self.overviewImage)

        #self.amplPlot = pg.PlotItem()
        self.amplPlot = pg.PlotDataItem()

        self.p_ampl.addItem(self.amplPlot)

        self.specPlot = pg.ImageItem()
        self.p_spec.addItem(self.specPlot)
        self.specPlot2 = pg.PlotDataItem()
        self.p_spec.addItem(self.specPlot2)

        # Connect up the listeners
        #self.p_overview.scene().sigMouseClicked.connect(self.mouseClicked_overview)
        self.p_ampl.scene().sigMouseClicked.connect(self.mouseClicked_ampl)
        self.p_spec.scene().sigMouseClicked.connect(self.mouseClicked_spec)
        self.p_spec.sigMouseDragged.connect(self.mouseDragged_spec)

        self.w_controls = pg.LayoutWidget()
        self.d_controls.addWidget(self.w_controls)

        self.w_files = pg.LayoutWidget()
        self.d_files.addWidget(self.w_files)

        #self.w_buttons = pg.LayoutWidget()
        #self.d_buttons.addWidget(self.w_buttons)

        # # The buttons to move through the overview
        self.leftBtn = QToolButton()
        self.leftBtn.setArrowType(Qt.LeftArrow)
        self.connect(self.leftBtn, SIGNAL('clicked()'), self.moveLeft)
        self.w_overview.addWidget(self.leftBtn)
        self.rightBtn = QToolButton()
        self.rightBtn.setArrowType(Qt.RightArrow)
        self.connect(self.rightBtn, SIGNAL('clicked()'), self.moveRight)
        self.w_overview.addWidget(self.rightBtn)

        # The instructions and buttons below figMain
        # playButton = QPushButton(QIcon(":/Resources/play.svg"),"&Play Window")

        self.playButton = QtGui.QToolButton()
        self.playButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
        #self.playButton = QPushButton("&Play")
        self.connect(self.playButton, SIGNAL('clicked()'), self.playSegment)
        self.timePlayed = QLabel()
        #self.resetButton = QPushButton("&Reset")
        #self.connect(self.resetButton, SIGNAL('clicked()'), self.resetSegment)

        self.playSegButton = QtGui.QToolButton()
        self.playSegButton.setIcon(QtGui.QIcon('img/playsegment.png'))
        self.playSegButton.setIconSize(QtCore.QSize(20, 20))
        self.connect(self.playSegButton, SIGNAL('clicked()'), self.playSelectedSegment)
        self.playSegButton.setEnabled(False)

        self.playBandLimitedSegButton = QtGui.QToolButton()
        self.playBandLimitedSegButton.setIcon(QtGui.QIcon('img/playsegment.png'))
        self.playBandLimitedSegButton.setIconSize(QtCore.QSize(20, 20))
        self.connect(self.playBandLimitedSegButton, SIGNAL('clicked()'), self.playBandLimitedSegment)
        self.playBandLimitedSegButton.setEnabled(False)

        # Checkbox for whether or not user is drawing boxes around song in the spectrogram (defaults to clicks not drags)
        #self.dragRectangles = QCheckBox('Drag boxes in spectrogram')
        #self.dragRectangles.stateChanged[int].connect(self.dragRectanglesCheck)
        #self.useAmplitudeTick = QCheckBox('Show amplitude plot')
        #self.useAmplitudeTick.stateChanged[int].connect(self.useAmplitudeCheck)
        #self.useAmplitudeTick.setChecked(True)
        #self.showFundamental = QCheckBox('Show fundamental frequency')
        #self.showFundamental.stateChanged[int].connect(self.showFundamentalFreq)
        #self.showFundamental.setChecked(False)

        # A slider to show playback position
        # This is hidden, but controls the moving bar
        self.playSlider = QSlider(Qt.Horizontal)
        self.connect(self.playSlider,SIGNAL('sliderReleased()'),self.sliderMoved)
        self.playSlider.setVisible(False)
        self.d_spec.addWidget(self.playSlider)
        #self.w_controls.addWidget(self.playSlider,row=1,col=0,colspan=4)

        # A slider to move through the file easily
        # TODO: Why doesn't this have the forward/backward arrows?
        # TODO: And can I line it up with the spectrogram?
        self.scrollSlider = QScrollBar(Qt.Horizontal)
        #self.scrollSlider = QScrollBar()
        self.scrollSlider.valueChanged.connect(self.scroll)
        self.d_spec.addWidget(self.scrollSlider)
        #self.w_spec.addItem(self.scrollSlider,row=2,col=1)
        #self.w_spec.setHorizontalScrollBar(self.scrollSlider)
        #self.w_spec.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)


        #self.w_controls.addWidget(self.resetButton,row=2,col=1)
        #self.w_controls.addWidget(self.dragRectangles,row=0,col=3)
        #self.w_controls.addWidget(self.useAmplitudeTick,row=1,col=3)
        #self.w_controls.addWidget(self.showFundamental,row=0,col=4)

        # The spinbox for changing the width shown in figMain
        self.widthWindow = QDoubleSpinBox()
        self.widthWindow.setSingleStep(1.0)
        self.widthWindow.setDecimals(2)
        self.widthWindow.setValue(self.config['windowWidth'])
        self.widthWindow.valueChanged[float].connect(self.changeWidth)

        # Brightness, contrast and colour reverse options
        self.brightnessSlider = QSlider(Qt.Horizontal)
        self.brightnessSlider.setMinimum(0)
        self.brightnessSlider.setMaximum(100)
        self.brightnessSlider.setValue(self.config['brightness'])
        self.brightnessSlider.setTickInterval(1)
        self.brightnessSlider.valueChanged.connect(self.setColourLevels)

        self.contrastSlider = QSlider(Qt.Horizontal)
        self.contrastSlider.setMinimum(0)
        self.contrastSlider.setMaximum(100)
        self.contrastSlider.setValue(self.config['contrast'])
        self.contrastSlider.setTickInterval(1)
        self.contrastSlider.valueChanged.connect(self.setColourLevels)

        deleteButton = QPushButton("&Delete Current Segment")
        self.connect(deleteButton, SIGNAL('clicked()'), self.deleteSegment)
        #self.swapBW = QCheckBox()
        #self.swapBW.setChecked(self.config['coloursInverted'])
        #self.swapBW.stateChanged.connect(self.colourChange)
        #self.swapBW.stateChanged.connect(self.swappedBW)

        #self.w_controls.addWidget(QLabel("Swap B/W"),row=2,col=0)
        #self.w_controls.addWidget(self.swapBW,row=3,col=0)
        #self.w_controls.addWidget(QLabel('Slide top box to move through recording, click to start and end a segment, click on segment to edit or label. Right click to interleave.'),row=0,col=0,colspan=6)
        self.w_controls.addWidget(self.playButton,row=0,col=0)
        self.w_controls.addWidget(self.playSegButton,row=0,col=1)
        self.w_controls.addWidget(self.playBandLimitedSegButton,row=0,col=2)
        self.w_controls.addWidget(self.timePlayed,row=1,col=0)
        self.w_controls.addWidget(QLabel("Brightness"),row=2,col=0,colspan=3)
        self.w_controls.addWidget(self.brightnessSlider,row=3,col=0,colspan=3)
        self.w_controls.addWidget(QLabel("Contrast"),row=4,col=0,colspan=3)
        self.w_controls.addWidget(self.contrastSlider,row=5,col=0,colspan=3)
        self.w_controls.addWidget(deleteButton,row=6,col=0)
        self.w_controls.addWidget(QLabel('Visible window width (seconds)'),row=7,col=0,colspan=2)
        self.w_controls.addWidget(self.widthWindow,row=8,col=0,colspan=2)#,colspan=2)


        # List to hold the list of files
        self.listFiles = QListWidget(self)
        self.listFiles.setFixedWidth(150)
        self.fillFileList()
        self.listFiles.connect(self.listFiles, SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self.listLoadFile)

        self.w_files.addWidget(QLabel('Double click to select'),row=0,col=0)
        self.w_files.addWidget(QLabel('Red names have segments'),row=1,col=0)
        self.w_files.addWidget(self.listFiles,row=2,col=0)

        # These are the main buttons, on the bottom right
        #quitButton = QPushButton("&Quit")
        #self.connect(quitButton, SIGNAL('clicked()'), self.quit)
        #spectrogramButton = QPushButton("Spectrogram &Params")
        #self.connect(spectrogramButton, SIGNAL('clicked()'), self.showSpectrogramDialog)
        #segmentButton = QPushButton("&Segment")
        #self.connect(segmentButton, SIGNAL('clicked()'), self.segmentationDialog)
        #denoiseButton = QPushButton("&Denoise")
        #self.connect(denoiseButton, SIGNAL('clicked()'), self.denoiseDialog)
        #recogniseButton = QPushButton("&Recognise")
        #self.connect(recogniseButton, SIGNAL('clicked()'), self.recognise)
        #deleteAllButton = QPushButton("&Delete All Segments")
        #self.connect(deleteAllButton, SIGNAL('clicked()'), self.deleteAll)
        #findMatchButton = QPushButton("&Find Matches")
        #self.connect(findMatchButton, SIGNAL('clicked()'), self.findMatches)
        #checkButton1 = QPushButton("&Check Segments 1")
        #self.connect(checkButton1, SIGNAL('clicked()'), self.humanClassifyDialog1)
        #checkButton2 = QPushButton("&Check Segments 2")
        #self.connect(checkButton2, SIGNAL('clicked()'), self.humanClassifyDialog2)
        #dockButton = QPushButton("&Put Docks Back")
        #self.connect(dockButton, SIGNAL('clicked()'), self.dockReplace)
        #loadButton = QPushButton("&Load File")
        #self.connect(loadButton, SIGNAL('clicked()'), self.openFile)
        #playSegButton = QPushButton("&Play Segment")
        #self.connect(playSegButton, SIGNAL('clicked()'), self.playSelectedSegment)

        #self.w_buttons.addWidget(loadButton,row=0,col=0)
        #self.w_buttons.addWidget(deleteAllButton,row=0,col=4)
        #self.w_buttons.addWidget(denoiseButton,row=0,col=2)
        #self.w_buttons.addWidget(spectrogramButton,row=0,col=3)
        #self.w_buttons.addWidget(checkButton1,row=1,col=4)
        #self.w_buttons.addWidget(checkButton2,row=1,col=5)

        #self.w_buttons.addWidget(segmentButton,row=1,col=0)
        #self.w_buttons.addWidget(findMatchButton,row=1,col=1)
        #self.w_buttons.addWidget(dockButton,row=1,col=2)
        #self.w_buttons.addWidget(quitButton,row=1,col=3)
        #for w in [deleteButton, deleteAllButton, spectrogramButton, segmentButton, findMatchButton,
        #              checkButton1, checkButton2, dockButton, quitButton]:

        # The context menu (drops down on mouse click) to select birds
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.menuBirdList = QMenu()
        self.menuBird2 = self.menuBirdList.addMenu('Other')
        self.fillBirdList()

        # # An array of radio buttons and a list and a text entry box
        # # Create an array of radio buttons for the most common birds (2 columns of 10 choices)
        # # self.birds1 = []
        # # for item in self.config['BirdButtons1']:
        # #     self.birds1.append(QRadioButton(item))
        # # self.birds2 = []
        # # for item in self.config['BirdButtons2']:
        # #     self.birds2.append(QRadioButton(item))
        # #
        # # for i in xrange(len(self.birds1)):
        # #     self.birds1[i].setEnabled(False)
        # #     self.connect(self.birds1[i], SIGNAL("clicked()"), self.radioBirdsClicked)
        # # for i in xrange(len(self.birds2)):
        # #     self.birds2[i].setEnabled(False)
        # #     self.connect(self.birds2[i], SIGNAL("clicked()"), self.radioBirdsClicked)
        #
        # # The list of less common birds
        # # self.birdList = QListWidget(self)
        # # self.birdList.setMaximumWidth(150)
        # # for item in self.config['ListBirdsEntries']:
        # #     self.birdList.addItem(item)
        # # self.birdList.sortItems()
        # # # Explicitly add "Other" option in
        # # self.birdList.insertItem(0,'Other')
        #
        # # self.connect(self.birdList, SIGNAL("itemClicked(QListWidgetItem*)"), self.listBirdsClicked)
        # # self.birdList.setEnabled(False)
        #
        # # This is the text box for missing birds
        # # self.tbox = QLineEdit(self)
        # # self.tbox.setMaximumWidth(150)
        # # self.connect(self.tbox, SIGNAL('editingFinished()'), self.birdTextEntered)
        # # self.tbox.setEnabled(False)
        #
        # # birds1Layout = QVBoxLayout()
        # # for i in xrange(len(self.birds1)):
        # #     birds1Layout.addWidget(self.birds1[i])
        # #
        # # birds2Layout = QVBoxLayout()
        # # for i in xrange(len(self.birds2)):
        # #     birds2Layout.addWidget(self.birds2[i])
        # #
        # # birdListLayout = QVBoxLayout()
        # # birdListLayout.addWidget(self.birdList)
        # # birdListLayout.addWidget(QLabel("If bird isn't in list, select Other"))
        # # birdListLayout.addWidget(QLabel("Type below, Return at end"))
        # # birdListLayout.addWidget(self.tbox)

        # Instantiate a Qt media object and prepare it (for audio playback)
        self.media_obj = phonon.Phonon.MediaObject(self)
        self.audio_output = phonon.Phonon.AudioOutput(phonon.Phonon.MusicCategory, self)
        phonon.Phonon.createPath(self.media_obj, self.audio_output)
        self.media_obj.setTickInterval(20)
        #self.media_obj.tick.connect(self.movePlaySlider)
        self.media_obj.finished.connect(self.playFinished)
        # TODO: Check the next line out!
        #self.media_obj.totalTimeChanged.connect(self.setSliderLimits)

        # Make the colours
        self.ColourSelected = QtGui.QBrush(QtGui.QColor(self.config['ColourSelected'][0], self.config['ColourSelected'][1], self.config['ColourSelected'][2], self.config['ColourSelected'][3]))
        self.ColourNamed = QtGui.QBrush(QtGui.QColor(self.config['ColourNamed'][0], self.config['ColourNamed'][1], self.config['ColourNamed'][2], self.config['ColourNamed'][3]))
        self.ColourNone = QtGui.QBrush(QtGui.QColor(self.config['ColourNone'][0], self.config['ColourNone'][1], self.config['ColourNone'][2], self.config['ColourNone'][3]))
        self.ColourPossible = QtGui.QBrush(QtGui.QColor(self.config['ColourPossible'][0], self.config['ColourPossible'][1], self.config['ColourPossible'][2], self.config['ColourPossible'][3]))

        # Hack to get the type of an ROI
        p_spec_r = SupportClasses.ShadedRectROI(0, 0)
        self.ROItype = type(p_spec_r)

        # Listener for key presses
        self.connect(self.p_spec, SIGNAL("keyPressed"),self.handleKey)
        # Store the state of the docks
        self.state = self.area.saveState()

        # Plot everything
        self.show()

    def handleKey(self,ev):
        if ev.key() == Qt.Key_Backspace:
            self.deleteSegment()

    def fillBirdList(self,unsure=False):
        self.menuBirdList.clear()
        self.menuBird2.clear()
        for item in self.config['BirdList'][:20]:
            if unsure and item != "Don't Know":
                item = item+'?'
            bird = self.menuBirdList.addAction(item)
            #birdp = self.menuBirdList.addMenu(item)
            #birdp.addAction('Possible '+item)
            receiver = lambda birdname=item: self.birdSelected(birdname)
            self.connect(bird, SIGNAL("triggered()"), receiver)
            self.menuBirdList.addAction(bird)
        self.menuBird2 = self.menuBirdList.addMenu('Other')
        for item in self.config['BirdList'][20:]+['Other']:
            if unsure and item != "Don't Know" and item != "Other":
                item = item+'?'
            bird = self.menuBird2.addAction(item)
            receiver = lambda birdname=item: self.birdSelected(birdname)
            self.connect(bird, SIGNAL("triggered()"), receiver)
            self.menuBird2.addAction(bird)

    def fillFileList(self):
        # Generates the list of files for the listbox on lower left
        # Most of the work is to deal with directories in that list
        if not os.path.isdir(self.dirName):
            print("Directory doesn't exist: making it")
            os.makedirs(self.dirName)
        self.listOfFiles = QDir(self.dirName).entryInfoList(['..','*.wav'],filters=QDir.AllDirs|QDir.NoDot|QDir.Files,sort=QDir.DirsFirst)
        listOfDataFiles = QDir(self.dirName).entryList(['*.data'])
        listOfLongFiles = QDir(self.dirName).entryList(['*_1.wav'])
        for file in self.listOfFiles:
            if file.fileName()[:-4]+'_1.wav' in listOfLongFiles:
                # Ignore this entry
                pass
            else:
                # If there is a .data version, colour the name red to show it has been labelled
                item = QListWidgetItem(self.listFiles)
                item.setText(file.fileName())
                if file.fileName()+'.data' in listOfDataFiles:
                    item.setTextColor(Qt.red)
        index = self.listFiles.findItems(self.firstFile,Qt.MatchExactly)
        if len(index)>0:
            self.listFiles.setCurrentItem(index[0])
        else:
            index = self.listFiles.findItems(self.listOfFiles[0].fileName(),Qt.MatchExactly)
            self.listFiles.setCurrentItem(index[0])

    def resetStorageArrays(self):
        # These variables hold the data to be saved and/or plotted
        # Used when new files are loaded

        # Remove the segments
        self.removeSegments()
        if hasattr(self, 'overviewImageRegion'):
            self.p_overview.removeItem(self.overviewImageRegion)

        # This is a flag to say if the next thing that they click on should be a start or a stop for segmentation
        self.started = False

        # Keep track of start points and selected buttons
        #self.start_a = 0
        self.windowStart = 0
        self.playPosition = self.windowStart
        self.prevBoxCol = self.config['ColourNone']
        #self.line = None

        # Remove the overview segments
        for r in self.SegmentRects:
            self.p_overview2.removeItem(r)
        self.SegmentRects = []

        #self.recta1 = None
        #self.recta2 = None
        #self.focusRegionSelected = False
        #self.figMainSegment1 = None
        #self.figMainSegment2 = None
        #self.figMainSegmenting = False

        #self.playbar1 = None
        #self.isPlaying = False

    def openFile(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'Choose File', self.dirName,"Wav files (*.wav)")

        # Find the '/' in the fileName
        i=len(fileName)-1
        while fileName[i] != '/' and i>0:
            i = i-1
        self.dirName = fileName[:i+1]
        if self.previousFile is not None:
            if self.segments != [] or self.hasSegments:
                self.saveSegments()
        # TODO: Should check if the file is in the list in the Files box and then actually store it for colouring
        # Also find current and highlight it
        self.previousFile = None
        self.resetStorageArrays()
        self.showFundamental.setChecked(False)
        self.showInvSpec.setChecked(False)
        self.loadFile(fileName)

    def listLoadFile(self,current):
        # Listener for when the user clicks on a filename
        # Saves segments of current file, resets flags and calls loader
        #self.p_ampl.clear()
        if self.previousFile is not None:
            if self.segments != [] or self.hasSegments:
                self.saveSegments()
                self.previousFile.setTextColor(Qt.red)
        self.previousFile = current
        self.resetStorageArrays()

        i=0
        while self.listOfFiles[i].fileName() != current.text():
            i+=1
        # Slightly dangerous, but the file REALLY should exist
        if self.listOfFiles[i].isDir():
            dir = QDir(self.dirName)
            dir.cd(self.listOfFiles[i].fileName())
            # Now repopulate the listbox
            #print "Now in "+self.listOfFiles[i].fileName()
            self.dirName=str(dir.absolutePath())
            self.listFiles.clearSelection()
            self.listFiles.clearFocus()
            self.listFiles.clear()
            self.previousFile = None
            self.fillFileList()
        else:
            self.loadFile(current)

    def loadFile(self,name):
        # This does the work of loading a file
        # One magic constant, which normalises the data
        # TODO: Note that if load normalised the data, this buggers up the spectrogram for e.g., Harma

        # Create a modal dialog to get the name of the user and show some file info
        # TODO: do something with the stuff below
        # TODO: at least: add username to metadata for segments
        #name = 'xxx'
        #date = 'xy'
        #time = '12:00'
        #fdd = FileDataDialog(name,date,time)
        #fdd.exec_()
        #username = fdd.getData()

        print type(name)
        if isinstance(name,str):
            self.filename = self.dirName+'/'+name
        elif isinstance(name,QString):
            self.filename = str(name)
        else:
            self.filename = str(self.dirName+'/'+name.text())
        print self.filename, type(self.filename)
        #self.audiodata, self.sampleRate = lr.load(self.filename,sr=None)
        #self.sampleRate, self.audiodata = wavfile.read(self.filename)
        wavobj = wavio.read(self.filename)
        self.sampleRate = wavobj.rate
        self.audiodata = wavobj.data
        self.minFreq = 0
        self.maxFreq = self.sampleRate/2.
        # None of the following should be necessary for librosa
        if self.audiodata.dtype is not 'float':
            self.audiodata = self.audiodata.astype('float') #/ 32768.0
        if np.shape(np.shape(self.audiodata))[0]>1:
            self.audiodata = self.audiodata[:,0]
        self.datalength = np.shape(self.audiodata)[0]
        self.setWindowTitle('AviaNZ - ' + self.filename)
        print("Length of file is ",len(self.audiodata),float(self.datalength)/self.sampleRate)

        # Create an instance of the Signal Processing class
        if not hasattr(self,'sp'):
            self.sp = SignalProc.SignalProc(self.audiodata, self.sampleRate,self.config['window_width'],self.config['incr'])

        # Get the data for the spectrogram
        self.sgRaw = self.sp.spectrogram(self.audiodata,self.sampleRate,mean_normalise=True,onesided=True,multitaper=False)
        maxsg = np.min(self.sgRaw)
        self.sg = np.abs(np.where(self.sgRaw==0,0.0,10.0 * np.log10(self.sgRaw/maxsg)))

        # Load any previous segments stored
        if os.path.isfile(self.filename+'.data'):
            file = open(self.filename+'.data', 'r')
            self.segments = json.load(file)
            file.close()
            self.hasSegments = True
        else:
            self.hasSegments = False

        # Update the data that is seen by the other classes
        # TODO: keep an eye on this to add other classes as required
        if hasattr(self,'seg'):
            self.seg.setNewData(self.audiodata,self.sgRaw,self.sampleRate,self.config['window_width'],self.config['incr'])
        self.sp.setNewData(self.audiodata,self.sampleRate)

        # Delete any denoising backups from the previous one
        if hasattr(self,'audiodata_backup'):
            self.audiodata_backup = None

        # Set the values for the segmentation thresholds
        # self.ampThr.setRange(0.001,np.max(self.audiodata)+0.001)
        # self.ampThr.setSingleStep(0.001)
        # self.ampThr.setDecimals(4)
        # self.ampThr.setValue(np.max(self.audiodata)+0.001)

        # Set the window size
        self.windowSize = self.config['windowWidth']
        self.widthWindow.setRange(0.5, float(len(self.audiodata))/self.sampleRate)

        # Reset it if the file is shorter than the window
        if float(len(self.audiodata))/self.sampleRate < self.windowSize:
            self.windowSize = float(len(self.audiodata))/self.sampleRate
        self.widthWindow.setValue(self.windowSize)

        # Load the file for playback as well, and connect up the listeners for it
        self.media_obj.setCurrentSource(phonon.Phonon.MediaSource(self.filename))
        self.totalTime = self.convertMillisecs(self.media_obj.totalTime())
        print self.media_obj.totalTime(), self.totalTime
        self.media_obj.tick.connect(self.movePlaySlider)

        # Set the length of the scrollbar
        print np.shape(self.sg)
        self.scrollSlider.setRange(0,np.shape(self.sg)[0]-self.convertAmpltoSpec(self.widthWindow.value()))
        self.scrollSlider.setValue(0)

        # Get the height of the amplitude for plotting the box
        self.minampl = np.min(self.audiodata)+0.1*(np.max(self.audiodata)+np.abs(np.min(self.audiodata)))
        #self.plotheight = np.abs(self.minampl) + np.max(self.audiodata)
        self.drawOverview()
        self.drawfigMain()

    # def openFile(self):
    #     # If have an open file option this will deal with it via a file dialog
    #     # Currently unused
    #     Formats = "Wav file (*.wav)"
    #     filename = QFileDialog.getOpenFileName(self, 'Open File', '/Users/srmarsla/Projects/AviaNZ', Formats)
    #     if filename != None:
    #         self.loadFile(filename)

    def dragRectanglesCheck(self):
        # The checkbox that says if the user is dragging rectangles or clicking on the spectrogram has changed state
        if self.dragRectangles.isChecked():
            #print "Checked"
            self.p_spec.setMouseMode(pg.ViewBox.RectMode)
        else:
            #print "Unchecked"
            self.p_spec.setMouseMode(pg.ViewBox.PanMode)

    def useAmplitudeCheck(self):
        # Note that this doesn't remove the dock, just hide it. So it's all still live and easy to replace :)
        # Also move all the labels
        if self.useAmplitudeTick.isChecked():
            #if hasattr(self,'useAmplitude'):
            #    self.w_spec.removeItem(self.timeaxis)
            self.useAmplitude = True
            #self.w_spec.addItem(self.timeaxis, row=1, col=1)
            #self.timeaxis.linkToView(self.p_ampl)
            #for r in self.listLabels:
                #self.p_spec.removeItem(r)
                #self.p_ampl.addItem(r)
                #r.setPos(self.convertSpectoAmpl(r.x()),self.minampl)
            self.d_ampl.show()
        else:
            self.useAmplitude = False
            #self.w_ampl.removeItem(self.timeaxis)
            #self.w_spec.addItem(self.timeaxis, row=1, col=1)
            #for r in self.listLabels:
                #self.p_ampl.removeItem(r)
                #self.p_spec.addItem(r)
                #r.setPos(self.textpos)
            self.d_ampl.hide()

    def useFilesCheck(self):
        if self.useFilesTick.isChecked():
            self.d_files.show()
        else:
            self.d_files.hide()

    def showOverviewSegsCheck(self):
        if self.showOverviewSegsTick.isChecked():
            self.p_overview2.show()
        else:
            self.p_overview2.hide()


    def showFundamentalFreq(self):
        # Draw the fundamental frequency
        if self.showFundamental.isChecked():
            if not hasattr(self,'seg'):
                self.seg = Segment.Segment(self.audiodata,self.sgRaw,self.sp,self.sampleRate,self.config['minSegment'],self.config['window_width'],self.config['incr'])
            pitch, y, minfreq, W = self.seg.yin()
            ind = np.squeeze(np.where(pitch>minfreq))
            pitch = pitch[ind]
            ind = ind*W/(self.config['window_width']/2.)
            x = (pitch*2./self.sampleRate*np.shape(self.sg)[1]).astype('int')

            # Get the individual pieces
            # TODO: FINISH!
            print ind
            segs = self.seg.identifySegments(ind,maxgap=10,minlength=5)
            for s in segs:
                s[0] = s[0] * self.sampleRate / float(self.config['incr'])
                s[1] = s[1] * self.sampleRate / float(self.config['incr'])
                i = np.where((ind>s[0]) & (ind<s[1]))
                print s, i
                self.specPlot2.setData(ind[i],x[i],pen=pg.mkPen('r', width=3))

            self.yinRois = []
            for r in range(len(x)):
                self.yinRois.append(pg.CircleROI([ind[r],x[r]], [2,2], pen=(4, 9),movable=False))
            for r in self.yinRois:
                self.p_spec.addItem(r)

            # TODO: Fit a spline and draw it
            #from scipy.interpolate import interp1d
            #f = interp1d(x, ind, kind='cubic')
            #self.sg[ind,x] = 1
        else:
            for r in self.yinRois:
                self.p_spec.removeItem(r)
        #self.specPlot.setImage(self.sg)

    def showFundamentalFreq2(self):
        # yaapt
        import pYAAPT
        import basic_tools
        # Actually this is a pain, since it either gives back a value for each amplitude sample, or for it's own weird windows
        if self.showFundamental2.isChecked():
            y = basic_tools.SignalObj(self.filename)
            x = pYAAPT.yaapt(y)
            self.yinRois = []
            for r in range(len(x)):
                self.yinRois.append(pg.CircleROI([ind[r],x[r]], [2,2], pen=(4, 9),movable=False))
            for r in self.yinRois:
                self.p_spec.addItem(r)
        else:
            for r in self.yinRois:
                self.p_spec.removeItem(r)

    def showFundamentalFreq3(self):
        # Harvest
        import audio_tools
        if self.showFundamental2.isChecked():
            p, f, t, fa = audio_tools.harvest(self.audiodata,self.sampleRate)
            ind = f/self.config['window_width']
            x = (p*2./self.sampleRate*np.shape(self.sg)[1]).astype('int')
            print ind, x
            self.yinRois = []
            for r in range(len(x)):
                self.yinRois.append(pg.CircleROI([ind[r],x[r]], [2,2], pen=(4, 9),movable=False))
            for r in self.yinRois:
                self.p_spec.addItem(r)
        else:
            for r in self.yinRois:
                self.p_spec.removeItem(r)

    def showInvertedSpectrogram(self):
        if self.showInvSpec.isChecked():
            self.sgRaw = self.sp.show_invS()
        else:
            self.sgRaw = self.sp.spectrogram(self.audiodata, self.sampleRate, mean_normalise=True, onesided=True,
                                         multitaper=False)
        maxsg = np.min(self.sgRaw)
        self.sg = np.abs(np.where(self.sgRaw == 0, 0.0, 10.0 * np.log10(self.sgRaw / maxsg)))
        self.overviewImage.setImage(self.sg)
        self.specPlot.setImage(self.sg)

    def medianFilterSpec(self):
        from scipy.ndimage.filters import median_filter
        median_filter(self.sg,size=(100,20))
        self.specPlot.setImage(self.sg)

    def denoiseImage(self):
        from cv2 import fastNlMeansDenoising
        sg = np.array(self.sg/np.max(self.sg)*255,dtype = np.uint8)
        sg = fastNlMeansDenoising(sg,10,7,21)
        self.specPlot.setImage(sg)
# ==============
# Code for drawing and using the main figure

    def convertAmpltoSpec(self,x):
        return x*self.sampleRate/self.config['incr']

    def convertSpectoAmpl(self,x):
        return x*self.config['incr']/self.sampleRate

    def convertMillisecs(self,millisecs):
        seconds = (millisecs / 1000) % 60
        minutes = (millisecs / (1000 * 60)) % 60
        return "%02d" % minutes+":"+"%02d" % seconds

    def drawOverview(self):
        # On loading a new file, update the overview figure to show where you are up to in the file
        self.overviewImage.setImage(self.sg)
        self.overviewImageRegion = pg.LinearRegionItem()
        self.p_overview.addItem(self.overviewImageRegion, ignoreBounds=True)
        self.overviewImageRegion.setRegion([0, self.convertAmpltoSpec(self.widthWindow.value())])
        self.overviewImageRegion.sigRegionChanged.connect(self.updateOverview)
        #self.overviewImageRegion.sigRegionChangeFinished.connect(self.updateOverview)

        # Three y values are No. not known, No. known, No. possible
        # widthOverviewSegment is in seconds
        numSegments = int(np.ceil(np.shape(self.sg)[0]/self.convertAmpltoSpec(self.config['widthOverviewSegment'])))
        self.widthOverviewSegment = int(np.shape(self.sg)[0]/numSegments)
        self.overviewSegments = np.zeros((numSegments,3))
        for i in range(numSegments):
            r = pg.QtGui.QGraphicsRectItem(i*self.widthOverviewSegment, 0, (i+1)*self.widthOverviewSegment, 0.5)
            r.setPen(pg.mkPen('k'))
            #r.setPen(pg.mkPen(None))
            r.setBrush(pg.mkBrush('w'))
            self.SegmentRects.append(r)
            self.p_overview2.addItem(r)

    def updateOverview(self):
        # Listener for when the overview box is changed
        # Does the work of keeping all the plots in the right range
        # TODO: Why does this update the other plots so slowly?
        minX, maxX = self.overviewImageRegion.getRegion()
        #print "updating overview", minX, maxX, self.convertSpectoAmpl(maxX)
        self.widthWindow.setValue(self.convertSpectoAmpl(maxX-minX))
        self.p_ampl.setXRange(self.convertSpectoAmpl(minX), self.convertSpectoAmpl(maxX), padding=0)
        self.p_spec.setXRange(minX, maxX, padding=0)
        self.p_ampl.setXRange(self.convertSpectoAmpl(minX), self.convertSpectoAmpl(maxX), padding=0)
        self.p_spec.setXRange(minX, maxX, padding=0)
        #print "Slider:", self.convertSpectoAmpl(minX),self.convertSpectoAmpl(maxX)
        self.setSliderLimits(1000.0*self.convertSpectoAmpl(minX),1000.0*self.convertSpectoAmpl(maxX))
        self.scrollSlider.setValue(minX)
        self.pointData.setPos(minX,0)
        pg.QtGui.QApplication.processEvents()

    def drawfigMain(self):
        # This draws the main amplitude and spectrogram plots

        self.amplPlot.setData(np.linspace(0.0,float(self.datalength)/self.sampleRate,num=self.datalength,endpoint=True),self.audiodata)

        self.specPlot.setImage(self.sg)
        self.setColourMap(self.config['cmap'])

        # The constants here are divided by 1000 to get kHz, and then remember the top is sampleRate/2
        FreqRange = (self.maxFreq-self.minFreq)/1000.
        height = self.sampleRate/2./np.shape(self.sg)[1]
        self.specaxis.setTicks([[(0,self.minFreq/1000.),(np.shape(self.sg)[1]/4,self.minFreq/1000.+FreqRange/4.),(np.shape(self.sg)[1]/2,self.minFreq/1000.+FreqRange/2.),(3*np.shape(self.sg)[1]/4,self.minFreq/1000.+3*FreqRange/4.),(np.shape(self.sg)[1],self.minFreq/1000.+FreqRange)]])
        self.specaxis.setLabel('kHz')
        self.updateOverview()

        self.setColourLevels()
        self.textpos = np.shape(self.sg)[1] + self.config['textoffset']

        # If there are segments, show them
        for count in range(len(self.segments)):
            self.addSegment(self.segments[count][0], self.segments[count][1],self.segments[count][2],self.segments[count][3],self.segments[count][4],False)

        # This is the moving bar for the playback
        if not hasattr(self,'bar'):
            self.bar = pg.InfiniteLine(angle=90, movable=True, pen={'color': 'c', 'width': 3})
        self.p_spec.addItem(self.bar, ignoreBounds=True)
        self.bar.sigPositionChangeFinished.connect(self.barMoved)

    def updateRegion_spec(self):
        # This is the listener for when a segment box is changed
        # It updates the position of the matching box, and also the text within it
        sender = self.sender()
        i = 0
        while self.listRectanglesa2[i] != sender and i<len(self.listRectanglesa2):
            i = i+1
        if i>len(self.listRectanglesa2):
            print "segment not found!"
        else:
            if type(sender) == self.ROItype:
                x1 = self.convertSpectoAmpl(sender.pos()[0])
                x2 = self.convertSpectoAmpl(sender.pos()[0]+sender.size()[0])
            else:
                x1 = self.convertSpectoAmpl(sender.getRegion()[0])
                x2 = self.convertSpectoAmpl(sender.getRegion()[1])
            self.listRectanglesa1[i].setRegion([x1,x2])
            self.listLabels[i].setPos(sender.getRegion()[0],self.textpos)

            self.segments[i][0] = x1
            self.segments[i][1] = x2

    def updateRegion_ampl(self):
        # This is the listener for when a segment box is changed
        # It updates the position of the matching box, and also the text within it
        sender = self.sender()
        i = 0
        while self.listRectanglesa1[i] != sender and i<len(self.listRectanglesa1):
            i = i+1
        if i>len(self.listRectanglesa1):
            print "segment not found!"
        else:
            x1 = self.convertAmpltoSpec(sender.getRegion()[0])
            x2 = self.convertAmpltoSpec(sender.getRegion()[1])

            if type(self.listRectanglesa2[i]) == self.ROItype:
                y1 = self.listRectanglesa2[i].pos().y()
                y2 = self.listRectanglesa2[i].size().y()
                self.listRectanglesa2[i].setPos(pg.Point(x1,y1))
                self.listRectanglesa2[i].setSize(pg.Point(x2-x1,y2))
            else:
                self.listRectanglesa2[i].setRegion([x1,x2])
            #self.listLabels[i].setPos(sender.getRegion()[0],self.minampl)
            self.listLabels[i].setPos(x1,self.textpos)

            self.segments[i][0] = sender.getRegion()[0]
            self.segments[i][1] = sender.getRegion()[1]

    # def mouseClicked_overview(self,evt):
    #     pos = evt.pos()
    #     if self.p_overview.sceneBoundingRect().contains(pos):
    #         mousePoint = self.p_overview.mapSceneToView(pos)

    def addSegment(self,startpoint,endpoint,y1=0,y2=0,species=None,saveSeg=True):
        # Create a new segment and all the associated stuff
        # x, y in amplitude coordinates
        #print "Adding segment", self.overviewSegments
        wasNone = False
        # Get the name and colour sorted
        if species is None:
            species = "Don't Know"

        if species != "Don't Know":
            # Work out which overview segment this segment is in (could be more than one)
            inds = int(float(self.convertAmpltoSpec(startpoint))/self.widthOverviewSegment)
            inde = int(float(self.convertAmpltoSpec(endpoint))/self.widthOverviewSegment)
            if species[-1] == '?':
                brush = self.ColourPossible
                self.overviewSegments[inds:inde + 1, 2] += 1
            else:
                brush = self.ColourNamed
                self.overviewSegments[inds:inde + 1, 1] += 1
            self.prevBoxCol = brush

            for box in range(inds, inde + 1):
                if self.overviewSegments[box,0] > 0:
                    self.SegmentRects[box].setBrush(self.ColourNone)
                elif self.overviewSegments[box,2] > 0:
                    self.SegmentRects[box].setBrush(self.ColourPossible)
                elif self.overviewSegments[box,1] > 0:
                    self.SegmentRects[box].setBrush(self.ColourNamed)
                else:
                    self.SegmentRects[box].setBrush(pg.mkBrush('w'))
        else:
            brush = self.ColourNone
            self.prevBoxCol = brush
            # Work out which overview segment this segment is in (could be more than one)
            inds = int(float(self.convertAmpltoSpec(startpoint)) / self.widthOverviewSegment)
            inde = int(float(self.convertAmpltoSpec(endpoint)) / self.widthOverviewSegment)
            self.overviewSegments[inds:inde+1,0] += 1
            # Turn the colour of these segments in the overview
            for box in range(inds, inde + 1):
                self.SegmentRects[box].setBrush(pg.mkBrush('w'))
                self.SegmentRects[box].setBrush(self.ColourNone)
                self.SegmentRects[box].update()

        if startpoint > endpoint:
            temp = startpoint
            startpoint = endpoint
            endpoint = temp
        if y1 > y2:
            temp = y1
            y1 = y2
            y2 = temp

        # Add the segments, connect up the listeners
        p_ampl_r = pg.LinearRegionItem(brush=brush)

        self.p_ampl.addItem(p_ampl_r, ignoreBounds=True)
        p_ampl_r.setRegion([startpoint, endpoint])
        p_ampl_r.sigRegionChangeFinished.connect(self.updateRegion_ampl)

        if y1==0 and y2==0:
            p_spec_r = pg.LinearRegionItem(brush = brush)
            #self.p_spec.addItem(p_spec_r, ignoreBounds=True)
            p_spec_r.setRegion([self.convertAmpltoSpec(startpoint), self.convertAmpltoSpec(endpoint)])
        else:
            startpointS = QPointF(self.convertAmpltoSpec(startpoint),y1)
            endpointS = QPointF(self.convertAmpltoSpec(endpoint),y2)
            p_spec_r = SupportClasses.ShadedRectROI(startpointS, endpointS - startpointS, pen='r')
            #self.p_spec.addItem(p_spec_r, ignoreBounds=True)
            #p_spec_r.sigRegionChangeFinished.connect(self.updateRegion_spec)
        self.p_spec.addItem(p_spec_r, ignoreBounds=True)
        p_spec_r.sigRegionChangeFinished.connect(self.updateRegion_spec)

        # Put the text into the box
        label = pg.TextItem(text=species, color='k')
        #if self.useAmplitude:
        #    self.p_ampl.addItem(label)
            #label.setPos(startpoint, self.minampl)
        #else:
        self.p_spec.addItem(label)
            #label.setPos(self.convertAmpltoSpec(startpoint), 1)
        label.setPos(self.convertAmpltoSpec(startpoint), self.textpos)

        # Add the segments to the relevent lists
        self.listRectanglesa1.append(p_ampl_r)
        self.listRectanglesa2.append(p_spec_r)
        self.listLabels.append(label)

        if saveSeg:
            # Add the segment to the data
            self.segments.append([startpoint, endpoint, y1, y2, species])

    def mouseClicked_ampl(self,evt):
        pos = evt.scenePos()

        if self.box1id>-1:
            self.listRectanglesa1[self.box1id].setBrush(self.prevBoxCol)
            self.listRectanglesa1[self.box1id].update()
            self.listRectanglesa2[self.box1id].setBrush(self.prevBoxCol)
            self.listRectanglesa2[self.box1id].update()

        if self.p_ampl.sceneBoundingRect().contains(pos):
            mousePoint = self.p_ampl.mapSceneToView(pos)

            if self.started:
                # This is the second click, so should pay attention and close the segment
                # Stop the mouse motion connection, remove the drawing boxes
                if self.started_window=='a':
                    self.p_ampl.scene().sigMouseMoved.disconnect()
                    self.p_ampl.removeItem(self.vLine_a)
                else:
                    self.p_spec.scene().sigMouseMoved.disconnect()
                    # Add the other mouse move listener back
                    self.p_spec.scene().sigMouseMoved.connect(self.mouseMoved)
                    self.p_spec.removeItem(self.vLine_s)

                self.p_ampl.removeItem(self.drawingBox_ampl)
                self.p_spec.removeItem(self.drawingBox_spec)
                # If the user has pressed shift, copy the last species and don't use the context menu
                # If they pressed Control, add ? to the names
                modifiers = QtGui.QApplication.keyboardModifiers()
                if modifiers == QtCore.Qt.ShiftModifier:
                    self.addSegment(self.start_location, mousePoint.x(),species=self.lastSpecies)
                elif modifiers == QtCore.Qt.ControlModifier:
                    self.addSegment(self.start_location,mousePoint.x())
                    # Context menu
                    self.box1id = len(self.segments) - 1
                    self.fillBirdList(unsure=True)
                    self.menuBirdList.popup(QPoint(evt.screenPos().x(), evt.screenPos().y()))
                else:
                    self.addSegment(self.start_location,mousePoint.x())
                    # Context menu
                    self.box1id = len(self.segments) - 1
                    self.fillBirdList()
                    self.menuBirdList.popup(QPoint(evt.screenPos().x(), evt.screenPos().y()))

                self.playSegButton.setEnabled(True)
                self.playBandLimitedSegButton.setEnabled(True)

                self.listRectanglesa1[self.box1id].setBrush(fn.mkBrush(self.ColourSelected))
                self.listRectanglesa1[self.box1id].update()
                self.listRectanglesa2[self.box1id].setBrush(fn.mkBrush(self.ColourSelected))
                self.listRectanglesa2[self.box1id].update()

                self.started = not(self.started)
            else:
                # Check if the user has clicked in a box
                # Note: Returns the first one it finds
                box1id = -1
                for count in range(len(self.listRectanglesa1)):
                    x1, x2 = self.listRectanglesa1[count].getRegion()
                    if x1 <= mousePoint.x() and x2 >= mousePoint.x():
                        box1id = count

                if box1id > -1 and not evt.button() == QtCore.Qt.RightButton:
                    # User clicked in a box (with the left button)
                    # Change colour, store the old colour
                    self.box1id = box1id
                    self.prevBoxCol = self.listRectanglesa1[box1id].brush.color()
                    self.listRectanglesa1[box1id].setBrush(fn.mkBrush(self.ColourSelected))
                    self.listRectanglesa1[box1id].update()
                    self.playSegButton.setEnabled(True)
                    self.playBandLimitedSegButton.setEnabled(True)
                    self.listRectanglesa2[box1id].setBrush(fn.mkBrush(self.ColourSelected))
                    self.listRectanglesa2[box1id].update()

                    modifiers = QtGui.QApplication.keyboardModifiers()
                    if modifiers == QtCore.Qt.ControlModifier:
                        self.fillBirdList(unsure=True)
                    else:
                        self.fillBirdList()
                    self.menuBirdList.popup(QPoint(evt.screenPos().x(), evt.screenPos().y()))
                else:
                    # User hasn't clicked in a box (or used the right button), so start a new segment
                    self.start_location = mousePoint.x()
                    self.vLine_a = pg.InfiniteLine(angle=90, movable=False,pen={'color': 'r', 'width': 3})
                    self.p_ampl.addItem(self.vLine_a, ignoreBounds=True)
                    self.vLine_a.setPos(self.start_location)

                    self.playSegButton.setEnabled(False)
                    self.playBandLimitedSegButton.setEnabled(True)
                    brush = self.ColourNone
                    self.drawingBox_ampl = pg.LinearRegionItem(brush=brush)
                    self.p_ampl.addItem(self.drawingBox_ampl, ignoreBounds=True)
                    self.drawingBox_ampl.setRegion([self.start_location, self.start_location])
                    self.drawingBox_spec = pg.LinearRegionItem(brush=brush)
                    self.p_spec.addItem(self.drawingBox_spec, ignoreBounds=True)
                    self.drawingBox_spec.setRegion([self.convertAmpltoSpec(self.start_location), self.convertAmpltoSpec(self.start_location)])
                    self.p_ampl.scene().sigMouseMoved.connect(self.GrowBox_ampl)
                    self.started_window = 'a'

                    self.started = not (self.started)

    def mouseClicked_spec(self,evt):

        pos = evt.scenePos()

        if self.box1id>-1:
            self.listRectanglesa1[self.box1id].setBrush(self.prevBoxCol)
            self.listRectanglesa1[self.box1id].update()
            self.listRectanglesa2[self.box1id].setBrush(self.prevBoxCol)
            self.listRectanglesa2[self.box1id].update()

        if self.p_spec.sceneBoundingRect().contains(pos):
            mousePoint = self.p_spec.mapSceneToView(pos)

            if self.started:
                # This is the second click, so should pay attention and close the segment
                # Stop the mouse motion connection, remove the drawing boxes
                if self.dragRectangles.isChecked():
                    return
                else:
                    if self.started_window == 's':
                        self.p_spec.scene().sigMouseMoved.disconnect()
                        self.p_spec.scene().sigMouseMoved.connect(self.mouseMoved)
                        self.p_spec.removeItem(self.vLine_s)
                    else:
                        self.p_ampl.scene().sigMouseMoved.disconnect()
                        self.p_ampl.removeItem(self.vLine_a)
                    self.p_ampl.removeItem(self.drawingBox_ampl)
                    self.p_spec.removeItem(self.drawingBox_spec)
                    # If the user has pressed shift, copy the last species and don't use the context menu
                    modifiers = QtGui.QApplication.keyboardModifiers()
                    if modifiers == QtCore.Qt.ShiftModifier:
                        self.addSegment(self.start_location, self.convertSpectoAmpl(mousePoint.x()), species=self.lastSpecies)
                    elif modifiers == QtCore.Qt.ControlModifier:
                        self.addSegment(self.start_location, self.convertSpectoAmpl(mousePoint.x()))
                        # Context menu
                        self.box1id = len(self.segments) - 1
                        self.fillBirdList(unsure=True)
                        self.menuBirdList.popup(QPoint(evt.screenPos().x(), evt.screenPos().y()))
                    else:
                        self.addSegment(self.start_location, self.convertSpectoAmpl(mousePoint.x()))
                        # Context menu
                        self.box1id = len(self.segments) - 1
                        self.fillBirdList()
                        self.menuBirdList.popup(QPoint(evt.screenPos().x(), evt.screenPos().y()))

                    self.playSegButton.setEnabled(True)
                    self.playBandLimitedSegButton.setEnabled(True)

                    self.listRectanglesa1[self.box1id].setBrush(fn.mkBrush(self.ColourSelected))
                    self.listRectanglesa1[self.box1id].update()
                    self.listRectanglesa2[self.box1id].setBrush(fn.mkBrush(self.ColourSelected))
                    self.listRectanglesa2[self.box1id].update()

                    self.started = not(self.started)
            else:
                # Check if the user has clicked in a box
                # Note: Returns the first one it finds
                box1id = -1
                for count in range(len(self.listRectanglesa2)):
                    if type(self.listRectanglesa2[count]) == self.ROItype:
                        x1 = self.listRectanglesa2[count].pos().x()
                        y1 = self.listRectanglesa2[count].pos().y()
                        x2 = x1 + self.listRectanglesa2[count].size().x()
                        y2 = y1 + self.listRectanglesa2[count].size().y()
                        if x1 <= mousePoint.x() and x2 >= mousePoint.x() and y1 <= mousePoint.y() and y2 >= mousePoint.y():
                            box1id = count
                    else:
                        x1, x2 = self.listRectanglesa2[count].getRegion()
                        if x1 <= mousePoint.x() and x2 >= mousePoint.x():
                            box1id = count

                if box1id > -1 and not evt.button() == QtCore.Qt.RightButton:
                    # User clicked in a box (with the left button)
                    self.box1id = box1id
                    self.prevBoxCol = self.listRectanglesa1[box1id].brush.color()
                    self.listRectanglesa1[box1id].setBrush(fn.mkBrush(self.ColourSelected))
                    self.listRectanglesa1[box1id].update()
                    self.playSegButton.setEnabled(True)
                    self.playBandLimitedSegButton.setEnabled(True)
                    self.listRectanglesa2[box1id].setBrush(fn.mkBrush(self.ColourSelected))
                    self.listRectanglesa2[box1id].update()
                    modifiers = QtGui.QApplication.keyboardModifiers()
                    if modifiers == QtCore.Qt.ControlModifier:
                        self.fillBirdList(unsure=True)
                    else:
                        self.fillBirdList()
                    self.menuBirdList.popup(QPoint(evt.screenPos().x(), evt.screenPos().y()))
                else:
                    # User hasn't clicked in a box (or used the right button), so start a new segment
                    # Note that need to click in the same plot both times.
                    if self.dragRectangles.isChecked():
                        return
                    else:
                        self.start_location = self.convertSpectoAmpl(mousePoint.x())
                        self.vLine_s = pg.InfiniteLine(angle=90, movable=False,pen={'color': 'r', 'width': 3})
                        self.p_spec.addItem(self.vLine_s, ignoreBounds=True)
                        self.vLine_s.setPos(mousePoint.x())
                        self.playSegButton.setEnabled(False)
                        self.playBandLimitedSegButton.setEnabled(True)

                        brush = self.ColourNone
                        self.drawingBox_ampl = pg.LinearRegionItem(brush=brush)
                        self.p_ampl.addItem(self.drawingBox_ampl, ignoreBounds=True)
                        self.drawingBox_ampl.setRegion([self.start_location, self.start_location])
                        self.drawingBox_spec = pg.LinearRegionItem(brush=brush)
                        self.p_spec.addItem(self.drawingBox_spec, ignoreBounds=True)
                        self.drawingBox_spec.setRegion([mousePoint.x(),mousePoint.x()])
                        self.p_spec.scene().sigMouseMoved.connect(self.GrowBox_spec)
                        self.started_window = 's'

                        self.started = not (self.started)

    def mouseDragged_spec(self, evt1, evt2, evt3):
        if self.box1id>-1:
            self.listRectanglesa1[self.box1id].setBrush(self.prevBoxCol)
            self.listRectanglesa1[self.box1id].update()
            self.listRectanglesa2[self.box1id].setBrush(self.prevBoxCol)
            self.listRectanglesa2[self.box1id].update()

        if self.dragRectangles.isChecked():
            evt1 = self.p_spec.mapSceneToView(evt1)
            evt2 = self.p_spec.mapSceneToView(evt2)

            # If the user has pressed shift, copy the last species and don't use the context menu
            modifiers = QtGui.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ShiftModifier:
                self.addSegment(self.convertSpectoAmpl(evt1.x()), self.convertSpectoAmpl(evt2.x()), evt1.y(), evt2.y(),self.lastSpecies)
            elif modifiers == QtCore.Qt.ControlModifier:
                self.addSegment(self.convertSpectoAmpl(evt1.x()), self.convertSpectoAmpl(evt2.x()), evt1.y(), evt2.y())
                # Context menu
                self.box1id = len(self.segments) - 1
                self.fillBirdList(unsure=True)
                self.menuBirdList.popup(QPoint(evt.screenPos().x(), evt.screenPos().y()))
            else:
                self.addSegment(self.convertSpectoAmpl(evt1.x()), self.convertSpectoAmpl(evt2.x()), evt1.y(), evt2.y())
                # Context menu
                self.box1id = len(self.segments) - 1
                self.fillBirdList()
                self.menuBirdList.popup(QPoint(evt3.x(), evt3.y()))

            self.playSegButton.setEnabled(True)
            self.playBandLimitedSegButton.setEnabled(True)

            self.listRectanglesa1[self.box1id].setBrush(fn.mkBrush(self.ColourSelected))
            self.listRectanglesa1[self.box1id].update()
            self.listRectanglesa2[self.box1id].setBrush(fn.mkBrush(self.ColourSelected))
            self.listRectanglesa2[self.box1id].update()
        else:
            return

    def GrowBox_ampl(self,evt):
        pos = evt
        if self.p_ampl.sceneBoundingRect().contains(pos):
            mousePoint = self.p_ampl.mapSceneToView(pos)
            self.drawingBox_ampl.setRegion([self.start_location, mousePoint.x()])
            self.drawingBox_spec.setRegion([self.convertAmpltoSpec(self.start_location), self.convertAmpltoSpec(mousePoint.x())])

    def GrowBox_spec(self, evt):
        pos = evt
        if self.p_spec.sceneBoundingRect().contains(pos):
            mousePoint = self.p_spec.mapSceneToView(pos)
            self.drawingBox_ampl.setRegion([self.start_location, self.convertSpectoAmpl(mousePoint.x())])
            self.drawingBox_spec.setRegion([self.convertAmpltoSpec(self.start_location), mousePoint.x()])

    def birdSelected(self,birdname):
        # This collects the label for a bird from the context menu and processes it
        #print birdname, self.box1id

        oldname = self.segments[self.box1id][4]
        # Work out which overview segment this segment is in (could be more than one)
        inds = int(float(self.convertAmpltoSpec(self.segments[self.box1id][0])) / self.widthOverviewSegment)
        inde = int(float(self.convertAmpltoSpec(self.segments[self.box1id][1])) / self.widthOverviewSegment)
        if oldname == "Don't Know":
            if birdname != "Don't Know":
                if birdname[-1] == '?':
                    self.overviewSegments[inds:inde + 1, 0] -= 1
                    self.overviewSegments[inds:inde + 1, 2] += 1
                else:
                    self.overviewSegments[inds:inde + 1, 0] -= 1
                    self.overviewSegments[inds:inde + 1, 1] += 1
        elif oldname[-1] == '?':
            if birdname[-1] != '?':
                if birdname == "Don't Know":
                    self.overviewSegments[inds:inde + 1, 2] -= 1
                    self.overviewSegments[inds:inde + 1, 0] += 1
                else:
                    self.overviewSegments[inds:inde + 1, 2] -= 1
                    self.overviewSegments[inds:inde + 1, 1] += 1
        else:
            if birdname == "Don't Know":
                self.overviewSegments[inds:inde + 1, 1] -= 1
                self.overviewSegments[inds:inde + 1, 0] += 1
            elif birdname[-1] == '?':
                self.overviewSegments[inds:inde + 1, 1] -= 1
                self.overviewSegments[inds:inde + 1, 2] += 1

        for box in range(inds, inde + 1):
            if self.overviewSegments[box, 0] > 0:
                self.SegmentRects[box].setBrush(pg.mkBrush('w'))
                self.SegmentRects[box].setBrush(self.ColourNone)
                self.SegmentRects[box].update()
            elif self.overviewSegments[box, 2] > 0:
                self.SegmentRects[box].setBrush(self.ColourPossible)
            elif self.overviewSegments[box, 1] > 0:
                self.SegmentRects[box].setBrush(pg.mkBrush('w'))
                self.SegmentRects[box].setBrush(self.ColourNamed)
                self.SegmentRects[box].update()
            else:
                self.SegmentRects[box].setBrush(pg.mkBrush('w'))

        # Now update the text
        if birdname is not 'Other':
            self.updateText(birdname)
            # Put the selected bird name at the top of the list
            if birdname[-1] == '?':
                birdname = birdname[:-1]
            self.config['BirdList'].remove(birdname)
            self.config['BirdList'].insert(0,birdname)
        else:
            text, ok = QInputDialog.getText(self, 'Bird name', 'Enter the bird name:')
            if ok:
                text = str(text).title()
                self.updateText(text)

                if text in self.config['BirdList']:
                    pass
                else:
                    # Add the new bird name.
                    #count = 0
                    #while self.config['BirdList'][count] < text and count < len(self.config['BirdList'])-1:
                    #    count += 1
                    #self.config['BirdList'].insert(count-1,text)
                    self.config['BirdList'].insert(0,text)
                    self.saveConfig = True

                    #bird = self.menuBird2.addAction(text)
                    #receiver = lambda birdname=text: self.birdSelected(birdname)
                    #self.connect(bird, SIGNAL("triggered()"), receiver)
                    #self.menuBird2.addAction(bird)
        #print "Updated segments",self.overviewSegments

    def mouseMoved(self,evt):
        # Print the time, frequency, power for mouse location in the spectrogram
        # TODO: Format the time string, check the others
        if self.p_spec.sceneBoundingRect().contains(evt):
            mousePoint = self.p_spec.mapSceneToView(evt)
            indexx = int(mousePoint.x())
            indexy = int(mousePoint.y())
            if indexx > 0 and indexx < np.shape(self.sg)[0] and indexy > 0 and indexy < np.shape(self.sg)[1]:
                self.pointData.setText('time=%0.2f (s), freq=%0.1f (Hz),power=%0.1f (dB)' % (self.convertSpectoAmpl(mousePoint.x()), mousePoint.y() * self.sampleRate / 2. / np.shape(self.sg)[1], self.sg[indexx, indexy]))

    # def activateRadioButtons(self):
        # Make the radio buttons selectable
    #     found = False
    #     for i in range(len(self.birds1)):
    #         self.birds1[i].setEnabled(True)
    #         if str(self.a1text[self.box1id].get_text()) == self.birds1[i].text():
    #             self.birds1[i].setChecked(True)
    #             found = True
    #     for i in range(len(self.birds2)):
    #         self.birds2[i].setEnabled(True)
    #         if str(self.a1text[self.box1id].get_text()) == self.birds2[i].text():
    #             self.birds2[i].setChecked(True)
    #             found = True
    #
    #     if not found:
    #         # Select 'Other' in radio buttons (last item) and activate the listwidget
    #         self.birds2[-1].setChecked(True)
    #         self.birdList.setEnabled(True)
    #         items = self.birdList.findItems(str(self.a1text[self.box1id].get_text()), Qt.MatchExactly)
    #         for item in items:
    #             self.birdList.setCurrentItem(item)

    def dockReplace(self):
        self.area.restoreState(self.state)

    def updateText(self, text):
        # When the user sets or changes the name in a segment, update the text
        self.segments[self.box1id][4] = text
        self.listLabels[self.box1id].setText(text,'k')

        # Update the colour
        if text != "Don't Know":
            if text[-1] == '?':
                self.prevBoxCol = self.ColourPossible
            else:
                self.prevBoxCol = self.ColourNamed
        else:
            self.prevBoxCol = self.ColourNone

        self.lastSpecies = text

    # def radioBirdsClicked(self):
    #     # Listener for when the user selects a radio button
    #     # Update the text and store the data
    #     for button in self.birds1 + self.birds2:
    #         if button.isChecked():
    #             if button.text() == "Other":
    #                 self.birdList.setEnabled(True)
    #             else:
    #                 self.birdList.setEnabled(False)
    #                 self.updateText(str(button.text()))
    #
    # def listBirdsClicked(self, item):
    #     # Listener for clicks in the listbox of birds
    #     if (item.text() == "Other"):
    #         self.tbox.setEnabled(True)
    #     else:
    #         # Save the entry
    #         self.updateText(str(item.text()))
    #         # self.segments[self.box1id][4] = str(item.text())
    #         # self.a1text[self.box1id].set_text(str(item.text()))
    #         # # The font size is a pain because the window is in pixels, so have to transform it
    #         # # Force a redraw to make bounding box available
    #         # self.canvasMain.draw()
    #         # # fs = a1t.get_fontsize()
    #         # width = self.a1text[self.box1id].get_window_extent().inverse_transformed(self.a1.transData).width
    #         # if width > self.segments[self.box1id][1] - self.segments[self.box1id][0]:
    #         #     self.a1text[self.box1id].set_fontsize(8)
    #         #
    #         # self.listRectanglesa1[self.box1id].set_facecolor('b')
    #         # self.listRectanglesa2[self.box1id].set_facecolor('b')
    #         # self.topBoxCol = self.listRectanglesa1[self.box1id].get_facecolor()
    #         # self.canvasMain.draw()
    #
    # def birdTextEntered(self):
    #     # Listener for the text entry in the bird list
    #     # Check text isn't already in the listbox, and add if not
    #     # Doesn't sort the list, but will when program is closed
    #     item = self.birdList.findItems(self.tbox.text(), Qt.MatchExactly)
    #     if item:
    #         pass
    #     else:
    #         self.birdList.addItem(self.tbox.text())
    #         self.config['ListBirdsEntries'].append(str(self.tbox.text()))
    #     self.updateText(str(self.tbox.text()))
    #     # self.segments[self.box1id][4] = str(self.tbox.text())
    #     # self.a1text[self.box1id].set_text(str(self.tbox.text()))
    #     # # The font size is a pain because the window is in pixels, so have to transform it
    #     # # Force a redraw to make bounding box available
    #     # self.canvasMain.draw()
    #     # # fs = self.a1text[self.box1id].get_fontsize()
    #     # width = self.a1text[self.box1id].get_window_extent().inverse_transformed(self.a1.transData).width
    #     # if width > self.segments[self.box1id][1] - self.segments[self.box1id][0]:
    #     #     self.a1text[self.box1id].set_fontsize(8)
    #     #
    #     # self.listRectanglesa1[self.box1id].set_facecolor('b')
    #     # self.listRectanglesa2[self.box1id].set_facecolor('b')
    #     # self.topBoxCol = self.listRectanglesa1[self.box1id].get_facecolor()
    #     # self.canvasMain.draw()
    #     self.saveConfig = True
    #     # self.tbox.setEnabled(False)

    def setColourMap(self,cmap):
        self.config['cmap'] = cmap

        import colourMaps
        pos, colour, mode = colourMaps.colourMaps(cmap)

        cmap = pg.ColorMap(pos, colour,mode)
        self.lut = cmap.getLookupTable(0.0, 1.0, 256)

        self.specPlot.setLookupTable(self.lut)
        self.overviewImage.setLookupTable(self.lut)

    def invertColourMap(self):
        self.cmapInverted = not self.cmapInverted
        self.setColourLevels()

    def setColourLevels(self):
        # Choose the black and white levels
        minsg = np.min(self.sg)
        maxsg = np.max(self.sg)
        brightness = self.brightnessSlider.value()
        contrast = self.contrastSlider.value()
        self.colourStart = (brightness / 100.0 * contrast / 100.0) * (maxsg - minsg) + minsg
        self.colourEnd = (maxsg - minsg) * (1.0 - contrast / 100.0) + self.colourStart

        if self.cmapInverted:
            self.overviewImage.setLevels([self.colourEnd, self.colourStart])
            self.specPlot.setLevels([self.colourEnd, self.colourStart])
        else:
            self.overviewImage.setLevels([self.colourStart, self.colourEnd])
            self.specPlot.setLevels([self.colourStart, self.colourEnd])
# ===========
# Code for things at the top of the screen (overview figure and left/right buttons)
    def moveLeft(self):
        # When the left button is pressed (next to the overview plot), move everything along
        # Note the parameter to all a 10% overlap
        minX, maxX = self.overviewImageRegion.getRegion()
        newminX = max(0,minX-(maxX-minX)*0.9)
        self.overviewImageRegion.setRegion([newminX, newminX+maxX-minX])
        self.updateOverview()
        self.playPosition = int(self.convertSpectoAmpl(newminX)*1000.0)
        #print "Slider:", self.convertSpectoAmpl(newminX),self.convertSpectoAmpl(maxX)
        #self.setSliderLimits(1000*self.convertSpectoAmpl(newminX),1000*self.convertSpectoAmpl(maxX))

    def moveRight(self):
        # When the right button is pressed (next to the overview plot), move everything along
        # Note the parameter to allow a 10% overlap
        minX, maxX = self.overviewImageRegion.getRegion()
        newminX = min(np.shape(self.sg)[0]-(maxX-minX),minX+(maxX-minX)*0.9)
        self.overviewImageRegion.setRegion([newminX, newminX+maxX-minX])
        self.updateOverview()
        self.playPosition = int(self.convertSpectoAmpl(newminX)*1000.0)
        #print "Slider:", self.convertSpectoAmpl(newminX),self.convertSpectoAmpl(maxX)
        #self.setSliderLimits(1000*self.convertSpectoAmpl(newminX),1000*self.convertSpectoAmpl(maxX))

    def scroll(self):
        # When the slider is moved, change the position of the plot
        newminX = self.scrollSlider.value()
        minX, maxX = self.overviewImageRegion.getRegion()
        self.overviewImageRegion.setRegion([newminX, newminX+maxX-minX])
        self.updateOverview()
        self.playPosition = int(self.convertSpectoAmpl(newminX)*1000.0)

    # def showSegments(self,seglen=0):
    #     # This plots the segments that are returned from any of the segmenters and adds them to the set of segments
    #     # If there are segments, show them
    #     for count in range(seglen,len(self.segments)):
    #         if self.segments[count][4] == 'None' or self.segments[count][4] == "Don't Know":
    #             facecolour = 'r'
    #         else:
    #             facecolour = 'b'
    #         a1R = self.a1.add_patch(pl.Rectangle((self.segments[count][0], np.min(self.audiodata)),
    #                                              self.segments[count][1] - self.segments[count][0],
    #                                              self.plotheight,
    #                                              facecolor=facecolour,
    #                                              alpha=0.5))
    #         a2R = self.a2.add_patch(pl.Rectangle((self.segments[count][0]*self.sampleRate / self.config['incr'], self.segments[count][2]),
    #                                              self.segments[count][1]*self.sampleRate / self.config['incr'] - self.segments[count][
    #                                                  0]*self.sampleRate / self.config['incr'],
    #                                              self.segments[count][3], facecolor=facecolour,
    #                                              alpha=0.5))
    #
    #         self.listRectanglesa1.append(a1R)
    #         self.listRectanglesa2.append(a2R)
    #         a1t = self.a1.text(self.segments[count][0], np.min(self.audiodata), self.segments[count][4])
    #         # The font size is a pain because the window is in pixels, so have to transform it
    #         # Force a redraw to make bounding box available
    #         self.canvasMain.draw()
    #         # fs = a1t.get_fontsize()
    #         width = a1t.get_window_extent().inverse_transformed(self.a1.transData).width
    #         #print width, self.segments[count][1] - self.segments[count][0]
    #         if width > self.segments[count][1] - self.segments[count][0]:
    #             a1t.set_fontsize(8)
    #
    #         self.a1text.append(a1t)
    #
    #     self.canvasMain.draw()

    def changeWidth(self, value):
        # This is the listener for the spinbox that decides the width of the main window.
        # It updates the top figure plots as the window width is changed.
        # Slightly annoyingly, it gets called when the value gets reset, hence the first line
        if not hasattr(self,'overviewImageRegion'):
            return
        self.windowSize = value

        # Redraw the highlight in the overview figure appropriately
        minX, maxX = self.overviewImageRegion.getRegion()
        newmaxX = self.convertAmpltoSpec(value)+minX
        self.overviewImageRegion.setRegion([minX, newmaxX])
        self.scrollSlider.setMaximum(np.shape(self.sg)[0]-self.convertAmpltoSpec(self.widthWindow.value()))
        self.updateOverview()

# ===============
# Generate the various dialogs that match the buttons

    def humanClassifyDialog1(self):
        # Create the dialog that shows calls to the user for verification
        if len(self.segments)>0:
            self.box1id = 0
            # Different calls for the two types of region
            if type(self.listRectanglesa2[self.box1id]) == self.ROItype:
                x1 = self.listRectanglesa2[self.box1id].pos()[0]
                x2 = x1 + self.listRectanglesa2[self.box1id].size()[0]
            else:
                x1, x2 = self.listRectanglesa2[self.box1id].getRegion()
            x1 = int(x1)
            x2 = int(x2)
            self.humanClassifyDialog1 = Dialogs.HumanClassify1(self.sg[x1:x2,:],self.segments[self.box1id][4],self.lut,self.colourStart,self.colourEnd,self.cmapInverted, self.config['BirdList'])
            self.humanClassifyDialog1.show()
            self.humanClassifyDialog1.activateWindow()
            self.humanClassifyDialog1.close.clicked.connect(self.humanClassifyClose1)
            self.humanClassifyDialog1.correct.clicked.connect(self.humanClassifyCorrect1)

    def humanClassifyClose1(self):
        # Listener for the human verification dialog.
        self.humanClassifyDialog1.done(1)

    def humanClassifyNextImage1(self):
        # Get the next image
        # TODO: Ends rather suddenly
        if self.box1id != len(self.listRectanglesa2)-1:
            self.box1id += 1
            # Different calls for the two types of region
            if type(self.listRectanglesa2[self.box1id]) == self.ROItype:
                x1 = self.listRectanglesa2[self.box1id].pos()[0]
                x2 = x1 + self.listRectanglesa2[self.box1id].size()[0]
            else:
                x1, x2 = self.listRectanglesa2[self.box1id].getRegion()
            x1 = int(x1)
            x2 = int(x2)
            self.humanClassifyDialog1.setImage(self.sg[x1:x2,:],self.segments[self.box1id][4])
        else:
            print "Last image"
            self.humanClassifyClose1()

    def humanClassifyCorrect1(self):
        label, self.saveConfig = self.humanClassifyDialog1.getValues()
        # TODO: Test, particularly that new birds are added
        # TODO: update the listRects
        if label != self.segments[self.box1id][4]:
            self.updateText(label)
            if self.saveConfig:
                self.config['ListBirdsEntries'].append(label)

        self.humanClassifyNextImage1()

    def humanClassifyDialog2(self):
        # Create the dialog that shows calls to the user for verification
        # TODO: Fix the next line
        label = "Bird"
        if len(self.segments)>0:
            self.humanClassifyDialog2 = Dialogs.HumanClassify2(self.sg,self.segments,label,self.sampleRate, self.config['incr'], self.lut,self.colourStart,self.colourEnd,self.cmapInverted)
            self.humanClassifyDialog2.show()
            self.humanClassifyDialog2.activateWindow()

    def showSpectrogramDialog(self):
        # Create the spectrogram dialog when the button is pressed
        if not hasattr(self,'spectrogramDialog'):
            self.spectrogramDialog = Dialogs.Spectrogram(self.config['window_width'],self.config['incr'])
        self.spectrogramDialog.show()
        self.spectrogramDialog.activateWindow()
        self.spectrogramDialog.activate.clicked.connect(self.spectrogram)
        # TODO: next line
        # self.connect(self.spectrogramDialog, SIGNAL("changed"), self.spectrogram)

    def spectrogram(self):
        # Listener for the spectrogram dialog.
        [alg, mean_normalise, multitaper, window_width, incr] = self.spectrogramDialog.getValues()

        self.sp.set_width(int(str(window_width)), int(str(incr)))
        self.sgRaw = self.sp.spectrogram(self.audiodata,str(alg),mean_normalise=True,onesided=True,multitaper=multitaper)
        maxsg = np.min(self.sgRaw)
        self.sg = np.abs(np.where(self.sgRaw==0,0.0,10.0 * np.log10(self.sgRaw/maxsg)))

        #self.amplPlot.setData(np.linspace(0.0,float(self.datalength)/self.sampleRate,num=self.datalength,endpoint=True),self.audiodata)
        #self.w_spec.removeItem(self.timeaxis)
        #self.timeaxis = None

        # If the size of the spectrogram has changed, need to update the positions of things
        if int(str(incr)) != self.config['incr'] or int(str(window_width)) != self.config['window_width']:
            self.config['incr'] = int(str(incr))
            self.config['window_width'] = int(str(window_width))
            self.changeWidth(self.widthWindow.value())
            # Update the positions of the segments
            self.textpos = np.shape(self.sg)[1] + self.config['textoffset']
            for s in range(len(self.listRectanglesa2)):
                x1 = self.convertAmpltoSpec(self.listRectanglesa1[s].getRegion()[0])
                x2 = self.convertAmpltoSpec(self.listRectanglesa1[s].getRegion()[1])
                self.listRectanglesa2[s].setRegion([x1, x2])
                self.listLabels[s].setPos(x1,self.textpos)
            # Update the axis
            FreqRange = (self.maxFreq - self.minFreq)/1000.
            self.specaxis.setTicks([[(0, self.minFreq / 1000.),
                                     (np.shape(self.sg)[1] / 4, self.minFreq / 1000. + FreqRange / 4.),
                                     (np.shape(self.sg)[1] / 2, self.minFreq / 1000. + FreqRange / 2.),
                                     (3 * np.shape(self.sg)[1] / 4, self.minFreq / 1000. + 3 * FreqRange / 4.),
                                     (np.shape(self.sg)[1], self.minFreq / 1000. + FreqRange)]])

            # Redraw everything and redraw it
            self.removeSegments()
            for r in self.SegmentRects:
                self.p_overview2.removeItem(r)
            self.SegmentRects = []
            self.p_overview.removeItem(self.overviewImageRegion)

            self.drawOverview()
            self.drawfigMain()
            if hasattr(self, 'seg'):
                self.seg.setNewData(self.audiodata, self.sgRaw, self.sampleRate, self.config['window_width'],
                                    self.config['incr'])

    def denoiseDialog(self):
        # Create the denoising dialog when the relevant button is pressed
        # TODO: Anything to help setting bandpass levels?
        self.denoiseDialog = Dialogs.Denoise()
        self.denoiseDialog.show()
        self.denoiseDialog.activateWindow()
        self.denoiseDialog.activate.clicked.connect(self.denoise)
        self.denoiseDialog.undo.clicked.connect(self.denoise_undo)
        self.denoiseDialog.save.clicked.connect(self.denoise_save)

    def backup(self):
        if hasattr(self, 'audiodata_backup'):
            if self.audiodata_backup is not None:
                audiodata_backup_new = np.empty(
                    (np.shape(self.audiodata_backup)[0], np.shape(self.audiodata_backup)[1] + 1))
                audiodata_backup_new[:, :-1] = np.copy(self.audiodata_backup)
                audiodata_backup_new[:, -1] = np.copy(self.audiodata)
                self.audiodata_backup = audiodata_backup_new
            else:
                self.audiodata_backup = np.empty((np.shape(self.audiodata)[0], 1))
                self.audiodata_backup[:, 0] = np.copy(self.audiodata)
        else:
            self.audiodata_backup = np.empty((np.shape(self.audiodata)[0], 1))
            self.audiodata_backup[:, 0] = np.copy(self.audiodata)

    def denoise(self):
        # Listener for the denoising dialog.
        # Calls the denoiser and then plots the updated data
        # TODO: should it be saved automatically, or a button added?
        [alg,depthchoice,depth,thrType,thr,wavelet,start,end,width] = self.denoiseDialog.getValues()
        # TODO: deal with these!
        # TODO: Undo needs testing
        self.backup()
        if str(alg) == "Wavelets":
            if thrType is True:
                type = 'Soft'
            else:
                type = 'Hard'
            if depthchoice:
                depth = None
            else:
                depth = int(str(depth))
            self.audiodata = self.sp.waveletDenoise(self.audiodata,type,float(str(thr)),depth,str(wavelet))
        elif str(alg) == "Bandpass --> Wavelets":
            if thrType is True:
                type = 'soft'
            else:
                type = 'hard'
            if depthchoice:
                depth = None
            else:
                depth = int(str(depth))
            self.audiodata = self.sp.bandpassFilter(self.audiodata,int(str(start)),int(str(end)))
            self.audiodata = self.sp.waveletDenoise(self.audiodata,type,float(str(thr)),depth,str(wavelet))
        elif str(alg) == "Wavelets --> Bandpass":
            if thrType is True:
                type = 'soft'
            else:
                type = 'hard'
            if depthchoice:
                depth = None
            else:
                depth = int(str(depth))
            self.audiodata = self.sp.waveletDenoise(self.audiodata,type,float(str(thr)),depth,str(wavelet))
            self.audiodata = self.sp.bandpassFilter(self.audiodata,int(str(start)),int(str(end)))
        #elif str(alg) == "Wavelets + Bandpass":
            #if thrType is True:
                #type = 'soft'
            #else:
                #type = 'hard'
            #if depthchoice:
                #depth = None
            #else:
                #depth = int(str(depth))
            #self.audiodata = self.sp.waveletDenoise(self.audiodata,float(str(thr)),int(str(depth)),str(wavelet))
            #self.audiodata = self.sp.bandpassFilter(self.audiodata,int(str(start)),int(str(end)))
        elif str(alg) == "Bandpass":
            self.audiodata = self.sp.bandpassFilter(self.audiodata, int(str(start)), int(str(end)))
        elif str(alg) == "Butterworth Bandpass":
            self.audiodata = self.sp.ButterworthBandpass(self.audiodata, self.sampleRate, low=int(str(start)), high=int(str(end)))
        else:
            #"Median Filter"
            self.audiodata = self.sp.medianFilter(self.audiodata,int(str(width)))

        self.sgRaw = self.sp.spectrogram(self.audiodata,self.sampleRate,mean_normalise=True,onesided=True,multitaper=False)
        maxsg = np.min(self.sgRaw)
        self.sg = np.abs(np.where(self.sgRaw==0,0.0,10.0 * np.log10(self.sgRaw/maxsg)))
        self.overviewImage.setImage(self.sg)

        self.specPlot.setImage(self.sg)
        self.amplPlot.setData(np.linspace(0.0,float(self.datalength)/self.sampleRate*1000.0,num=self.datalength,endpoint=True),self.audiodata)
        #self.specaxis.setTicks([[(0,0),(np.shape(self.sg)[1]/4,self.sampleRate/8000),(np.shape(self.sg)[1]/2,self.sampleRate/4000),(3*np.shape(self.sg)[1]/4,3*self.sampleRate/8000),(np.shape(self.sg)[1],self.sampleRate/2000)]])
        self.minFreq = int(str(start))
        self.maxFreq = int(str(end))

        self.setColourLevels()

    def redoFreqAxis(self):
        start = self.minFreq
        end = self.maxFreq

        height = self.sampleRate / 2. / np.shape(self.sg)[1]

        self.overviewImage.setImage(self.sg[:,int(float(start)/height):int(float(end)/height)])
        self.specPlot.setImage(self.sg[:,int(float(start)/height):int(float(end)/height)])

        FreqRange = end - start
        SpecRange = FreqRange/height
        self.specaxis.setTicks([[(0,(start/1000.)),(SpecRange/4,(start/1000.+FreqRange/4000.)),(SpecRange/2,(start/1000.+FreqRange/2000.)),(3*SpecRange/4,(start/1000.+3*FreqRange/4000.)),(SpecRange,(start/1000.+FreqRange/1000.))]])

    def denoise_undo(self):
        # Listener for undo button in denoising dialog
        # TODO: Can I actually delete something from an object?
        print("Undoing",np.shape(self.audiodata_backup))
        if hasattr(self,'audiodata_backup'):
            if self.audiodata_backup is not None:
                if np.shape(self.audiodata_backup)[1]>0:
                    self.audiodata = np.copy(self.audiodata_backup[:,-1])
                    self.audiodata_backup = self.audiodata_backup[:,:-1]
                    self.sp.setNewData(self.audiodata,self.sampleRate)
                    self.sgRaw = self.sp.spectrogram(self.audiodata,self.sampleRate,mean_normalise=True,onesided=True,multitaper=False)
                    maxsg = np.min(self.sgRaw)
                    self.sg = np.abs(np.where(self.sgRaw == 0, 0.0, 10.0 * np.log10(self.sgRaw / maxsg)))
                    self.overviewImage.setImage(self.sg)
                    self.specPlot.setImage(self.sg)
                    self.amplPlot.setData(
                        np.linspace(0.0, float(self.datalength) / self.sampleRate, num=self.datalength, endpoint=True),
                        self.audiodata)
                    if hasattr(self,'seg'):
                        self.seg.setNewData(self.audiodata,self.sgRaw,self.sampleRate,self.config['window_width'],self.config['incr'])

                    self.setColourLevels()

                    #self.drawfigMain()

    def denoise_save(self):
        # Listener for save button in denoising dialog
        # Save denoised data
        # Other players need them to be 16 bit, which is this magic number
        #self.audiodata *= 32768.0
        #self.audiodata = self.audiodata.astype('int16')
        #import soundfile as sf
        filename = self.filename[:-4] + '_d' + self.filename[-4:]
        self.audiodata = self.audiodata.astype('int16')
        #wavfile.write(filename,self.sampleRate, self.audiodata)
        wavio.write(filename,self.audiodata,self.sampleRate)

    def segmentationDialog(self):
        # Create the segmentation dialog when the relevant button is pressed
        self.segmentDialog = Dialogs.Segmentation(np.max(self.audiodata))
        self.segmentDialog.show()
        self.segmentDialog.activateWindow()
        self.segmentDialog.activate.clicked.connect(self.segment)
        #self.segmentDialog.save.clicked.connect(self.segments_save)

    def segment(self):
        # Listener for the segmentation dialog
        # TODO: Currently just gives them all the label "Don't Know"'
        # TODO: Add in the wavelet one
        # TODO: More testing of the algorithms, parameters, etc.
        seglen = len(self.segments)
        [alg, ampThr, medThr,HarmaThr1,HarmaThr2,PowerThr,minfreq,minperiods,Yinthr,window,FIRThr1,depth,thrType,thr,wavelet,bandchoice,start,end] = self.segmentDialog.getValues()
        if not hasattr(self,'seg'):
            self.seg = Segment.Segment(self.audiodata,self.sgRaw,self.sp,self.sampleRate,self.config['minSegment'],self.config['window_width'],self.config['incr'])
        if str(alg) == "Amplitude":
            newSegments = self.seg.segmentByAmplitude(float(str(ampThr)))
        elif str(alg) == "Median Clipping":
            newSegments = self.seg.medianClip(float(str(medThr)))
            #print newSegments
        elif str(alg) == "Harma":
            newSegments = self.seg.Harma(float(str(HarmaThr1)),float(str(HarmaThr2)))
        elif str(alg) == "Power":
            newSegments = self.seg.segmentByPower(float(str(PowerThr)))
        elif str(alg) == "Onsets":
            newSegments = self.seg.onsets()
            #print newSegments
        elif str(alg) == "Fundamental Frequency":
            newSegments, pitch, times = self.seg.yin(int(str(minfreq)),int(str(minperiods)),float(str(Yinthr)),int(str(window)),returnSegs=True)
            #print newSegments
        elif str(alg) == "FIR":
            newSegments = self.seg.segmentByFIR(float(str(FIRThr1)))
            print newSegments
        else:
            #"Wavelets"
            # TODO!!
            if thrType is True:
                type = 'soft'
            else:
                type = 'hard'
            if bandchoice:
                start = None
                end = None
            else:
                start = int(str(start))
                end = int(str(end))
            # TODO: needs learning and samplerate
                #newSegments = self.seg.segmentByWavelet(thrType,float(str(thr)), int(str(depth)), wavelet,sampleRate,bandchoice,start,end,learning,)
        print len(newSegments)
        for seg in newSegments:
            print seg[0], seg[1]
            self.addSegment(seg[0],seg[1],0,0,"Don't Know",True)

    def findMatches(self):
        # Calls the cross-correlation function to find matches like the currently highlighted box
        # TODO: Other methods apart from c-c?
        # So there needs to be a currently highlighted box
        # TODO: If there isn't a box highlighted, grey out the menu option
        if not hasattr(self,'seg'):
            self.seg = Segment.Segment(self.audiodata,self.sgRaw,self.sp,self.sampleRate,self.config['minSegment'],self.config['window_width'],self.config['incr'])

        if self.box1id is None or self.box1id == -1:
            print "No box selected"
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("No segment selected to match")
            msg.setWindowTitle("Error")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        else:
            #[alg, thr] = self.matchDialog.getValues()
            # Only want to draw new segments, so find out how many there are now
            seglen = len(self.segments)
            # Get the segment -- note that takes the full y range
            # TODO: is this correct?
            if type(self.listRectanglesa2[self.box1id]) == self.ROItype:
                x1 = self.listRectanglesa2[self.box1id].pos().x()
                x2 = x1 + self.listRectanglesa2[self.box1id].size().x()
            else:
                x1, x2 = self.listRectanglesa2[self.box1id].getRegion()
            print x1, x2
            segment = self.sgRaw[int(x1):int(x2),:]
            len_seg = (x2-x1) * self.config['incr'] / self.sampleRate
            indices = self.seg.findCCMatches(segment,self.sgRaw,self.config['corrThr'])
            # indices are in spectrogram pixels, need to turn into times
            for i in indices:
                # Miss out the one selected: note the hack parameter
                if np.abs(i-x1) > self.config['overlap_allowed']:
                    time = float(i)*self.config['incr'] / self.sampleRate
                    self.addSegment(time, time+len_seg,0,0,self.segments[self.box1id][4])

    def recognise(self):
        # This will eventually call methods to do automatic recognition
        # Actually, will produce a dialog to ask which species, etc.
        # TODO
        pass

# ===============
# Code for playing sounds
    # These functions are the phonon playing code
    # Note that if want to play e.g. denoised one, will have to save it and then reload it
    def playSegment(self):
        self.segmentStop = self.playSlider.maximum()
        if self.media_obj.state() == phonon.Phonon.PlayingState:
            self.media_obj.pause()
            self.playSegButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
        elif self.media_obj.state() == phonon.Phonon.PausedState or self.media_obj.state() == phonon.Phonon.StoppedState:
            self.media_obj.play()
            self.playSegButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPause))

    def playFinished(self):
        self.playButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
        #self.bar.setValue(0)
        self.bar.setValue(self.convertAmpltoSpec(self.playSlider.value()/1000.0))

    def sliderMoved(self):
        # When the slider is moved, change the position of playback
        self.media_obj.seek(self.playSlider.value())
        # playSlider.value() is in ms, need to convert this into spectrogram pixels
        self.bar.setValue(self.convertAmpltoSpec(self.playSlider.value()/1000.0))

    def barMoved(self,evt):
        self.playSlider.setValue(self.convertSpectoAmpl(evt.x())*1000)
        self.media_obj.seek(self.convertSpectoAmpl(evt.x())*1000)

    def movePlaySlider(self, time):
        if not self.playSlider.isSliderDown():
            self.playSlider.setValue(time)
        self.timePlayed.setText(self.convertMillisecs(time)+"/"+self.totalTime)
        if time > min(self.playSlider.maximum(),self.segmentStop):
            self.media_obj.stop()
            self.playButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
            self.media_obj.seek(self.playSlider.minimum())
        self.bar.setValue(self.convertAmpltoSpec(self.playSlider.value()/1000.0))

    def setSliderLimits(self, start,end):
        self.playSlider.setRange(start, end)
        self.playSlider.setValue(start)
        self.segmentStop = self.playSlider.maximum()
        self.media_obj.seek(start)

    def playSelectedSegment(self):
        # Get selected segment start and end (or return if no segment selected)
        # TODO: This isn't pausable, since it goes back to the beginning. I think it's OK though -- they should be short?
        if self.box1id > -1:
            start = self.listRectanglesa1[self.box1id].getRegion()[0]*1000
            self.segmentStop = self.listRectanglesa1[self.box1id].getRegion()[1]*1000
            self.media_obj.seek(start)
            #self.media_obj.play()
            #self.segmentStop = self.playSlider.maximum()
            if self.media_obj.state() == phonon.Phonon.PlayingState:
                self.media_obj.pause()
                self.playSegButton.setIcon(QtGui.QIcon('img/playsegment.png'))
                # self.playButton.setText("Play")
            elif self.media_obj.state() == phonon.Phonon.PausedState or self.media_obj.state() == phonon.Phonon.StoppedState:
                self.media_obj.play()
                #self.playSegButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPause))

    def playBandLimitedSegment(self):
        # Get the band limits of the segment, bandpass filter, then play that
        # TODO: This version uses sounddevice to play it back because the phonon needed to save it and then still wouldn't actually play it. Does it matter? You can't see the bar moving.
        start = int(self.listRectanglesa1[self.box1id].getRegion()[0]*self.sampleRate)
        stop = int(self.listRectanglesa1[self.box1id].getRegion()[1]*self.sampleRate)
        bottom = int(self.segments[self.box1id][2]*self.sampleRate/2./np.shape(self.sg)[1])
        top = int(self.segments[self.box1id][3]*self.sampleRate/2./np.shape(self.sg)[1])
        if bottom > 0 and top>0:
            import sounddevice as sd

            data = self.audiodata[start:stop]
            print bottom, top
            data = self.sp.ButterworthBandpass(data, self.sampleRate, bottom, top,order=2)

            sd.play(data,self.sampleRate)
        else:
            self.playSelectedSegment()
        # TODO!! Why won't this actually play back? The file exists, and it will play if you load it
        # So there is something odd about the media_obj
        # Kludge: save the file, load, play, put it back
        # Save
        #filename = 'temp.wav'
        #data = data.astype('int16')
        #wavfile.write(filename,self.sampleRate, data)

        #sr, data = wavfile.read(filename)

        #self.media_obj.setCurrentSource(phonon.Phonon.MediaSource(filename))
        #self.media_obj.tick.connect(self.movePlaySlider)

        #print "got here"
        #print self.convertMillisecs(self.media_obj.totalTime())
        #self.media_obj.play()

        #self.media_obj.setCurrentSource(phonon.Phonon.MediaSource(self.filename))
        #self.media_obj.tick.connect(self.movePlaySlider)

# ============
# Various actions: deleting, saving, quitting
    def deleteSegment(self):
        # Listener for delete segment button, or backspace key
        # Deletes segment if one is selected, otherwise does nothing
        if self.box1id>-1:
            # Work out which overview segment this segment is in (could be more than one) and update it
            inds = int(float(self.convertAmpltoSpec(self.segments[self.box1id][0]))/self.widthOverviewSegment)
            inde = int(float(self.convertAmpltoSpec(self.segments[self.box1id][1]))/self.widthOverviewSegment)

            if self.segments[self.box1id][4] == "Don't Know":
                self.overviewSegments[inds:inde+1,0] -= 1
            elif self.segments[self.box1id][4][-1] == '?':
                self.overviewSegments[inds:inde + 1, 2] -= 1
            else:
                self.overviewSegments[inds:inde + 1, 1] -= 1
            for box in range(inds, inde + 1):
                if self.overviewSegments[box,0] > 0:
                    self.SegmentRects[box].setBrush(self.ColourNone)
                elif self.overviewSegments[box,2] > 0:
                    self.SegmentRects[box].setBrush(self.ColourPossible)
                elif self.overviewSegments[box,1] > 0:
                    self.SegmentRects[box].setBrush(self.ColourNamed)
                else:
                    self.SegmentRects[box].setBrush(pg.mkBrush('w'))

            self.p_ampl.removeItem(self.listRectanglesa1[self.box1id])
            self.p_spec.removeItem(self.listRectanglesa2[self.box1id])
            self.p_spec.removeItem(self.listLabels[self.box1id])
            del self.listLabels[self.box1id]
            del self.segments[self.box1id]
            del self.listRectanglesa1[self.box1id]
            del self.listRectanglesa2[self.box1id]
            self.box1id = -1

    def deleteAll(self):
        # Listener for delete all button
        reply = QMessageBox.question(self,"Delete All Segments","Are you sure you want to delete all segments?",    QMessageBox.Yes | QMessageBox.No)
        if reply==QMessageBox.Yes:
            self.removeSegments()

    def removeSegments(self):
        for r in self.listLabels:
            self.p_spec.removeItem(r)
        for r in self.listRectanglesa1:
            self.p_ampl.removeItem(r)
        for r in self.listRectanglesa2:
            self.p_spec.removeItem(r)
        for r in self.SegmentRects:
            r.setBrush(pg.mkBrush('w'))
            r.update()
        self.segments=[]
        self.listRectanglesa1 = []
        self.listRectanglesa2 = []
        self.listLabels = []
        self.box1id = -1

    def saveSegments(self):
        # This saves the segmentation data as a json file
        if len(self.segments)>0 or self.hasSegments:
            print("Saving segments to "+self.filename)
            if isinstance(self.filename, str):
                file = open(self.filename + '.data', 'w')
            else:
                file = open(str(self.filename) + '.data', 'w')
            json.dump(self.segments,file)

    def closeEvent(self, event):
        # Catch the user closing the window by clicking the Close button instead of quitting
        self.quit()

    def quit(self):
        # Listener for the quit button
        print("Quitting")
        self.saveSegments()
        if self.saveConfig == True:
            print "Saving config file"
            json.dump(self.config, open(self.configfile, 'wb'))
        QApplication.quit()

# =============
# Helper functions

    def splitFile5mins(self, name):
        # Nirosha wants to split files that are long (15 mins) into 5 min segments
        # Could be used when loading long files :)
        # TODO: put paging in here, possible in librosa
        try:
            self.audiodata, self.sampleRate = lr.load(name,sr=None)
        except:
            print("Error: try another file")
        nsamples = np.shape(self.audiodata)[0]
        lengthwanted = self.sampleRate * 60 * 5
        count = 0
        while (count + 1) * lengthwanted < nsamples:
            data = self.audiodata[count * lengthwanted:(count + 1) * lengthwanted]
            filename = name[:-4] + '_' +str(count) + name[-4:]
            lr.output.write_wav(filename, data, self.sampleRate)
            count += 1
        data = self.audiodata[(count) * lengthwanted:]
        filename = name[:-4] + '_' + str((count)) + name[-4:]
        lr.output.write_wav(filename,data,self.sampleRate)



    # def setImage2(self,seg):
    #     # This was an attempt to do it with pixmaps, which didn't work
    #     self.image = pg.ImageItem()
    #     self.image.setImage(seg)
    #     im1 = self.image.getPixmap()
    #
    #     self.image.setImage(-seg)
    #     im2 = self.image.getPixmap()
    #
    #     return [im1, im2]

# Start the application
app = QApplication(sys.argv)

# This screen asks what you want to do, then gets the response
# TODO: Why don't the buttons appear at once?
#first = StartScreen()
#first.exec_()

#task = first.getValues()

#if task == 0:
avianz = AviaNZInterface(configfile='AviaNZconfig.txt')
avianz.show()
app.exec_()