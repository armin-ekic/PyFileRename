# -*- coding: utf-8 -*-
# Rename/app.py

""""This module provides the Renamer application"""

import sys

#this is used for all GUI applications using Qt, and this is used for widget based Qt applications
from PyQt5.QtWidgets import QApplication

from .views import Window


def main():

    #application created
    app = QApplication(sys.argv)
    #main window created and displayed
    win = Window()
    win.show()
    #event loop, this functions allows cleanly exiting the aff when the main window is closed
    sys.exit(app.exec())