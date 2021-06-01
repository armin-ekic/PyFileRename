# -*- coding: utf-8 -*-
# Rename/views.py

"""This module provides the Renamer main window."""

#allows efficient aappending and popping from either side of the deque (used to store paths of files to be renamed)
from collections import deque

#used to represent concrete file or directory paths in the file system, and allows functions on files or directories
from pathlib import Path

#allows the use of multithreading so our GUI doesn't freeze when handling a large number of files
from PyQt5.QtCore import QThread

#allows the use of the renamer function used to change the names of the selected files
from .rename import Renamer

#allows us to use widgets in our created GUI window, and allows base GUI functionality, and import QFileDialog
#which lets us select files or directories from our file system using a predefined dialog
from PyQt5.QtWidgets import QFileDialog, QWidget

#allows functionality/creation of our GUI window using the created .py file
from .ui.window import Ui_Window

#this constant specifies file filters as a string, allowing selection of different file types
FILTERS = ";;".join(
    (
        "PNG Files (*.png)",
        "JPEG Files (*.jpeg)",
        "JPG Files (*.jpg)",
        "GIF Files (*.gif)",
        "Text Files (*.txt)",
        "Python Files (*.py)",
    )
)


#used to initialize/setup the window, multiple inheritance of QWidget and UI_Window, allowing us to access methods
#and attributes from both using super(). Ui_Window is the arbitrary name picked for the created window class
class Window(QWidget, Ui_Window):

    #in terms of object oriented concepts, __init__ is basically a constructor, it's called when an object of the
    #defined class is created
    def __init__(self):
        #super() allows me to create a tempory object of the window class
        super().__init__()
        #queue to store the paths to the files we want to rename
        self._files = deque()
        #stores the number of files we will need to rename
        self._filesCount = len(self._files)
        #defining self in the argument above allows us to access the methods of the defined class (setupUI() here)
        self._setupUI()
        self._connectSignalsSlots()

    def _setupUI(self):
        self.setupUi(self)

    #collect signal and slot connections, so we can .loadFiles() everytime the Load Files button is clicked in GUI
    #and rename files everytime the renameFiles button is clicked. loadFilesButton and renameFilesButton are the
    #values for the objects in Qt Designer which was edited when the GUI was designed
    def _connectSignalsSlots(self):
        self.loadFilesButton.clicked.connect(self.loadFiles)
        self.renameFilesButton.clicked.connect(self.renameFiles)

    #loads the selected files that we want to rename
    def loadFiles(self):
        #clears the .dstFileList list widget whenever the Load Files button is clicked
        self.dstFileList.clear()
        #conditional statement to cehck if the Last Source Directory line edit is displaying a path. if it is then
        #the initial directory (initDir) holds the path, if not, the initial directory is set to the home folder
        if self.dirEdit.text():
            initDir = self.dirEdit.text()
        else:
            initDir = str(Path.home())
        #creates dialog to allow user to select multiple files, returns a list of string-based paths to the chosen
        #files. also returns the previously defined file filter
        files, filter = QFileDialog.getOpenFileNames(
            self, "Choose Files to Rename", initDir, filter=FILTERS
        )
        #if at least one file is selected, go into this conditional
        if len(files) > 0:
            #slices the filter string to extract the file extension
            fileExtension = filter[filter.index("*"): -1]
            #sets the extensionLabel object to the extracted extension (extensionLabel is what it was called in GUI)
            self.extensionLabel.setText(fileExtension)
            #retrieve the path to the directory containing the files using the path to the first file in the list
            srcDirName = str(Path(files[0]).parent)
            #set the texts of dirEdit to the directory path found one line up
            self.dirEdit.setText(srcDirName)
            #iterate over the slected files, create a path object for each file, and append it to ._files
            for file in files:
                self._files.append(Path(file))
                self.srcFileList.addItem(file)
            #update to reflect the total number of files in the list
            self._filesCount = len(self._files)

    #this will run the thread functionality to rename files
    def renameFiles(self):
        self._runRenamerThread()

    #creates threads and renames selected files
    def _runRenamerThread(self):
        #get the text in the Filename Prefix line edit which the user provides (called prefixEdit as GUI value)
        prefix = self.prefixEdit.text()
        #create a new QThread to offload the file renaming process
        self._thread = QThread()
        #instantiate Renamer passing the list of files and the desired prefix to the constructor
        self._renamer = Renamer(files = tuple(self._files), prefix = prefix,)
        #move the given object to a different thread of execution using ._thread as the target thread
        self._renamer.moveToThread(self._thread)
        #rename the files, connect .started() with .renameFiles() on the Renamer instance, start renaming when the
        #thread starts
        self._thread.started.connect(self._renamer.renameFiles)
        #update the state, connect .renamedFile() with ._updateStateWhenFileRenamed()
        self._renamer.renamedFile.connect(self._updateSttateWhenFileRenamed)
        #clean up the threads by getting rid of the extras
        #connect Renamers .finished() with the thread's .quit() slot to quit when renaming is finished
        self._renamer.finished.connect(self._thread.quit)
        #connect Renamers .finished with the thread's .deleteLater() slot to schedule it for later deletion
        self._renamer.finished.connect(self._renamer.deleteLater)
        #connects threads .finished() with .deleteLater() to delete the thread only after it's finished its job
        self._thread.finished.connect(self._thread.deleteLater)
        #run the worker thread
        self._thread.start()

    #when a file is renamed, remove the file from the list of files to be renamed, then update the necessary lists
    def _updateStateWhenFileRenamed(self, newFile):
        self._files.popleft()
        self.srcFileList.takeItem(0)
        self.dstFileList.addItem(str(newFile))
