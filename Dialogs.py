# Dialogs used by the AviaNZ program
# Since most of them just get user selections, they are mostly just a mess of UI things

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.functions as fn
import numpy as np
import SupportClasses as SupportClasses

#======
class StartScreen(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Choose Task')
        self.activateWindow()

        #b1 = QPushButton(QIcon(":/Resources/play.svg"), "&Play Window")
        b1 = QPushButton("Manual Segmentation")
        b2 = QPushButton("Find a species")
        b3 = QPushButton("Denoise a folder")

        self.connect(b1, SIGNAL('clicked()'), self.manualSeg)
        self.connect(b2, SIGNAL('clicked()'), self.findSpecies)
        self.connect(b3, SIGNAL('clicked()'), self.denoise)

        vbox = QVBoxLayout()
        for w in [b1, b2, b3]:
                vbox.addWidget(w)

        self.setLayout(vbox)
        self.task = -1

    def manualSeg(self):
        self.task = 0
        self.accept()

    def findSpecies(self):
        self.task = 1
        self.accept()

    def denoise(self):
        self.task = 2
        self.accept()

    def getValues(self):
        return self.task

#======
class FileDataDialog(QDialog):
    def __init__(self, name, date, time, parent=None):
        super(FileDataDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        l1 = QLabel("Annotator")
        self.name = QLineEdit(self)
        self.name.setText(name)

        l2 = QLabel("Data recorded: " + date)
        l3 = QLabel("Time recorded: " + time)

        layout.addWidget(l1)
        layout.addWidget(self.name)
        layout.addWidget(l2)
        layout.addWidget(l3)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)

        layout.addWidget(button)

    def getData(self):
        return

#======
class Spectrogram(QDialog):
    # Class for the spectrogram dialog box
    # TODO: Steal the graph from Raven (View/Configure Brightness)
    def __init__(self, width, incr, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Spectrogram Options')

        self.algs = QComboBox()
        self.algs.addItems(['Hann','Parzen','Welch','Hamming','Blackman','BlackmanHarris'])

        self.mean_normalise = QCheckBox()
        self.mean_normalise.setChecked(True)
        self.multitaper = QCheckBox()

        self.activate = QPushButton("Update Spectrogram")

        self.window_width = QLineEdit(self)
        self.window_width.setText(str(width))
        self.incr = QLineEdit(self)
        self.incr.setText(str(incr))

        Box = QVBoxLayout()
        Box.addWidget(self.algs)
        Box.addWidget(QLabel('Mean normalise'))
        Box.addWidget(self.mean_normalise)
        Box.addWidget(QLabel('Multitapering'))
        Box.addWidget(self.multitaper)
        Box.addWidget(QLabel('Window Width'))
        Box.addWidget(self.window_width)
        Box.addWidget(QLabel('Hop'))
        Box.addWidget(self.incr)
        Box.addWidget(self.activate)

        # Now put everything into the frame
        self.setLayout(Box)

    def getValues(self):
        return [self.algs.currentText(),self.mean_normalise.checkState(),self.multitaper.checkState(),self.window_width.text(),self.incr.text()]

    # def closeEvent(self, event):
    #     msg = QMessageBox()
    #     msg.setIcon(QMessageBox.Question)
    #     msg.setText("Do you want to keep the new values?")
    #     msg.setWindowTitle("Closing Spectrogram Dialog")
    #     msg.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
    #     msg.buttonClicked.connect(self.resetValues)
    #     msg.exec_()
    #     return

    # def resetValues(self,button):
    #     print button.text()

#======
class Segmentation(QDialog):
    # Class for the segmentation dialog box
    # TODO: add the wavelet params
    # TODO: work out how to return varying size of params, also process them
    # TODO: test and play
    def __init__(self, maxv, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Segmentation Options')

        self.algs = QComboBox()
        #self.algs.addItems(["Amplitude","Energy Curve","Harma","Median Clipping","Wavelets"])
        self.algs.addItems(["Amplitude","Harma","Power","Median Clipping","Onsets","Fundamental Frequency","FIR"])
        self.algs.currentIndexChanged[QString].connect(self.changeBoxes)
        self.prevAlg = "Amplitude"
        self.activate = QPushButton("Segment")
        #self.save = QPushButton("Save segments")

        # Define the whole set of possible options for the dialog box here, just to have them together.
        # Then hide and show them as required as the algorithm chosen changes.

        # Spin box for amplitude threshold
        self.ampThr = QDoubleSpinBox()
        self.ampThr.setRange(0.001,maxv+0.001)
        self.ampThr.setSingleStep(0.002)
        self.ampThr.setDecimals(4)
        self.ampThr.setValue(maxv+0.001)

        self.HarmaThr1 = QSpinBox()
        self.HarmaThr1.setRange(10,50)
        self.HarmaThr1.setSingleStep(1)
        self.HarmaThr1.setValue(10)
        self.HarmaThr2 = QDoubleSpinBox()
        self.HarmaThr2.setRange(0.1,0.95)
        self.HarmaThr2.setSingleStep(0.05)
        self.HarmaThr2.setDecimals(2)
        self.HarmaThr2.setValue(0.9)

        self.PowerThr = QDoubleSpinBox()
        self.PowerThr.setRange(0.0,2.0)
        self.PowerThr.setSingleStep(0.1)
        self.PowerThr.setValue(1.0)

        self.Fundminfreqlabel = QLabel("Min Frequency")
        self.Fundminfreq = QLineEdit()
        self.Fundminfreq.setText('100')
        self.Fundminperiodslabel = QLabel("Min Number of periods")
        self.Fundminperiods = QSpinBox()
        self.Fundminperiods.setRange(1,10)
        self.Fundminperiods.setValue(3)
        self.Fundthrlabel = QLabel("Threshold")
        self.Fundthr = QDoubleSpinBox()
        self.Fundthr.setRange(0.1,1.0)
        self.Fundthr.setDecimals(1)
        self.Fundthr.setValue(0.5)
        self.Fundwindowlabel = QLabel("Window size (will be rounded up as appropriate)")
        self.Fundwindow = QSpinBox()
        self.Fundwindow.setRange(300,5000)
        self.Fundwindow.setSingleStep(500)
        self.Fundwindow.setValue(1000)

        self.medThr = QDoubleSpinBox()
        self.medThr.setRange(0.2,6)
        self.medThr.setSingleStep(1)
        self.medThr.setDecimals(1)
        self.medThr.setValue(3)

        self.ecThr = QDoubleSpinBox()
        self.ecThr.setRange(0.001,6)
        self.ecThr.setSingleStep(1)
        self.ecThr.setDecimals(3)
        self.ecThr.setValue(1)

        self.FIRThr1 = QDoubleSpinBox()
        self.FIRThr1.setRange(0.0,1.0)
        self.FIRThr1.setSingleStep(0.05)
        self.FIRThr1.setValue(0.1)

        Box = QVBoxLayout()
        Box.addWidget(self.algs)
        # Labels
        self.amplabel = QLabel("Set threshold amplitude")
        Box.addWidget(self.amplabel)

        self.Harmalabel = QLabel("Set decibal threshold")
        Box.addWidget(self.Harmalabel)
        self.Harmalabel.hide()

        self.Onsetslabel = QLabel("Onsets: No parameters")
        Box.addWidget(self.Onsetslabel)
        self.Onsetslabel.hide()

        self.medlabel = QLabel("Set median threshold")
        Box.addWidget(self.medlabel)
        self.medlabel.hide()

        self.eclabel = QLabel("Set energy curve threshold")
        Box.addWidget(self.eclabel)
        self.eclabel.hide()
        self.ecthrtype = [QRadioButton("N standard deviations"), QRadioButton("Threshold")]

        self.wavlabel = QLabel("Wavelets")
        self.depthlabel = QLabel("Depth of wavelet packet decomposition")
        #self.depthchoice = QCheckBox()
        #self.connect(self.depthchoice, SIGNAL('clicked()'), self.depthclicked)
        self.depth = QSpinBox()
        self.depth.setRange(1,10)
        self.depth.setSingleStep(1)
        self.depth.setValue(5)

        self.thrtypelabel = QLabel("Type of thresholding")
        self.thrtype = [QRadioButton("Soft"), QRadioButton("Hard")]
        self.thrtype[0].setChecked(True)

        self.thrlabel = QLabel("Multiplier of std dev for threshold")
        self.thr = QSpinBox()
        self.thr.setRange(1,10)
        self.thr.setSingleStep(1)
        self.thr.setValue(5)

        self.waveletlabel = QLabel("Type of wavelet")
        self.wavelet = QComboBox()
        self.wavelet.addItems(["dmey","db2","db5","haar"])
        self.wavelet.setCurrentIndex(0)

        self.blabel = QLabel("Start and end points of the band for bandpass filter")
        self.start = QLineEdit()
        self.start.setText('1000')
        self.end = QLineEdit()
        self.end.setText('7500')
        self.blabel2 = QLabel("Check if not using bandpass")
        self.bandchoice = QCheckBox()
        self.connect(self.bandchoice, SIGNAL('clicked()'), self.bandclicked)


        Box.addWidget(self.wavlabel)
        self.wavlabel.hide()
        Box.addWidget(self.depthlabel)
        self.depthlabel.hide()
        #Box.addWidget(self.depthchoice)
        #self.depthchoice.hide()
        Box.addWidget(self.depth)
        self.depth.hide()

        Box.addWidget(self.thrtypelabel)
        self.thrtypelabel.hide()
        Box.addWidget(self.thrtype[0])
        self.thrtype[0].hide()
        Box.addWidget(self.thrtype[1])
        self.thrtype[1].hide()

        Box.addWidget(self.thrlabel)
        self.thrlabel.hide()
        Box.addWidget(self.thr)
        self.thr.hide()

        Box.addWidget(self.waveletlabel)
        self.waveletlabel.hide()
        Box.addWidget(self.wavelet)
        self.wavelet.hide()

        Box.addWidget(self.blabel)
        self.blabel.hide()
        Box.addWidget(self.start)
        self.start.hide()
        Box.addWidget(self.end)
        self.end.hide()
        Box.addWidget(self.blabel2)
        self.blabel2.hide()
        Box.addWidget(self.bandchoice)
        self.bandchoice.hide()

        Box.addWidget(self.ampThr)
        Box.addWidget(self.HarmaThr1)
        Box.addWidget(self.HarmaThr2)
        self.HarmaThr1.hide()
        self.HarmaThr2.hide()
        Box.addWidget(self.PowerThr)
        self.PowerThr.hide()

        Box.addWidget(self.medThr)
        self.medThr.hide()
        for i in range(len(self.ecthrtype)):
            Box.addWidget(self.ecthrtype[i])
            self.ecthrtype[i].hide()
        Box.addWidget(self.ecThr)
        self.ecThr.hide()

        Box.addWidget(self.FIRThr1)
        self.FIRThr1.hide()

        Box.addWidget(self.Fundminfreqlabel)
        self.Fundminfreqlabel.hide()
        Box.addWidget(self.Fundminfreq)
        self.Fundminfreq.hide()
        Box.addWidget(self.Fundminperiodslabel)
        self.Fundminperiodslabel.hide()
        Box.addWidget(self.Fundminperiods)
        self.Fundminperiods.hide()
        Box.addWidget(self.Fundthrlabel)
        self.Fundthrlabel.hide()
        Box.addWidget(self.Fundthr)
        self.Fundthr.hide()
        Box.addWidget(self.Fundwindowlabel)
        self.Fundwindowlabel.hide()
        Box.addWidget(self.Fundwindow)
        self.Fundwindow.hide()

        Box.addWidget(self.activate)
        #Box.addWidget(self.save)

        # Now put everything into the frame
        self.setLayout(Box)

    def changeBoxes(self,alg):
        # This does the hiding and showing of the options as the algorithm changes
        if self.prevAlg == "Amplitude":
            self.amplabel.hide()
            self.ampThr.hide()
        elif self.prevAlg == "Energy Curve":
            self.eclabel.hide()
            self.ecThr.hide()
            for i in range(len(self.ecthrtype)):
                self.ecthrtype[i].hide()
            #self.ecThr.hide()
        elif self.prevAlg == "Harma":
            self.Harmalabel.hide()
            self.HarmaThr1.hide()
            self.HarmaThr2.hide()
        elif self.prevAlg == "Power":
            self.PowerThr.hide()
        elif self.prevAlg == "Median Clipping":
            self.medlabel.hide()
            self.medThr.hide()
        elif self.prevAlg == "Fundamental Frequency":
            self.Fundminfreq.hide()
            self.Fundminperiods.hide()
            self.Fundthr.hide()
            self.Fundwindow.hide()
            self.Fundminfreqlabel.hide()
            self.Fundminperiodslabel.hide()
            self.Fundthrlabel.hide()
            self.Fundwindowlabel.hide()
        elif self.prevAlg == "Onsets":
            self.Onsetslabel.hide()
        elif self.prevAlg == "FIR":
            self.FIRThr1.hide()
        else:
            self.wavlabel.hide()
            self.depthlabel.hide()
            self.depth.hide()
            #self.depthchoice.hide()
            self.thrtypelabel.hide()
            self.thrtype[0].hide()
            self.thrtype[1].hide()
            self.thrlabel.hide()
            self.thr.hide()
            self.waveletlabel.hide()
            self.wavelet.hide()
            self.blabel.hide()
            self.start.hide()
            self.end.hide()
            self.blabel2.hide()
            self.bandchoice.hide()
        self.prevAlg = str(alg)

        if str(alg) == "Amplitude":
            self.amplabel.show()
            self.ampThr.show()
        elif str(alg) == "Energy Curve":
            self.eclabel.show()
            self.ecThr.show()
            for i in range(len(self.ecthrtype)):
                self.ecthrtype[i].show()
            self.ecThr.show()
        elif str(alg) == "Harma":
            self.Harmalabel.show()
            self.HarmaThr1.show()
            self.HarmaThr2.show()
        elif str(alg) == "Power":
            self.PowerThr.show()
        elif str(alg) == "Median Clipping":
            self.medlabel.show()
            self.medThr.show()
        elif str(alg) == "Fundamental Frequency":
            self.Fundminfreq.show()
            self.Fundminperiods.show()
            self.Fundthr.show()
            self.Fundwindow.show()
            self.Fundminfreqlabel.show()
            self.Fundminperiodslabel.show()
            self.Fundthrlabel.show()
            self.Fundwindowlabel.show()
        elif str(alg) == "Onsets":
            self.Onsetslabel.show()
        elif str(alg) == "FIR":
            self.FIRThr1.show()
        else:
            #"Wavelets"
            self.wavlabel.show()
            self.depthlabel.show()
            #self.depthchoice.show()
            self.depth.show()
            self.thrtypelabel.show()
            self.thrtype[0].show()
            self.thrtype[1].show()
            self.thrlabel.show()
            self.thr.show()
            self.waveletlabel.show()
            self.wavelet.show()
            self.blabel.show()
            self.start.show()
            self.end.show()
            self.blabel2.show()
            self.bandchoice.show()

    def bandclicked(self):
        # TODO: Can they be grayed out?
        self.start.setEnabled(not self.start.isEnabled())
        self.end.setEnabled(not self.end.isEnabled())

    def getValues(self):
        return [self.algs.currentText(),self.ampThr.text(),self.medThr.text(),self.HarmaThr1.text(),self.HarmaThr2.text(),self.PowerThr.text(),self.Fundminfreq.text(),self.Fundminperiods.text(),self.Fundthr.text(),self.Fundwindow.text(),self.FIRThr1.text(),self.depth.text(),self.thrtype[0].isChecked(),self.thr.text(),self.wavelet.currentText(),self.bandchoice.isChecked(),self.start.text(),self.end.text()]

#======
class Denoise(QDialog):
    # Class for the denoising dialog box
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Denoising Options')

        self.algs = QComboBox()
        self.algs.addItems(["Wavelets","Bandpass", "Wavelets --> Bandpass","Bandpass --> Wavelets","Median Filter"])
        self.algs.currentIndexChanged[QString].connect(self.changeBoxes)
        self.prevAlg = "Wavelets"

        # Wavelet: Depth of tree, threshold type, threshold multiplier, wavelet
        self.wavlabel = QLabel("Wavelets")
        self.depthlabel = QLabel("Depth of wavelet packet decomposition (or tick box to use best)")
        self.depthchoice = QCheckBox()
        self.connect(self.depthchoice, SIGNAL('clicked()'), self.depthclicked)
        self.depth = QSpinBox()
        self.depth.setRange(1,10)
        self.depth.setSingleStep(1)
        self.depth.setValue(5)

        self.thrtypelabel = QLabel("Type of thresholding")
        self.thrtype = [QRadioButton("Soft"), QRadioButton("Hard")]
        self.thrtype[0].setChecked(True)

        self.thrlabel = QLabel("Multiplier of std dev for threshold")
        self.thr = QDoubleSpinBox()
        self.thr.setRange(1,10)
        self.thr.setSingleStep(0.5)
        self.thr.setValue(4.0)

        self.waveletlabel = QLabel("Type of wavelet")
        self.wavelet = QComboBox()
        self.wavelet.addItems(["dmey","db2","db5","haar"])
        self.wavelet.setCurrentIndex(0)

        # Median: width of filter
        self.medlabel = QLabel("Median Filter")
        self.widthlabel = QLabel("Half width of median filter")
        self.width = QSpinBox()
        self.width.setRange(1,101)
        self.width.setSingleStep(1)
        self.width.setValue(11)

        # Bandpass: start and end
        self.bandlabel = QLabel("Bandpass Filter")
        self.wblabel = QLabel("Wavelets and Bandpass Filter")
        self.blabel = QLabel("Start and end points of the band")
        self.start = QLineEdit(self)
        self.start.setText('1000')
        self.end = QLineEdit(self)
        self.end.setText('7500')

        # Want combinations of these too!

        self.activate = QPushButton("Denoise")
        self.undo = QPushButton("Undo")
        self.save = QPushButton("Save Denoised Sound")
        #self.connect(self.undo, SIGNAL('clicked()'), self.undo)
        Box = QVBoxLayout()
        Box.addWidget(self.algs)

        Box.addWidget(self.wavlabel)
        Box.addWidget(self.depthlabel)
        Box.addWidget(self.depthchoice)
        Box.addWidget(self.depth)

        Box.addWidget(self.thrtypelabel)
        Box.addWidget(self.thrtype[0])
        Box.addWidget(self.thrtype[1])

        Box.addWidget(self.thrlabel)
        Box.addWidget(self.thr)

        Box.addWidget(self.waveletlabel)
        Box.addWidget(self.wavelet)

        # Median: width of filter
        Box.addWidget(self.medlabel)
        self.medlabel.hide()
        Box.addWidget(self.widthlabel)
        self.widthlabel.hide()
        Box.addWidget(self.width)
        self.width.hide()

        # Bandpass: start and end
        Box.addWidget(self.bandlabel)
        self.bandlabel.hide()
        Box.addWidget(self.wblabel)
        self.wblabel.hide()
        Box.addWidget(self.blabel)
        self.blabel.hide()
        Box.addWidget(self.start)
        self.start.hide()
        Box.addWidget(self.end)
        self.end.hide()

        Box.addWidget(self.activate)
        Box.addWidget(self.undo)
        Box.addWidget(self.save)

        # Now put everything into the frame
        self.setLayout(Box)

    def changeBoxes(self,alg):
        # This does the hiding and showing of the options as the algorithm changes
        if self.prevAlg == "Wavelets":
            self.wavlabel.hide()
            self.depthlabel.hide()
            self.depth.hide()
            self.depthchoice.hide()
            self.thrtypelabel.hide()
            self.thrtype[0].hide()
            self.thrtype[1].hide()
            self.thrlabel.hide()
            self.thr.hide()
            self.waveletlabel.hide()
            self.wavelet.hide()
        elif self.prevAlg == "Bandpass --> Wavelets":
            self.wblabel.hide()
            self.depthlabel.hide()
            self.depth.hide()
            self.depthchoice.hide()
            self.thrtypelabel.hide()
            self.thrtype[0].hide()
            self.thrtype[1].hide()
            self.thrlabel.hide()
            self.thr.hide()
            self.waveletlabel.hide()
            self.wavelet.hide()
            self.blabel.hide()
            self.start.hide()
            self.end.hide()
            self.medlabel.hide()
            self.widthlabel.hide()
            self.width.hide()
        elif self.prevAlg == "Wavelets --> Bandpass":
            self.wblabel.hide()
            self.depthlabel.hide()
            self.depth.hide()
            self.depthchoice.hide()
            self.thrtypelabel.hide()
            self.thrtype[0].hide()
            self.thrtype[1].hide()
            self.thrlabel.hide()
            self.thr.hide()
            self.waveletlabel.hide()
            self.wavelet.hide()
            self.blabel.hide()
            self.start.hide()
            self.end.hide()
            self.medlabel.hide()
            self.widthlabel.hide()
            self.width.hide()
        elif self.prevAlg == "Bandpass" or self.prevAlg == "Butterworth Bandpass":
            self.bandlabel.hide()
            self.blabel.hide()
            self.start.hide()
            self.end.hide()
        else:
            # Median filter
            self.medlabel.hide()
            self.widthlabel.hide()
            self.width.hide()

        self.prevAlg = str(alg)
        if str(alg) == "Wavelets":
            self.wavlabel.show()
            self.depthlabel.show()
            self.depthchoice.show()
            self.depth.show()
            self.thrtypelabel.show()
            self.thrtype[0].show()
            self.thrtype[1].show()
            self.thrlabel.show()
            self.thr.show()
            self.waveletlabel.show()
            self.wavelet.show()
        elif str(alg) == "Wavelets --> Bandpass":
            # self.wblabel.show()
            self.depthlabel.show()
            self.depthchoice.show()
            self.depth.show()
            self.thrtypelabel.show()
            self.thrtype[0].show()
            self.thrtype[1].show()
            self.thrlabel.show()
            self.thr.show()
            self.waveletlabel.show()
            self.wavelet.show()
            self.blabel.show()
            self.start.show()
            self.end.show()
        elif str(alg) == "Bandpass --> Wavelets":
            # self.wblabel.show()
            self.depthlabel.show()
            self.depthchoice.show()
            self.depth.show()
            self.thrtypelabel.show()
            self.thrtype[0].show()
            self.thrtype[1].show()
            self.thrlabel.show()
            self.thr.show()
            self.waveletlabel.show()
            self.wavelet.show()
            self.blabel.show()
            self.start.show()
            self.end.show()
        elif str(alg) == "Bandpass" or str(alg) == "Butterworth Bandpass":
            self.bandlabel.show()
            self.start.show()
            self.end.show()
        else:
            #"Median filter"
            self.medlabel.show()
            self.widthlabel.show()
            self.width.show()

    def depthclicked(self):
        self.depth.setEnabled(not self.depth.isEnabled())

    def getValues(self):
        return [self.algs.currentText(),self.depthchoice.isChecked(),self.depth.text(),self.thrtype[0].isChecked(),self.thr.text(),self.wavelet.currentText(),self.start.text(),self.end.text(),self.width.text()]

#======
class HumanClassify1(QDialog):
    # This dialog is different to the others. The aim is to check (or ask for) classifications for segments.
    # This version shows a single segment at a time, working through all the segments.
    # So it needs to show a segment, and its current label
    # TODO: Select the right option in the list
    # TODO: Deal with changes
    # TODO: Make the plot the correct size

    def __init__(self, seg, label, lut, colourStart, colourEnd, cmapInverted, birdList, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Check Classifications')
        self.frame = QWidget()

        self.lut = lut
        self.colourStart = colourStart
        self.colourEnd = colourEnd
        self.cmapInverted = cmapInverted
        self.label = label
        self.saveConfig = False

        # Set up the plot window, then the right and wrong buttons, and a close button
        self.wPlot = pg.GraphicsLayoutWidget()
        self.pPlot = self.wPlot.addViewBox(enableMouse=False, row=0, col=1)
        self.plot = pg.ImageItem()
        self.pPlot.addItem(self.plot)

        self.species = QLabel(self.label)

        # The buttons to move through the overview
        self.correct = QtGui.QToolButton()
        self.correct.setIcon(QtGui.QIcon('Resources/tick.png'))
        # self.wrong = QtGui.QToolButton()
        # self.wrong.setIcon(QtGui.QIcon('Resources/cross.png'))

        self.close = QPushButton("Close")

        # An array of radio buttons and a list and a text entry box
        # Create an array of radio buttons for the most common birds (2 columns of 10 choices)
        self.birds1 = []
        for item in birdList[:10]:
            self.birds1.append(QRadioButton(item))
        self.birds2 = []
        for item in birdList[10:19]:
            self.birds2.append(QRadioButton(item))
        self.birds2.append(QRadioButton('Other'))

        for i in xrange(len(self.birds1)):
            self.birds1[i].setEnabled(True)
            self.connect(self.birds1[i], SIGNAL("clicked()"), self.radioBirdsClicked)
        for i in xrange(len(self.birds2)):
            self.birds2[i].setEnabled(True)
            self.connect(self.birds2[i], SIGNAL("clicked()"), self.radioBirdsClicked)

        # The list of less common birds
        self.birdList = QListWidget(self)
        self.birdList.setMaximumWidth(150)
        for item in birdList[20:]:
            self.birdList.addItem(item)
        self.birdList.sortItems()
        # Explicitly add "Other" option in
        self.birdList.insertItem(0, 'Other')

        self.connect(self.birdList, SIGNAL("itemClicked(QListWidgetItem*)"), self.listBirdsClicked)
        self.birdList.setEnabled(False)

        # This is the text box for missing birds
        self.tbox = QLineEdit(self)
        self.tbox.setMaximumWidth(150)
        self.connect(self.tbox, SIGNAL('editingFinished()'), self.birdTextEntered)
        self.tbox.setEnabled(False)

        self.close = QPushButton("Done")
        self.connect(self.close, SIGNAL("clicked()"), self.accept)

        # The layouts
        birds1Layout = QVBoxLayout()
        for i in xrange(len(self.birds1)):
            birds1Layout.addWidget(self.birds1[i])

        birds2Layout = QVBoxLayout()
        for i in xrange(len(self.birds2)):
            birds2Layout.addWidget(self.birds2[i])

        birdListLayout = QVBoxLayout()
        birdListLayout.addWidget(self.birdList)
        birdListLayout.addWidget(QLabel("If bird isn't in list, select Other"))
        birdListLayout.addWidget(QLabel("Type below, Return at end"))
        birdListLayout.addWidget(self.tbox)

        hboxBirds = QHBoxLayout()
        hboxBirds.addLayout(birds1Layout)
        hboxBirds.addLayout(birds2Layout)
        hboxBirds.addLayout(birdListLayout)

        # The layouts
        hboxButtons = QHBoxLayout()
        hboxButtons.addWidget(self.correct)
        # hboxButtons.addWidget(self.wrong)
        hboxButtons.addWidget(self.close)

        vboxFull = QVBoxLayout()
        vboxFull.addWidget(self.wPlot)
        vboxFull.addWidget(self.species)
        vboxFull.addLayout(hboxBirds)
        vboxFull.addLayout(hboxButtons)
        vboxFull.addWidget(self.close)

        self.setLayout(vboxFull)
        self.setImage(seg, self.label)

    def setImage(self, seg, label):
        self.plot.setImage(seg)
        self.plot.setLookupTable(self.lut)
        if self.cmapInverted:
            self.plot.setLevels([self.colourEnd, self.colourStart])
        else:
            self.plot.setLevels([self.colourStart, self.colourEnd])
        self.species.setText(label)

    def radioBirdsClicked(self):
        # Listener for when the user selects a radio button
        # Update the text and store the data
        for button in self.birds1 + self.birds2:
            if button.isChecked():
                if button.text() == "Other":
                    self.birdList.setEnabled(True)
                else:
                    self.birdList.setEnabled(False)
                    self.label = str(button.text())

    def listBirdsClicked(self, item):
        # Listener for clicks in the listbox of birds
        if (item.text() == "Other"):
            self.tbox.setEnabled(True)
        else:
            # Save the entry
            self.label = str(item.text())

    def birdTextEntered(self):
        # Listener for the text entry in the bird list
        # Check text isn't already in the listbox, and add if not
        # Doesn't sort the list, but will when program is closed
        item = self.birdList.findItems(self.tbox.text(), Qt.MatchExactly)
        if item:
            pass
        else:
            self.birdList.addItem(self.tbox.text())
        self.label = str(self.tbox.text())
        self.saveConfig = True
        self.tbox.setEnabled(False)

    def getValues(self):
        return [self.label, self.saveConfig]

# ======
# class CorrectHumanClassify1(QDialog):
#     # This is to correct the classification of those that the program got wrong
#     def __init__(self, seg, bb1, bb2, bb3, parent=None):
#         QDialog.__init__(self, parent)
#         self.setWindowTitle('Correct Classification')
#         self.frame = QWidget()
#
#         self.saveConfig = False
#
#         self.wPlot = pg.GraphicsLayoutWidget()
#         self.pPlot = self.wPlot.addViewBox(enableMouse=False,row=0,col=1)
#         self.plot = pg.ImageItem()
#         self.pPlot.addItem(self.plot)
#
#         # An array of radio buttons and a list and a text entry box
#         # Create an array of radio buttons for the most common birds (2 columns of 10 choices)
#         self.birds1 = []
#         for item in bb1:
#             self.birds1.append(QRadioButton(item))
#         self.birds2 = []
#         for item in bb2:
#             self.birds2.append(QRadioButton(item))
#
#         for i in xrange(len(self.birds1)):
#             self.birds1[i].setEnabled(True)
#             self.connect(self.birds1[i], SIGNAL("clicked()"), self.radioBirdsClicked)
#         for i in xrange(len(self.birds2)):
#             self.birds2[i].setEnabled(True)
#             self.connect(self.birds2[i], SIGNAL("clicked()"), self.radioBirdsClicked)
#
#         # The list of less common birds
#         self.birdList = QListWidget(self)
#         self.birdList.setMaximumWidth(150)
#         for item in bb3:
#             self.birdList.addItem(item)
#         self.birdList.sortItems()
#         # Explicitly add "Other" option in
#         self.birdList.insertItem(0,'Other')
#
#         self.connect(self.birdList, SIGNAL("itemClicked(QListWidgetItem*)"), self.listBirdsClicked)
#         self.birdList.setEnabled(False)
#
#         # This is the text box for missing birds
#         self.tbox = QLineEdit(self)
#         self.tbox.setMaximumWidth(150)
#         self.connect(self.tbox, SIGNAL('editingFinished()'), self.birdTextEntered)
#         self.tbox.setEnabled(False)
#
#         self.close = QPushButton("Done")
#         self.connect(self.close, SIGNAL("clicked()"), self.accept)
#
#         # The layouts
#         birds1Layout = QVBoxLayout()
#         for i in xrange(len(self.birds1)):
#             birds1Layout.addWidget(self.birds1[i])
#
#         birds2Layout = QVBoxLayout()
#         for i in xrange(len(self.birds2)):
#             birds2Layout.addWidget(self.birds2[i])
#
#         birdListLayout = QVBoxLayout()
#         birdListLayout.addWidget(self.birdList)
#         birdListLayout.addWidget(QLabel("If bird isn't in list, select Other"))
#         birdListLayout.addWidget(QLabel("Type below, Return at end"))
#         birdListLayout.addWidget(self.tbox)
#
#         hbox = QHBoxLayout()
#         hbox.addLayout(birds1Layout)
#         hbox.addLayout(birds2Layout)
#         hbox.addLayout(birdListLayout)
#
#         vboxFull = QVBoxLayout()
#         vboxFull.addWidget(self.wPlot)
#         vboxFull.addLayout(hbox)
#         vboxFull.addWidget(self.close)
#
#         self.setLayout(vboxFull)
#         self.makefig(seg)
#
#     def makefig(self,seg):
#         self.plot.setImage(seg)
#
#     def radioBirdsClicked(self):
#         # Listener for when the user selects a radio button
#         # Update the text and store the data
#         for button in self.birds1+self.birds2:
#             if button.isChecked():
#                 if button.text()=="Other":
#                     self.birdList.setEnabled(True)
#                 else:
#                     self.birdList.setEnabled(False)
#                     self.label = str(button.text())
#
#     def listBirdsClicked(self, item):
#         # Listener for clicks in the listbox of birds
#         if (item.text() == "Other"):
#             self.tbox.setEnabled(True)
#         else:
#             # Save the entry
#             self.label = str(item.text())
#
#     def birdTextEntered(self):
#         # Listener for the text entry in the bird list
#         # Check text isn't already in the listbox, and add if not
#         # Doesn't sort the list, but will when program is closed
#         item = self.birdList.findItems(self.tbox.text(),Qt.MatchExactly)
#         if item:
#             pass
#         else:
#             self.birdList.addItem(self.tbox.text())
#         self.label = str(self.tbox.text())
#         self.saveConfig=True
#         self.tbox.setEnabled(False)
#
#     # static method to create the dialog and return the correct label
#     @staticmethod
#     def getValues(seg, bb1, bb2, bb3,parent=None):
#         dialog = CorrectHumanClassify1(seg, bb1, bb2, bb3,parent)
#         result = dialog.exec_()
#         return dialog.label, dialog.saveConfig
#
#     def setImage(self,seg,label):
#         self.plot.setImage(seg)

#======
class HumanClassify2(QDialog):
    # This dialog is different to the others. The aim is to check (or ask for) classifications for segments.
    # This version gets *12* at a time, and put them all out together on buttons, and their labels.
    # It could be all the same species, or the ones that it is unsure about, or whatever.

    # TODO: First thing is to add a dialog that asks what you want -- all calls, a species, uncertain ones, whatever
    # Decide what you want to do with it. I think that it is about saying which ones are right or wrong, not correcting them.
    # Or just getting labels, or something
    def __init__(self, sg, segments, label, sampleRate, incr, lut, colourStart, colourEnd, cmapInverted, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Check Classifications')
        self.frame = QWidget()

        self.sampleRate = sampleRate
        self.incr = incr
        self.lut = lut
        self.colourStart = colourStart
        self.colourEnd = colourEnd
        self.cmapInverted = cmapInverted

        # Seems that image is backwards?
        self.sg = np.fliplr(sg)
        self.segments = segments
        self.firstSegment = 0

        # TODO: Add a label with instructions
        # TODO: More next button turn into a close and then close the window at the end

        species = QLabel(label)
        next = QPushButton("Next")
        self.connect(next, SIGNAL("clicked()"), self.next)

        # TODO: Decide on these sizes
        self.width = 3
        self.height = 1
        self.grid = QGridLayout()

        self.makeButtons()

        vboxFull = QVBoxLayout()
        vboxFull.addWidget(species)
        vboxFull.addLayout(self.grid)
        vboxFull.addWidget(next)
        self.setLayout(vboxFull)

    def makeButtons(self):
        positions = [(i, j) for i in range(self.height) for j in range(self.width)]
        images = []
        segRemain = len(self.segments) - self.firstSegment
        print segRemain, self.firstSegment

        if segRemain < self.width * self.height:
            for i in range(segRemain):
                ind = i + self.firstSegment
                if (self.segments[ind][2] == 0) and (self.segments[ind][3] == 0):
                    x1 = int(self.convertAmpltoSpec(self.segments[ind][0]))
                    x2 = int(self.convertAmpltoSpec(self.segments[ind][1]))
                    x3 = 0
                    x4 = np.shape(self.sg)[1]
                else:
                    x1 = int(self.segments[ind][0])
                    x2 = int(self.segments[ind][1])
                    x3 = int(self.segments[ind][2])
                    x4 = int(self.segments[ind][3])
                images.append(self.setImage(self.sg[x1:x2, x3:x4]))
            for i in range(segRemain, self.width * self.height):
                images.append([None, None])
        else:
            for i in range(self.width * self.height):
                ind = i + self.firstSegment
                if (self.segments[ind][2] == 0) and (self.segments[ind][3] == 0):
                    x1 = int(self.convertAmpltoSpec(self.segments[ind][0]))
                    x2 = int(self.convertAmpltoSpec(self.segments[ind][1]))
                    x3 = 0
                    x4 = np.shape(self.sg)[1]
                else:
                    x1 = int(self.segments[ind][0])
                    x2 = int(self.segments[ind][1])
                    x3 = int(self.segments[ind][2])
                    x4 = int(self.segments[ind][3])
                images.append(self.setImage(self.sg[x1:x2, x3:x4]))
        self.buttons = []
        for position, im in zip(positions, images):
            if im[0] is not None:
                self.buttons.append(SupportClasses.PicButton(position[0] * self.width + position[1], im[0], im[1]))
                self.grid.addWidget(self.buttons[-1], *position)

    def convertAmpltoSpec(self, x):
        return x * self.sampleRate / self.incr

    def setImage(self, seg):
        if self.cmapInverted:
            im, alpha = fn.makeARGB(seg, lut=self.lut, levels=[self.colourEnd, self.colourStart])
        else:
            im, alpha = fn.makeARGB(seg, lut=self.lut, levels=[self.colourStart, self.colourEnd])
        im1 = fn.makeQImage(im, alpha)

        if self.cmapInverted:
            im, alpha = fn.makeARGB(seg, lut=self.lut, levels=[self.colourStart, self.colourEnd])
        else:
            im, alpha = fn.makeARGB(seg, lut=self.lut, levels=[self.colourEnd, self.colourStart])

        im2 = fn.makeQImage(im, alpha)

        return [im1, im2]

    def next(self):
        # TODO: Make this close the dialog
        if (len(self.segments) - self.firstSegment) < self.width * self.height:
            # Have finished
            return
        else:
            self.firstSegment += self.width * self.height
            if self.firstSegment != len(self.segments):
                for i in range(self.width * self.height):
                    self.grid.removeWidget(self.buttons[i])
                self.makeButtons()
            else:
                return