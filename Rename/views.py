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
FILTERS = "Desired(*.png *.jpg *.jpeg *.gif *.txt)"


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

    #this is one of the methods ran right when the code is ran, as it is called within __init__()
    def _setupUI(self):
        self.setupUi(self)
        self._updateStateWhenNoFiles()

    #set the values for our relevant object/attributes when no files are available for renaming
    def _updateStateWhenNoFiles(self):
        #update the total number of files, in this case it is 0
        self._filesCount = len(self._files)
        #enable the Load Files button so the users can click it
        self.loadFilesButton.setEnabled(True)
        #moves the focus to the Load Files button so the user can press space to load files
        self.loadFilesButton.setFocus(True)
        #disables rename because no files will be selected yet
        self.renameFilesButton.setEnabled(True)
        #remove any previously input prefixes
        self.prefixEdit.clear()
        #disable the ability to type in a prefix if no files are selected
        self.prefixEdit.setEnabled(False)

    #collect signal and slot connections, so we can .loadFiles() everytime the Load Files button is clicked in GUI
    #and rename files everytime the renameFiles button is clicked. loadFilesButton and renameFilesButton are the
    #values for the objects in Qt Designer which was edited when the GUI was designed
    def _connectSignalsSlots(self):
        self.loadFilesButton.clicked.connect(self.loadFiles)
        self.renameFilesButton.clicked.connect(self.renameFiles)
        self.prefixEdit.textChanged.connect(self._updateStateWhenReady)

    #when the user has given a prefix for the new names the rename button will be enables, otherwise it'll it won't
    def _updateStateWhenReady(self):
        if self.prefixEdit.text():
            self.renameFilesButton.setEnabled(True)
        else:
            self.renameFilesButton.setEnabled(False)

    #loads the selected files that we want to rename
    def loadFiles(self):
        #clears the .dstFileList list widget whenever the Load Files button is clicked
        self.dstFileList.clear()
        #conditional statement to check if the Last Source Directory line edit is displaying a path. if it is then
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
            #if we have files selected to be renamed, indicate this by going to that state
            self._updateStateWhenFilesLoaded()
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

    def _updateStateWhenFilesLoaded(self):
        #enable the prefix edit line so a prefix name can be input
        self.prefixEdit.setEnabled(True)
        #moves the focus to the prefix edit widget so you can provide a prefix name immediately
        self.prefixEdit.setFocus(True)

    #this will run the thread functionality to rename files
    def renameFiles(self):
        self._runRenamerThread()
        self._updateStateWhileRenaming()

    #when the application is in the process of renaming, the user can't click the load files or rename button
    def _updateStateWhileRenaming(self):
        self.loadFilesButton.setEnabled(False)
        self.renameFilesButton.setEnabled(False)

    #creates threads and renames selected files
    def _runRenamerThread(self):
        #get the text in the Filename Prefix line edit which the user provides (called prefixEdit as GUI value)
        prefix = self.prefixEdit.text()
        #create a new QThread to offload the file renaming process
        self._thread = QThread()
        #instantiate Renamer passing the list of files and the desired prefix to the constructor, this Renamer
        #object will be referred to as ._renamer further in this function definition
        self._renamer = Renamer(files = tuple(self._files), prefix = prefix)
        #move the given object to a different thread of execution using ._thread as the target thread
        self._renamer.moveToThread(self._thread)
        #rename the files, connect .started() with .renameFiles() on the Renamer instance, start renaming when the
        #thread starts
        self._thread.started.connect(self._renamer.renameFiles)
        #update the state, connect .renamedFile() with ._updateStateWhenFileRenamed()
        self._renamer.renamedFile.connect(self._updateStateWhenFileRenamed)
        #connects the renamer .progressed() with ._updateProgressBar()
        self._renamer.progressed.connect(self._updateProgressBar)
        #go to this state when we are done renaming, as there will be no more files left to rename
        self._renamer.finished.connect(self._updateStateWhenNoFiles)
        #clean up the threads by getting rid of the extras
        #connect Renamers .finished() with the thread's .quit() slot to quit when renaming is finished
        self._renamer.finished.connect(self._thread.quit)
        #connect Renamers .finished with the thread's .deleteLater() slot to schedule it for later deletion
        self._renamer.finished.connect(self._renamer.deleteLater)
        #connects threads .finished() with .deleteLater() to delete the thread only after it's finished its job
        self._thread.finished.connect(self._thread.deleteLater)
        #run the worker thread
        self._thread.start()

    #update the value of progress bar based on the number of files renamed, we are able to pass a valid file number
    #above because progressed() always has the fileNumber when a file gets renamed
    def _updateProgressBar(self, fileNumber):
        #compute the progress as a percentage of the total number of files
        progressPercent = int(fileNumber / self._filesCount * 100)
        #update .value using .setValue with progressPercent as an argument, this progressBar name was the name given
        #to the progress bar object in Qt Designer GUI
        self.progressBar.setValue(progressPercent)

    #when a file is renamed, remove the file from the list of files to be renamed, then update the necessary lists
    def _updateStateWhenFileRenamed(self, newFile):
        self._files.popleft()
        self.srcFileList.takeItem(0)
        self.dstFileList.addItem(str(newFile))
