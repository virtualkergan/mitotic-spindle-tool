import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                               QSpinBox, QTableView, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QSizePolicy,
                               QFileDialog, QSplitter, QFrame, QSplitterHandle,
                               QAbstractItemView)
from PySide6.QtGui import (QPixmap, QFont, QPainter, QBrush, QGradient,
                           QTransform)
from PySide6.QtCore import Qt, QDir, QAbstractTableModel, QEvent
import tiffFunctions as tiffF
import threshFunctions as threshF
import curveFitData as cFD
import plotSpindle as pS
from numpy import zeros

# subclass QMainWindow to create a custom MainWindow
class MainWindow(QMainWindow):

    # set up the MainWindow
    def __init__(self):

        # allow the QMainWindow to initialize
        super().__init__()

        self.setWindowTitle("Mitotic Spindle Image Analysis")
        
        # Update the version for new releases
        versionNumber = "v1.0.1"
        
        # keep track of the open file name
        self.fileName = None

        # bad frames reported by the user
        self.tossedFrames = []

        # record whether it is starting in light or dark mode
        self.isDarkMode = self.isComputerDarkMode()   
        
        # keep track of whether the preview is the default or not
        self.isPreviewCleared = True

        # create accessible widgets
        self.importLabel = QLabel("Single Z")
        self.tiffButton = QPushButton(".tiff")

        self.totalFrameLabel = QLabel("# of Frames")
        self.totalFrameValue = QLabel("0")
        self.totalFrameValue.setAlignment(Qt.AlignRight)
        self.frameLabel = QLabel("Frame #")
        self.frameValue = QSpinBox()
        self.frameValue.setAlignment(Qt.AlignRight)
        self.frameValue.setMinimum(1)
        self.frameValue.setMaximum(1)

        self.threshLabel = QLabel("Threshold")
        self.threshValue = QSpinBox()
        self.threshValue.setAlignment(Qt.AlignRight)
        self.threshValue.setSingleStep(50)
        self.threshValue.setMinimum(0)
        self.threshValue.setMaximum(65535)
        self.threshValue.setValue(1000)

        self.gOLIterationsLabel = QLabel("GOL Iterations")
        self.gOLIterationsValue = QSpinBox()
        self.gOLIterationsValue.setAlignment(Qt.AlignRight)
        self.gOLIterationsValue.setMinimum(1)
        self.gOLIterationsValue.setMaximum(5)

        self.gOLFactorLabel = QLabel("GOL Factor")
        self.gOLFactorValue = QSpinBox()
        self.gOLFactorValue.setAlignment(Qt.AlignRight)
        self.gOLFactorValue.setMinimum(0)
        self.gOLFactorValue.setMaximum(8)
        self.gOLFactorValue.setValue(4)

        self.previewButton = QPushButton("Preview")
        self.addButton = QPushButton("Add")
        self.tossButton = QPushButton("Toss")
        self.tossButton.setSizePolicy(QSizePolicy.Maximum,
                                           QSizePolicy.Maximum)
        self.exportButton = QPushButton("Export")

        self.dataTableView = QTableView()
        self.dataTableView.setSelectionMode(QAbstractItemView.NoSelection)
        self.dataTableArray = None

        self.backShade = self.dataTableView.palette().base().color().value()

        imageLabel = QLabel("Source")
        imageMap = QPixmap(tiffF.defaultPix(self.backShade))
        self.imagePixLabel = PixLabel()
        self.imagePixLabel.setPixmap(imageMap)

        thresholdImageLabel = QLabel("Threshold")
        threshMap = QPixmap(tiffF.defaultPix(self.backShade))
        self.threshPixLabel = PixLabel()
        self.threshPixLabel.setPixmap(threshMap)

        previewImageLabel = QLabel("Preview")
        previewMap = QPixmap(tiffF.defaultPix(self.backShade))
        self.previewPixLabel = PixLabel()
        self.previewPixLabel.setPixmap(previewMap)

        imageLabels = (imageLabel, thresholdImageLabel, previewImageLabel)
        imagePixLabels = (self.imagePixLabel, self.threshPixLabel, 
                          self.previewPixLabel)
        
        imageSplitter = SplitterWithHandles(Qt.Horizontal)
        rightSplitter = SplitterWithHandles(Qt.Vertical)

        # create section titles with modified font
        importTitle = QLabel("Import")
        thresholdTitle = QLabel("Threshold")
        dataTitle = QLabel("Record")
        imagesTitle = QLabel("Images")
        tableTitle = QLabel("Data")

        sectionTitles = (importTitle, thresholdTitle, dataTitle,
                  imagesTitle, tableTitle)

        titleFont = importTitle.font()
        titleFont.setCapitalization(QFont.AllUppercase)

        for title in sectionTitles:
            # change the font and look of the titles
            title.setStyleSheet("color:#777777")
            title.setFont(titleFont)

        # version number (could move this up to a menu in the future)
        versionLabel = QLabel(versionNumber)
        versionLabel.setStyleSheet("color:#777777")

        # set default size hint for buttons and spacing
        # based off of QButton with the text "Toss Frame Data"
        defaultSize = QPushButton("Toss Frame Data").sizeHint()

        # create container widgets and layouts
        centralWidget = QWidget()
        leftWidget = QWidget()
        importWidget = QWidget()
        thresholdWidget = QWidget()
        bottomLeftWidget = QWidget()
        imageWidget = QWidget()
        thresholdImageWidget = QWidget()
        previewImageWidget = QWidget()
        dataTableWidget = QWidget()

        dividingLine = QFrame()
        dividingLine.setFrameStyle(QFrame.VLine | QFrame.Raised)

        imageWidgets = (imageWidget, thresholdImageWidget, previewImageWidget)

        tempImageWidget = QWidget()
        tempHorizontal = QHBoxLayout()
        tempVertical = QVBoxLayout()
        tempGrid = QGridLayout()
        
        # place widgets in the app
        tempVertical.addWidget(importTitle)
        tempGrid.addWidget(self.importLabel, 0, 0)
        tempGrid.addWidget(self.tiffButton, 0, 1)
        importWidget.setLayout(tempGrid)
        tempGrid = QGridLayout()
        tempVertical.addWidget(importWidget)

        tempVertical.addSpacing(defaultSize.height())
        tempVertical.addWidget(thresholdTitle)
        tempGrid.addWidget(self.totalFrameLabel, 0, 0)
        tempGrid.addWidget(self.totalFrameValue, 0, 1, Qt.AlignRight)
        tempGrid.addWidget(self.frameLabel, 1, 0)
        tempGrid.addWidget(self.frameValue, 1, 1)
        tempGrid.addWidget(self.threshLabel, 2, 0)
        tempGrid.addWidget(self.threshValue, 2, 1)
        tempGrid.addWidget(self.gOLIterationsLabel, 3, 0)
        tempGrid.addWidget(self.gOLIterationsValue, 3, 1)
        tempGrid.addWidget(self.gOLFactorLabel, 4, 0)
        tempGrid.addWidget(self.gOLFactorValue, 4, 1)
        thresholdWidget.setLayout(tempGrid)
        tempGrid = QGridLayout()
        tempVertical.addWidget(thresholdWidget)

        tempVertical.addSpacing(defaultSize.height())
        tempVertical.addWidget(dataTitle)
        tempGrid.addWidget(self.addButton, 0, 0)
        tempGrid.addWidget(self.previewButton, 0, 1)
        tempGrid.addWidget(self.tossButton, 1, 0)
        tempGrid.addWidget(self.exportButton, 1, 1)
        bottomLeftWidget.setLayout(tempGrid)
        tempVertical.addWidget(bottomLeftWidget)
        tempVertical.addStretch()
        tempVertical.addWidget(versionLabel)
        tempGrid = QGridLayout()
        leftWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()

        for i in range(len(imageLabels)):
            tempVertical.addWidget(imageLabels[i],
                               alignment=Qt.AlignLeft | Qt.AlignBottom)
            tempHorizontal.setContentsMargins(0,0,0,0)
            tempHorizontal.addWidget(imagePixLabels[i], alignment=Qt.AlignLeft)
            tempImageWidget.setLayout(tempHorizontal)
            tempHorizontal = QHBoxLayout()
            tempVertical.addWidget(tempImageWidget)
            tempImageWidget = QWidget()
            tempVertical.addStretch()
            imageWidgets[i].setLayout(tempVertical)
            tempVertical = QVBoxLayout()
            imageSplitter.addWidget(imageWidgets[i])
        
        imageSplitterWidget = QWidget()
        tempVertical.addWidget(imagesTitle)
        tempVertical.addWidget(imageSplitter)
        tempVertical.addStretch()
        imageSplitterWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()
        tempVertical.addWidget(tableTitle)
        tempVertical.addWidget(self.dataTableView)
        dataTableWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()

        rightSplitter.addWidget(imageSplitterWidget)
        rightSplitter.addWidget(dataTableWidget)

        tempHorizontal.addWidget(leftWidget)
        tempHorizontal.addWidget(dividingLine)
        tempHorizontal.addWidget(rightSplitter, stretch=1)
        centralWidget.setLayout(tempHorizontal)
        tempHorizontal = QHBoxLayout()

        self.setCentralWidget(centralWidget)

        # set fixed button sizes
        self.tiffButton.setFixedSize(defaultSize)
        self.previewButton.setFixedSize(defaultSize)
        self.addButton.setFixedSize(defaultSize)
        self.tossButton.setFixedSize(defaultSize)
        self.exportButton.setFixedSize(defaultSize)
        
        # connect signals to slots
        self.tiffButton.clicked.connect(self.onInputTiffClicked)

        self.frameValue.textChanged.connect(self.onFrameUpdate)
        self.threshValue.textChanged.connect(self.applyThreshold)
        self.gOLIterationsValue.textChanged.connect(self.applyThreshold)
        self.gOLFactorValue.textChanged.connect(self.applyThreshold)

        self.previewButton.clicked.connect(self.onPreviewClicked)
        self.addButton.clicked.connect(self.onAddDataClicked)
        self.tossButton.clicked.connect(self.onTossDataClicked)
        self.exportButton.clicked.connect(self.onExportDataClicked)

        # center window on the desktop
        def centerApplication(xSize, ySize):
            self.setGeometry(100, 100, xSize, ySize)
            qFrameRect = self.frameGeometry()
            center_point = QApplication.primaryScreen().geometry().center()
            qFrameRect.moveCenter(center_point)
            self.setGeometry(qFrameRect.topLeft().x(),
                             qFrameRect.topLeft().y(),
                             xSize, ySize)
        centerApplication(770, 450)
    
    # handle import .tiff button push
    def onInputTiffClicked(self):

        fileName, filter = QFileDialog.getOpenFileName(
                parent=self, caption='Open .tiff',
                dir=QDir.homePath(), filter='*.tiff;*.tif')
        
        # if the user selected a file successfully
        if fileName:
            self.fileName = fileName
            self.clearThreshAndPreview()
            self.frameValue.setValue(1)
            self.onFrameUpdate()
            numFrames = tiffF.framesInTiff(self.fileName)
            self.frameValue.setMaximum(numFrames)
            self.totalFrameValue.setText(str(numFrames))
            
            # create the data array and place it in the QTableView
            self.dataTableArray = zeros((numFrames, len(cFD.DATA_NAMES)))
            self.dataTableModel = (
                    ImageTableModel(cFD.DATA_NAMES, self.dataTableArray))
            self.dataTableView.setModel(self.dataTableModel)
            self.dataTableView.resizeColumnsToContents()

            # reset the tossed frames for the new image
            self.tossedFrames = []

            # reset input values
            self.frameValue.setValue(1)
            self.threshValue.setValue(1000)
            self.gOLIterationsValue.setValue(1)
            self.gOLFactorValue.setValue(4)

    # handle update of the frame number scroller
    def onFrameUpdate(self):
        self.clearThreshAndPreview()

        self.imagePixLabel.setPixmap(
                tiffF.pixFromTiff(self.fileName, self.frameValue.value() - 1))
        self.imagePixLabel.setImageArr(
                tiffF.arrFromTiff(self.fileName, self.frameValue.value() - 1))
        self.applyThreshold(cleared=True)

    # handle applying the threshold
    def applyThreshold(self, text="", cleared=False):
        if not cleared:
            self.clearThreshAndPreview()

        if self.fileName:
            arr = threshF.applyThreshToArr(self.imagePixLabel.imageArr,
                                            self.threshValue.value(),
                                            self.gOLIterationsValue.value(),
                                            self.gOLFactorValue.value())
            self.threshPixLabel.setPixmap(tiffF.threshPixFromArr(arr))
            self.threshPixLabel.setImageArr(arr)
    
    # handle the preview button press
    def onPreviewClicked(self):
        if self.fileName:
            spindlePlotData, doesSpindleExist = (
                    cFD.spindlePlot(self.imagePixLabel.imageArr, 
                                    self.threshPixLabel.imageArr))
            self.previewPixLabel.setPixmap(pS.plotSpindle(spindlePlotData,
                                                          doesSpindleExist))
            self.isPreviewCleared = False
    
    # handle the add data button press
    def onAddDataClicked(self):

        if self.fileName:
            data, doesSpindleExist = (cFD.spindleMeasurements(
                                            self.imagePixLabel.imageArr,
                                            self.threshPixLabel.imageArr))

            if doesSpindleExist:
                # add the row of data to the data table
                self.dataTableModel.beginResetModel()
                frameIndex = self.frameValue.value() - 1
                for i in range(len(data)):
                    self.dataTableArray[frameIndex, i] = data[i]
                # update the table view
                self.dataTableModel.endResetModel()

                indexOfData = self.dataTableModel.createIndex(frameIndex, 0)
                self.dataTableView.scrollTo(indexOfData)

                self.frameValue.setValue(frameIndex + 2)
    
    # handle the toss data button press
    def onTossDataClicked(self):
        tossedFrame = self.frameValue.value()
        if (tossedFrame not in self.tossedFrames and self.fileName):
            self.tossedFrames.append(tossedFrame)
            self.tossedFrames.sort()
            self.dataTableModel.addTossedRow(tossedFrame)
            self.onAddDataClicked() # this follows previous lab standard
        elif (tossedFrame in self.tossedFrames and self.fileName):
            # "un-tosses" the frame
            self.tossedFrames.remove(tossedFrame)
            self.dataTableModel.removeTossedRow(tossedFrame)
            self.onAddDataClicked()

        if self.fileName:
            self.frameValue.setValue(tossedFrame + 1)

            indexOfData = self.dataTableModel.createIndex(tossedFrame - 1, 0)
            self.dataTableView.scrollTo(indexOfData)
    
    # write the data to a textfile
    def onExportDataClicked(self):
        if self.fileName:

            # prompt the user for the save location and file name
            fileName, filter = QFileDialog.getSaveFileName(
                    parent=self, caption='Export Image Data',
                    dir=QDir.homePath(), filter="*.txt")
            if not fileName:
                return None # cancel the export
            
            with open(fileName, "w", encoding="utf-8") as f:

                for column in range(self.dataTableArray.shape[1]):
                    f.write(F"{cFD.DATA_NAMES[column]}\n")

                    for row in range(self.dataTableArray.shape[0]):
                        f.write(F"{self.dataTableArray[row, column]:.4f}\n")
                
                f.write("Bad Frames\n")
                for frame in self.tossedFrames:
                    f.write(F"{frame}\n")
    
    # slot called anytime the inputs are modified
    def clearThreshAndPreview(self):
        if self.fileName:
            self.threshPixLabel.setPixmap(tiffF.defaultPix(self.backShade))
            self.previewPixLabel.setPixmap(tiffF.defaultPix(self.backShade))
            self.isPreviewCleared = True

    # changes default pixmap color when computer switches color mode
    def changeDefaultPixmaps(self):
        self.backShade = QTableView().palette().base().color().value()
        newPix = tiffF.defaultPix(self.backShade)
        if self.fileName and self.isPreviewCleared:
            # image and thresh have images but not preview
            self.previewPixLabel.setPixmap(newPix)
        elif not self.fileName:
            # no image is loaded (all three images are defaults)
            self.imagePixLabel.setPixmap(newPix)
            self.threshPixLabel.setPixmap(newPix)
            self.previewPixLabel.setPixmap(newPix)
    
    # determines if the application is in dark mode
    def isComputerDarkMode(self):
        aLabel = QLabel("a")
        return (aLabel.palette().color(aLabel.backgroundRole()).black() 
              > aLabel.palette().color(aLabel.foregroundRole()).black())

    # detects when the computer switches to dark or light mode
    def changeEvent(self, event):
        if event.type() == QEvent.ThemeChange:
            isComputerDarkMode = self.isComputerDarkMode()
            if isComputerDarkMode != self.isDarkMode:
                self.isDarkMode = isComputerDarkMode
                self.changeDefaultPixmaps()
        super().changeEvent(event)
        
# QLabel for keeping the contained pixmap scaled correctly
class PixLabel(QLabel):

    # set up the PixLabel
    def __init__(self):

        # allow the QLabel to initialize itself
        super().__init__()

        # adjustable side unit length of label
        self.side = 80

        # default size twice its minimum size
        self.setGeometry(0, 0, 2 * self.side, 2 * self.side)

        # define a class pixmap variable
        self.pix = None

        # define a class pixArray variable
        self.imageArr = None

        imgPolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setSizePolicy(imgPolicy)
        self.setMinimumSize(self.side, self.side)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
    
    # setter method for arr
    def setImageArr(self, arr):
        self.imageArr = arr

    # scale pixmap to label w and h, keeping pixmap aspect ratio
    def setPixmap(self, pix, isNewPix = True):

        # if a new pixmap is applied, adjust the minimum size of the
        # label so that the frame always stays flush with the pixmap
        # goal is for longest dimension to be minimum self.side
        if isNewPix:
            hOverW = pix.size().height() / pix.size().width()
            if hOverW < 1: # wide images
                self.setMinimumSize(self.side, int(self.side * hOverW))
            elif hOverW > 1: # tall images
                self.setMinimumSize(int(self.side / hOverW), self.side)
            else: # square images
                self.setMinimumSize(self.side, self.side)
        self.pix = pix
        scaled = pix.scaled(self.size(), Qt.KeepAspectRatio)
        super().setPixmap(scaled)
    
    # rescale the pixmap when the label is resized
    def resizeEvent(self, event):
        self.setPixmap(self.pix, False)
        self.setAlignment(Qt.AlignCenter)
        super().resizeEvent(event)

# subclassed QSplitter to allow for custom handles
class SplitterWithHandles(QSplitter):
    def __init__(self, orientation):
        super().__init__()
        self.setOrientation(orientation)
        self.setHandleWidth(4)

    def createHandle(self):
        return GradientSplitterHandle(self.orientation(), self)

# the custom splitter handle for a SplitterWithHandles
# subclass idea from PySide6 documentation page for QSplitterHandle
class GradientSplitterHandle(QSplitterHandle):

    def paintEvent(self, event):

        painter = QPainter()
        painter.begin(self)
        # preset gradient:
        gradientBrush = QBrush(QGradient.RiskyConcrete)
        if self.orientation() == Qt.Horizontal:
            gradientBrush.setTransform(QTransform().rotate(-90))

        painter.fillRect(self.rect(), gradientBrush)
        painter.end()

# BOILERPLATE TABLE MODEL
class ImageTableModel(QAbstractTableModel):
    def __init__(self, dataNames, data):
        super().__init__()

        self._dataNames = dataNames
        self._data = data
        self._tossedRows = []

    def addTossedRow(self, row):
        self._tossedRows.append(row)
    
    def removeTossedRow(self, row):
        self._tossedRows.remove(row)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if self._data[index.row(), index.column()] == 0.0:
                return ""
            else:
                return "%.4f" % self._data[index.row(), index.column()]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter + Qt.AlignRight
        if role == Qt.BackgroundRole:
            if (index.row() + 1) in self._tossedRows:
                return QBrush(Qt.darkGray)
    
    def rowCount(self, index):
        return self._data.shape[0]
    
    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._dataNames[section])

            if orientation == Qt.Vertical:
                return str(section + 1)

# create and display the application if this file is being run
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()