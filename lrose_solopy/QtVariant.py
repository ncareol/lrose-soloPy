# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
# ** Copyright UCAR (c) 1992 - 2014 
# ** University Corporation for Atmospheric Research(UCAR) 
# ** National Center for Atmospheric Research(NCAR) 
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA 
# ** See LICENSE.TXT for license details
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
import sys
import os

""" 
module to support both PySide and PyQt4 interfaces
from QtVariant import QtGui, QtCore
"""

default_variant = 'PySide'
variant = 'PySide'

#env_api = os.environ.get('QT_API', 'pyside')
#env_api = 'pyside'
#if '--pyside' in sys.argv:
#    variant = 'PySide'
#elif '--pyqt4' in sys.argv:
#    variant = 'PyQt4'
#elif env_api == 'pyside':
#    variant = 'PySide'
#elif env_api == 'pyqt':
#    variant = 'PyQt4'
#else:
#    variant = default_variant

if variant == 'PySide':
    from PySide import QtGui, QtCore
    # This will be passed on to new versions of matplotlib
    os.environ['QT_API'] = 'pyside'
    def QtLoadUI(uifile):
        from PySide import QtUiTools
        loader = QtUiTools.QUiLoader()
        uif = QtCore.QFile(uifile)
        uif.open(QtCore.QFile.ReadOnly)
        result = loader.load(uif)
        uif.close()
        return result
elif variant == 'PyQt4':
    import sip
    api2_classes = [
            'QData', 'QDateTime', 'QString', 'QTextStream',
            'QTime', 'QUrl', 'QVariant',
            ]
    for cl in api2_classes:
        sip.setapi(cl, 2)
    from PyQt4 import QtGui, QtCore
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    QtCore.QString = str
    os.environ['QT_API'] = 'pyqt'
    def QtLoadUI(uifile):
        from PyQt4 import uic
        return uic.loadUi(uifile)
else:
    raise ImportError("Python Variant not specified")

__all__ = [QtGui, QtCore, QtLoadUI, variant]
