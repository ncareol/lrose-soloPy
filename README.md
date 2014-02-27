# SoloPy
A prototype version of the SoloPy radar display using PySide, 
which is a set of LGPL-licensed Python bindings for Qt.

SoloPy has been tested with Python 2.7.3, matplotlib 1.2.0, PySide 1.1.2.
Some earlier versions may work, however there are known problems with using PyQt
under RHEL 6.3 (Python 2.6.6)
## Running SoloPy with Anaconda Python

[Anaconda](https://store.continuum.io/cshop/anaconda) is a free Python distribution 
from Continuum Analytics that includes numpy,
matplotlib and pyside, among many other scientific computing packages.

Anaconda supports the following platforms:

Linux and Windows: 64-bit and 32-bit
Mac OS X: Intel 64-bit
Python versions 2.6, 2.7, 3.3

1) Download Anaconda and install according to the provided instructions.

2) Verify that Anaconda Python is first in your path (logout/login, or source ~/.bashrc)

    $ which python
    /usr/local/anaconda/bin/python

For Mac OS users, the "graphical" version of Anaconda must be first in your
path:

    export PATH=/usr/local/anaconda/python.app/Contents/MacOS:/usr/local/anaconda/bin:$PATH

3) use the "conda" package manager to install the necessary packages

    $ conda install netcdf4

4) install the SoloPy package:

    python setup.py install
    cd ~    # don't run start_pysolo from the distribution directory

5) For first time users, run `start_pysolo` to create a default version of ~/solopy_config.xml.

Edit the 'data_dir' parameter to set the default directory for data files

6) run `run_solopy` to start the SoloPy application


## Running SoloPy with Enthought Canopy
SoloPy also works with [Enthought Canopy](https://www.enthought.com/store) Basic Edition or above.
Enthough Canopy is free for
students and staff of degree granting institutions.  The Enthought Canopy
Express edition will not work - it doesn't contain several packages needed by
SoloPy.
