# -*- coding: utf-8 -*-
# Rename/rename.py

"""This module provides the Renamer class to rename multiple files."""

#allows the use of wait statements in this case
import time

#import path to manipulate files and directories
from pathlib import Path

#imports QObject allowing us to make subclasses with custom signals/functionalities, and pyqtSignal to make signals
from PyQt5.QtCore import QObject, pyqtSignal


#subclass of QObject called Renamer
class Renamer(QObject):

    #custom signals
    #will emit every time a new file is renamed by the class, returns an int of the number of renamed files
    progressed = pyqtSignal(int)
    #will emit whenever a file is renamed, used to update the list of renamed files in the GUI
    renamedFile = pyqtSignal(Path)
    #emits whenever the file renaming process is complete
    finished = pyqtSignal()

    #files holds the selected list of files, and prefix is the entered prefix for the renaming process
    def __init__(self, files, prefix):
        super().__init__()
        self._files = files
        self._prefix = prefix

    #function to actually rename the selected files
    def renameFiles(self):
        #iterate over the list of selected files, enumerate used to generate a file number as we go on
        for fileNumber, file in enumerate(self._files, 1):
            #builds new file names using using the prefix, file number, and file extension
            newFile = file.parent.joinpath(
                f"{self._prefix}{str(fileNumber)}{file.suffix}"
            )
            #rename the file using the new file name generated a few lines up
            file.rename(newFile)
            #slows down the renaming of files so we can see it progress
            time.sleep(0.1)
            #indicate that a new file has been renamed, and give its number
            self.progressed.emit(fileNumber)
            #indicate that a file has been renamed and what the name of the file is
            self.renamedFile.emit(newFile)
        #resets the progress bar when we are finished
        self.progressed.emit(0)
        #indicate we are done with the renaming process
        self.finished.emit()