# -*- coding: utf-8 -*-
# rprenamer.py

""""This module provides the Renamer entry-point script"""

#bring in main from the defined app function so we can access it from this entry point script
from Rename.app import main

#call main if the module is ran as a python script
if __name__ == "__main__":
    main()