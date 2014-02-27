# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
# ** Copyright UCAR (c) 1992 - 2014 
# ** University Corporation for Atmospheric Research(UCAR) 
# ** National Center for Atmospheric Research(NCAR) 
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA 
# ** See LICENSE.TXT for license details
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
"""
  This class reads and parses user configuration file.
"""
from PySide import QtGui as gui
import xml.etree.ElementTree as ET
import os,os.path
from utility import determine_pkg_path
import shutil

class Config:
    """
    A class for reading and parsing configuration file.

    Parameters 
    ----------
    configFile : string or None
        Configuration file name.

    Attributes
    ----------
    config : dict
        Storing configurations.

    """

    CONFIGFILE = '~/solopy_config.xml'
    BSCANMODE = "BSCAN"
    BASICMODE = "BASIC"

    def __init__(self, configFile=None):
        """ setup defaults """
        if configFile is None:
            self.filename = os.path.expanduser(self.CONFIGFILE)
            if not os.path.exists(self.filename):
                master_conf = os.path.join(determine_pkg_path(), "solopy_config.xml")
                shutil.copyfile(master_conf, self.filename)
                msgBox = gui.QMessageBox()
                
                msgBox.setText("Please edit %s and customize your configuration " % self.filename)
                msgBox.exec_() 
                raise RuntimeError("Please edit %s and customize your configuration " % self.filename)
                
        else:
            self.filename = configFile
        self.config = self.readConfigFile(self.filename)

    def __call__(self, key):
        """ look up for the colormap based on the key provided"""
        if key in self.config:
            return self.config[key]
        else:
            print "configuration does not include ", key

    def readConfigFile(self,fn):
        """ read config.xml file and parse all color file names in the xml file """
        try:
            config = {}
            tree = ET.parse(fn)
            root = tree.getroot()
            colorfiles = {}

            ## find tag 'window_size'   
            width = None
            height = None
            for val in root.findall('window_size'):
                width = int(val.find('width').text)
                height = int(val.find('height').text)

            ## find tag 'color_scales'
            path = None
            for cs  in root.findall('color_scales'):
                path = cs.get('dir')
                for e in cs.iter():
                    if e == cs:
                        continue
                    colorfiles[e.tag] = e.text
                    
            ## find default directory to read file
            default_file_dir = None
            for nc in root.findall('data_dir'):
                default_file_dir = nc.get('dir')

            ## find tag 'start_field' - default start field to display 
            startField = None
            for field in root.findall('start_field'):
                startField = field.get('name')

            ## find tag 'header_label' - default header label for title
            headerLabel = ""
            for label in root.findall('header_label'):
                headerLabel = label.get('label')

            ## find tag 'plot_mode'
            mode = None
            for val in root.findall('plot_mode'):
                mode = val.get('mode')
            if mode:
                if mode.upper() == self.BSCANMODE or mode.upper() == self.BASICMODE:
                    config['plot-mode'] = mode.upper()
                else:
                    raise RuntimeError( "Error: incorrect plot_mode \"%s\" in configuration file." % mode)
                    sys.exit(1)
            else:
                raise RuntimeError( "Error: no plot_mode setup in configuration file.")
                sys.exit(1)

            if width and height:
                config['window-size'] = [width,height]
            else:
                config['window-size'] = [500,450]

            if path:
                config['colorfile-dir'] = path
            else:
                config['colorfile-dir'] = '~/color_scales'
                
            config['colorfiles'] = colorfiles

            if default_file_dir:
                config['data-dir'] = default_file_dir
            else:
                config['data-dir'] = "./"

            config['start-field'] = startField
            config['header-label'] = headerLabel
            
            return config

        except IOError:
            raise RuntimeError( "Error: can\'t find/read configuration file (%s)" % fn)
        except ValueError:
            raise RuntimeError('Value error in the configuration file (%s).', fn)

if __name__ == '__main__':
    c = Config()
