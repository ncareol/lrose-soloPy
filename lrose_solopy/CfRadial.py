# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
# ** Copyright UCAR (c) 1992 - 2014 
# ** University Corporation for Atmospheric Research(UCAR) 
# ** National Center for Atmospheric Research(NCAR) 
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA 
# ** See LICENSE.TXT for license details
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
from netCDF4 import Dataset
import netCDF4
import os
from Volume import Volume
#from Ray import Ray
from Sweep import Sweep
from numpy import *
from pylab import *

class CfRadial:
    """
    A class for reading and parsing netCDF file.

    Parameters 
    ----------
    filename : string
        The file name with full path.

    Attributes
    ----------
    filename : string
        NetCDF file.
    dimensions : OrderedDict
        Variable names in netCDF file.
    variables : list
        Variable names for display.
    dicTreeList : dict
        Storing netCDF attributes.
    treeList : list
        Storing netCDF attributes.
    ncfile : Dataset
        NetCDF object.
    volume : Volume
        Volume object for storing sweeps.
    sweepElevation : list
        Sweep elevation.
    displayMode : string
        Display mode in "BASIC" or "BSCAN"
    timeLabel : string
        Time information read from netCDF file.

    """

    BSCANMODE = "BSCAN"
    BASICMODE = "BASIC"

    def __init__(self, filename):

        self.filename = filename
        self.dimensions = ''
        self.variables = ''
        self.dicTreeList = {'dimensions':[],'variables':[], 'global attributes':[]}
        self.treeList = []
        self.ncfile = None
        self.volume = None
        self.sweepElevation = None
        self.displayMode = self.getDisplayMode()
        
    def readFile(self):
        """ read ncfile and get all information from ncfile """
        self.ncfile=Dataset(self.filename,'r')
        self.getMetadata()
        self.timeLabel = self.getTimeLabel()
        if self.displayMode == self.BSCANMODE:
            sweeps = self.retrieveData_BSCAN()
        else:
            sweeps = self.retrieveData(self.variables)
        return sweeps

    def getDisplayMode(self):
        self.ncfile=Dataset(self.filename,'r')
        self.getMetadata()

        if "beta_a_backscat_parallel" in self.variables and \
           "extinction" in self.variables:
            return self.BSCANMODE
        else:
            return self.BASICMODE

    def getTimeLabel(self):
        start = self.ncfile.variables['time_coverage_start'][:]
        end = self.ncfile.variables['time_coverage_end'][:]
        if type(start) == ma.core.MaskedArray :
            start = start.data
            end = end.data
        label = ''.join(start)
        label = label + " - " + ''.join(end)
        return label

    def retrieveData(self, var_list) :
        """ retrieve the list of variables specified by var_list """
    
        nrays = dtime = len(self.ncfile.dimensions['time'])
        drange = len(self.ncfile.dimensions['range'])
        dsweep = len(self.ncfile.dimensions['sweep']) # number of sweeps
        maxgates=self.ncfile.variables['range'].shape[0]
        
        n_points_flag = False
        if 'n_points' in self.ncfile.dimensions.keys():
            n_points = len(self.ncfile.dimensions['n_points'])
            n_points_flag = True

        vars_ = {}
        # retrieve the specified variables
        for v in var_list:
            vars_[v] = self.ncfile.variables[v]

        if n_points_flag == False:
            # Regular 2-D storage - constant number of gates
            #sweep_fixed_angle = self.ncfile.variables['fixed_angle'][:]
            pass
        else:
            # Staggered 2-D storage - variable number of gates
            ray_len = ray_n_gates = ray_len = self.ncfile.variables['ray_n_gates'][:]
            ray_start_index = self.ncfile.variables['ray_start_index'][:] 

        self.sweepElevation = sweep_fixed_angle = self.ncfile.variables['fixed_angle'][:] ## both Regular and Staggered have this field
        
        time = self.ncfile.variables['time'][:]
        ranges = self.ncfile.variables['range'][:]
        sweep_start_ray_index = self.ncfile.variables['sweep_start_ray_index'][:]
        sweep_end_ray_index = self.ncfile.variables['sweep_end_ray_index'][:]

        rg,azg=meshgrid(ranges, self.ncfile.variables['azimuth'][:])
        rg,eleg=meshgrid(ranges,self.ncfile.variables['elevation'][:])
        x,y,z=self.radar_coords_to_cart(rg,azg, eleg)

        if n_points_flag == False: 
            # Regular 2-D storage - constant number of gates
            print 'Regular 2-D storage - constant number of gates'
            time_range_list = {}

            for v in var_list:
                time_range=zeros([nrays, maxgates])-9999.0
                for ray in range(nrays):
                    time_range[ray, :]=vars_[v][ray]
                time_range_list[v] = time_range

        else:                           
            # Staggered 2-D storage - variable number of gates
            print 'Staggered 2-D storage - variable number of gates'
            time_range_list = {}
            
            for v in var_list:
                time_range=zeros([nrays, maxgates])-9999.0
                for ray in range(nrays):
                    time_range[ray, 0:ray_len[ray]]=vars_[v][ray_start_index[ray]:ray_start_index[ray]+ray_len[ray]]
                time_range_list[v] = time_range
                    
        ## format data into sweeps
        sweeps = []
        for sweepnumber in range(dsweep):
            firstRay = sweep_start_ray_index[sweepnumber]
            lastRay = sweep_end_ray_index[sweepnumber]
            data = {}
            for v in var_list:
                data[v] = time_range_list[v][firstRay:lastRay]
#            sweep = Sweep(sweepnumber,ranges,x[firstRay:lastRay]/1e3,y[firstRay:lastRay]/1e3,data,self.timeLabel)
            sweep = Sweep(sweepnumber,ranges,x[firstRay:lastRay]/1e3,y[firstRay:lastRay]/1e3,data,self.timeLabel,None)
            sweeps.append(sweep)

        return sweeps
    
    def retrieveData_BSCAN(self):
        """ retrieve data as required in BSCAN mode display """
        time = self.ncfile.variables['time'][:]
        time_coverage_start = self.ncfile.variables['time_coverage_start'][:].compressed().tostring()
        time_coverage_end = self.ncfile.variables['time_coverage_end'][:].compressed().tostring()
        altitude = self.ncfile.variables['altitude'][:]
        ranges = self.ncfile.variables['range'][:]
        data = {}
        for v in self.variables:
            data[v] = self.ncfile.variables[v][:]
            data[v] = np.ma.log10(data[v])

        sweeps = []
        sweep = Sweep(0,ranges,time,ranges,data,None,[time_coverage_start,time_coverage_end])
        sweeps.append(sweep)
        return sweeps

    def radar_coords_to_cart(self, rng, az, ele, debug=False):
        """
        Asumes standard atmosphere, ie R=4Re/3
        Note that this v
        """
        Re=6371.0*1000.0
        p_r=4.0*Re/3.0
        rm=rng
        z=(rm**2 + p_r**2 + 2.0*rm*p_r*np.sin(ele*np.pi/180.0))**0.5 -p_r
        #arc length
        s=p_r*np.arcsin(rm*np.cos(ele*np.pi/180.)/(p_r+z))
        if debug: print "Z=", z, "s=", s
        y=s*np.cos(az*np.pi/180.0)
        x=s*np.sin(az*np.pi/180.0)
        return x,y,z

    def cal_cart_BSCAN(self, rng, tx, debug=False):
        """
        Asumes standard atmosphere, ie R=4Re/3
        Note that this v
        """
        y = rng
        x = tx
        return x,y

    def closeFile(self):
        """ close ncfile """
        self.ncfile.close()

    def getValue(self, parent, child):
        if parent == 'dimensions':
            print '>>>>>>>>>> dim'
            value = self.ncfile.dimensions[child]
        elif parent == 'variables':
            print '>>>>>>>>>> var'
            value = self.ncfile.variables[child][:]
        elif parent == 'global attributes':
            print '>>>>>>>>>> glo'
            value = getattr(self.ncfile, parent) 
        else:
            print 'not found!'    

        print type(value)
        print value
        return 'done'
        
    def getMetadata(self):
        """ get all information from ncfile """
        self.dimensions = self.ncfile.dimensions.keys() # list
        self.variables = self.varFilter(self.ncfile.variables.keys())   # list
        self.globalAttList = self.ncfile.ncattrs() #dir(self.ncfile)

#        self.printing()
#        print type(self.globalAttList)
#        self.fileContent = ncdumpread()
        self.dicTreeList['dimensions'] = self.dimensions
        self.dicTreeList['variables'] = self.variables
#        self.dicTreeList['global attributes'] = self.globalAttList

        ld = ['dimensions']
        ld.append(self.dimensions)
        lv = ['variables']
        lv.append(self.variables)
        lg = ['global attributes']
        lg.append(self.globalAttList)
        
        self.treeList = [ld,lv,lg]

    def varFilter(self, variables):
        """ filter out variables, might not be necessary """
        var_lst = []

        n_points_flag = False
        if 'n_points' in self.ncfile.dimensions.keys():
            n_points = len(self.ncfile.dimensions['n_points'])
            n_points_flag = True

        for v in variables:
            d = self.ncfile.variables[v].dimensions
            
            if n_points_flag == False:  # for constant ngates
                if len(d) == 2:
                    if d[0] == 'time' and d[1] == 'range':
                        var_lst.append(v)
            else:                       # for variable ngates
                if len(d) == 1:
                    if d[0] == 'n_points': 
                        var_lst.append(v)

        tmp = [v.lower() for v in var_lst]
        if "beta_a_backscat_parallel" in tmp and \
           "extinction" in tmp:
            var_lst = ['extinction','beta_a_backscat_parallel']

        return var_lst
                    
    def getVar_npoints(self):
        self.ncfile
        
    def convertListToString(self, lList):
        res = ''
        for l in lList:
            res = ' '.join(res,l)
        return res

    
    def ncdumpRead(self):
        command = 'ncdump -f C ' + os.path.join(self.dirname, self.filename)
        #return subprocess.check_output(cmd, shell=True)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        output = process.communicate()
        retcode = process.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, command, output=output[0])
        print type(output)
#        print output[0]
        print '----------------'
#        print output[1]
        print 'tuple length = ', len(output)
        return output
        
    def printing(self):
        print "self.dimensions : ", self.dimensions
        print "self.variables : ", self.variables
        print "self.globalAttList : ", self.globalAttList
    
    
    def setVolume(self,sweeps,ranges): ## not called
        self.volume = Volume(sweeps, ranges)
        

def dumpSweeps(sweeps):
    for s in sweeps:
        pass
        
    
    
if __name__ == "__main__":
#    writeToFile("testing.nc")
#    readFile("testing.nc")
#    readFile("sresa1b_ncar_ccsm3_0_run1_200001.nc")
#    readFile("testing3.nc")
    cf = CfRadial('/tmp/test.nc')
    #sweeps = cf.readFile(['DBZ','VEL']) 
    print 'readFile complete'




