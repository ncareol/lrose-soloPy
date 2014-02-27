# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
# ** Copyright UCAR (c) 1992 - 2014 
# ** University Corporation for Atmospheric Research(UCAR) 
# ** National Center for Atmospheric Research(NCAR) 
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA 
# ** See LICENSE.TXT for license details
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
## not used

from Sweep import Sweep

class Volume:
    """
    A class for storing sweep objects.

    Parameters 
    ----------
    sweeps : Sweep
        Sweep object.
    ranges : list
        Range data.

    Attributes
    ----------
    sweep : Sweep
        List of sweeps.
    ranges : list
        Range data.

    """

    def __init__(self, sweeps, ranges):
        
        self.sweeps = sweeps
        self.ranges = ranges
        print '========', ranges
    def getMetadata(self):
        self.dimensions = self.ncfile.dimensions.keys() # list
        self.variableNames = self.ncfile.variables.keys()   # list
        self.globalAttList = self.ncfile.ncattrs() #dir(self.ncfile)
