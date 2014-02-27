# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
# ** Copyright UCAR (c) 1992 - 2014 
# ** University Corporation for Atmospheric Research(UCAR) 
# ** National Center for Atmospheric Research(NCAR) 
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA 
# ** See LICENSE.TXT for license details
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
import numpy as np
from math import sin, cos, pi
#from Polygon import Polygon
#from Ray import Ray

class Sweep:
    """
    A class for storing sweep information.

    Parameters 
    ----------
    sweepnumber : integer
        Sweep number.
    ranges : list
        Range data.
    x : list
        X values.
    y : list
        Y values.
    vars_ : dict
        Variable values.
    label : string
        Plot label.
    timeRange : list
        Start and end time information for BSCAN mode.

    Attributes
    ----------
    sweepnumber : integer
        Sweep number.
    ranges : list
        Range data.
    x : list
        X values.
    y : list
        Y values.
    vars_ : dict
        Variable values.
    timelabel : string
        Plot label.
    timeRange : list
        Start and end time information for BSCAN mode.

    """

    def __init__(self, sweepnumber, ranges, x, y, vars_, label, timeRange):
        self.sweepnumber = sweepnumber
        self.ranges = ranges
        self.vars_ = vars_ #in dict format
        self.x = x  #(n_rays, 996)
        self.y = y
        self.timeLabel = label
        self.timeRange = timeRange
        
    """
    def dataConvert2XYPlane(self, ranges, ax):
    
        color = Color()
        for i in range(len(self.rays)):
            ray = self.rays[i]
            az = ray.azimuth
            if az == 0 and i>0:
                az1 = self.rays[i-1].azimuth
                az2 = ray.azimuth + 360
                az3 = self.rays[i+1].azimuth
            elif az==0 and i==0:
                az1 = self.rays[len(sweep.rays)-1].azimuth
                az2 = ray.azimuth + 360
                az3 = self.rays[i+1].azimuth
            
            elif az == 359 and i<len(self.rays)-1: #and sweep.rays[i+1].azimuth==0:
                az1 = self.rays[i-1].azimuth
                az2 = ray.azimuth
                az3 = self.rays[i+1].azimuth + 360                
            elif az == 359 and i==len(sweep.rays)-1: # and sweep.rays[0].azimuth==0:
                az1 = self.rays[i-1].azimuth
                az2 = ray.azimuth
                az3 = self.rays[0].azimuth + 360                

            elif i==len(self.rays)-1:
                az1 = self.rays[i-1].azimuth
                az2 = ray.azimuth
                az3 = self.rays[0].azimuth
            else:
                az1 = self.rays[i-1].azimuth
                az2 = ray.azimuth
                az3 = self.rays[i+1].azimuth
            az_a = (az1+az2)/2/180.0 * pi
            az_b = (az2%360+az3)/2/180.0 * pi

            data = ray.data # gates
            '''
#            print 'data type of DBZ_S', type(data)
            print '==============================='
            print 'i = ', i
            print 'az1 = ', az1
            print 'az2 = ', az2            
            print 'az3 = ', az3            
            print 'az_a = ', az_a
            print 'az_b = ', az_b
            print 'dbz = ', data
            print 'len of ray and data = ', len(sweep.rays), len(data)
            '''
            sin_az_a = sin(az_a)
            cos_az_a = cos(az_a) 
            sin_az_b = sin(az_b)
            cos_az_b = cos(az_b) 

            for j in range(len(data)-1):
                if j == 0:
                    r1 = 0
                else:
                    r1 = ranges[j-1]
                r2 = ranges[j]
                r3 = ranges[j+1]
                r_a = (r1+r2)/2/1e3
                r_b = (r2+r3)/2/1e3
                
                x1 = r_a * sin_az_a
                y1 = r_a * cos_az_a
                
                x2 = r_a * sin_az_b 
                y2 = r_a * cos_az_b
                
                x3 = r_b * sin_az_b 
                y3 = r_b * cos_az_b
                
                x4 = r_b * sin_az_a 
                y4 = r_b * cos_az_a

                verts = [x1,y1], [x2,y2], [x3,y3], [x4,y4]
                poly = Polygon(verts, color(data[j]))
                poly.draw(painter)
    def draw(self):
        
#        width, height = matplotlib.rcParams['figure.figsize']
#        size = min(width, height)
        # make a square figure
#        fig = plt.figure(figsize=(size, size))
        fig = plt.figure()
        ax = fig.add_subplot(111) 
#        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], axisbg='#d5de9c')

#        for ray in self.rays:
#            ray.draw(ax)                
        self.dataConvert2XYPlane(self.ranges,ax)

        ax.set_xlim(-15,15) 
        ax.set_ylim(-15,15) 
        plt.grid()
        plt.show() 
        
#    def getColorTableRgb(self,data):
    """

