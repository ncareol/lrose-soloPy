# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
# ** Copyright UCAR (c) 1992 - 2014 
# ** University Corporation for Atmospheric Research(UCAR) 
# ** National Center for Atmospheric Research(NCAR) 
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA 
# ** See LICENSE.TXT for license details
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
#!/usr/bin/python

# colors.py

import time
import sys
from PySide import QtGui, QtCore
import math


class Colors(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(900, 900, 900, 900)
        self.setWindowTitle('Colors')
	self._colors = [ QtGui.QColor(255, 0, 0),
        	QtGui.QColor(0, 255, 0),
        	QtGui.QColor(0, 0, 255),
        	QtGui.QColor(50, 50, 0),
        	QtGui.QColor(0, 50, 50),
        	QtGui.QColor(50, 0, 50),
        	QtGui.QColor(150, 150, 0),
        	QtGui.QColor(0, 150, 150),
        	QtGui.QColor(150, 0, 150)
	]
	self.origin = [350, 350]
	self.colorIndex = 0
	self.drawIndex = self.colorIndex

    def drawRay(self, painter, angle, beamSpacing, pixPerGate, maxGates):
	sin1 = math.sin(angle)
	cos1 = math.cos(angle)
	sin2 = math.sin(angle+beamSpacing)
	cos2 = math.cos(angle+beamSpacing)
	XC = self.origin[0]
	YC = self.origin[1]
	for g in range(maxGates):
	    painter.setBrush(self._colors[self.colorIndex])
	    r0 = g*pixPerGate
	    r1 = (g+1)*pixPerGate
	
	    poly = QtGui.QPolygon([
		QtCore.QPoint( XC + cos1 * r0, YC + sin1 * r0),
		QtCore.QPoint( XC + cos1 * r1, YC + sin1 * r1),
		QtCore.QPoint( XC + cos2 * r1, YC + sin2 * r1),
		QtCore.QPoint( XC + cos2 * r0, YC + sin2 * r0),
	    ])
	    painter.drawConvexPolygon(poly)
	    self.colorIndex = (self.colorIndex + 1) % len(self._colors)
	    

    def paintEvent(self, event):
        paint = QtGui.QPainter()
        paint.begin(self)

        color = QtGui.QColor(0, 0, 0)
        color.setNamedColor('#d4d4d4')
        paint.setPen(color)
        self.drawIndex = (self.drawIndex + 1) % len(self._colors)
	self.colorIndex = self.drawIndex

	start = time.time()
	a = 0
	beamSpacing = 1.0
	while a < 360:
	    print "paintEvent: drawing %f\n" % a
	    self.drawRay(paint, a * math.pi/180.0, beamSpacing * math.pi/180.0, 6, 199)
	    a = a + beamSpacing

        paint.end()
	elapsed = time.time() - start
	print "draw took %5.1f seconds\n" %  elapsed

app = QtGui.QApplication(sys.argv)
dt = Colors()
dt.show()
app.exec_()
