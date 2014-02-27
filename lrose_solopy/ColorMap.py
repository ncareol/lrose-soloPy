# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
# ** Copyright UCAR (c) 1992 - 2014 
# ** University Corporation for Atmospheric Research(UCAR) 
# ** National Center for Atmospheric Research(NCAR) 
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA 
# ** See LICENSE.TXT for license details
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
import numpy.ma as ma
import os, glob
from matplotlib.colors import LinearSegmentedColormap, ColorConverter
from numpy import sort
from Config import Config

class ColorMap:
    """
    A class for storing color map information.

    Parameters 
    ----------
    files : dict
        Variable name and color file name mapping.
    dir_ : string
        Color file directory.

    Attributes
    ----------
    colorTable : dict
        Storing mapping between variable name and parsed color file.
    map : dict
        Storing mapping between variable name and color map.
    ticks_label : dict
        Stroing mapping between variable name and color bar ticks.

    """

    PATH = './color_scales/'

    def __init__(self,files,dir_):
        """ initialize, read and parse configuration file, generate colormap based on color files 
        files - dictionary of variable name vs colormap filename
        dir_ - directory containing colormap files
        """
        ## get color file directory and file names
        if dir_ == None:
            dir_ = self.PATH
        colorfiles = files
        self.colorTable = self.readColorFiles(dir_,colorfiles) ## colorfiles is in dict, e.g. {'vel': 'vel.colors', 'dbz': 'dbz.hawkeye.colors'}
        self.map, self.ticks_label = self.make_colormap_all() ## return dict

    def __call__(self, key):
        """ look up for the colormap based on the key provided"""
        if key not in self.map:
            return self.map[sorted(self.map.keys())[0]]
        else:
            return self.map[key]

    def make_colormap_all(self):
        """ make colormap for each color in self.colorTable"""
        colormap = {}
        ticks_label = {}
        for k,v in self.colorTable.items():
            colormap[k], ticks_label[k] = self.make_colormap(k)
        return colormap, ticks_label

    def make_colormap(self, key):
        """ define a new color map based on values specified in the color_scale file for the key"""
        #colors = {0.1:'#005a00', 0.2:'#6e0dc6',0.3:'#087fdb',0.4:'#1c47e8',0.5:'#007000'} # parsed result format from color_scale file
        colors = self.colorTable[key]
        z = sort(colors.keys()) ## keys
        n = len(z)
        z1 = min(z)
        zn = max(z)
        x0 = (z - z1) / (zn - z1)   ## normalized keys
        CC = ColorConverter()
        R = []
        G = []
        B = []
        for i in range(n):
            ## i'th color at level z[i]:
            Ci = colors[z[i]]      
            if type(Ci) == str:
                ## a hex string of form '#ff0000' for example (for red)
                RGB = CC.to_rgb(Ci)
            else:
                ## assume it's an RGB triple already:
                RGB = Ci
            R.append(RGB[0])
            G.append(RGB[1])
            B.append(RGB[2])

        cmap_dict = {}
        cmap_dict['red'] = [(x0[i],R[i],R[i]) for i in range(len(R))] ## normalized value in X0
        cmap_dict['green'] = [(x0[i],G[i],G[i]) for i in range(len(G))]
        cmap_dict['blue'] = [(x0[i],B[i],B[i]) for i in range(len(B))]
        mymap = LinearSegmentedColormap(key,cmap_dict)
        return mymap, z

    def readColorFiles2(self):
        """ get all the color_scales files that suffix are .colors """
        for infile in glob.glob( os.path.join(self.PATH, '*.colors') ):
            if len(infile.split("/")[1].split("."))==2:
                self.readColorFile(infile)

    def readColorFiles(self,dir_,filenames):
        """ get all the color_scales files """
        colorTable = {}
        for k,v in filenames.items():
            colorTable[k] = self.readColorFile(dir_+'/'+v, k)
        return colorTable

    def getDefaultFileName(self,var):
        """ if not find the named file, use the default file """
        fn = self.PATH + '/' + var + '.colors'
        return fn

    def readColorFile(self,fn,var):
        """ read and parse each color file """
        """ fn is the filename including path. var is the color name """
        try:
            with open(fn) as file: ## check if file exists
                pass
        except IOError as e:
            print "Unable to open file", fn
            ## set default value for fn
            ##fn = self.getDefaultFileName(var)

        f = open(fn,'r')
        ## format color scale to dict format   
        ## color_scale = {-10.:'#005a00', 20.:'#6e0dc6',30.:'#087fdb',40.:'#1c47e8',50.:'#007000'}
        color_scale = {}
        for line in f:
            line = line.strip('\r\n')
            line = line.strip(' ')
            if line !="" and line[0] != "#":
                v = line.split('\t')
                color_scale[float(v[0].strip(' '))] = v[2].strip(' ')
        f.close()
        return color_scale
        """
        colors = []
        for line in f:
            line = line.strip('\r\n')
            line = line.strip(' ')
            if line !="" and line[0] != "#":
                line = line.split('\t')
                c = []
                for l in line:
                    c.append(l.strip(' '))
                colors.append(c)
        if var not in self.colorTable:
            self.colorTable[var] = colors
        else:
            print 'duplicate color file for ', var
        """


if __name__ == '__main__':
    c = ColorMap()
    print c.colorTable['dbz']
