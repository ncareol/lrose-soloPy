# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
# ** Copyright UCAR (c) 1992 - 2014 
# ** University Corporation for Atmospheric Research(UCAR) 
# ** National Center for Atmospheric Research(NCAR) 
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA 
# ** See LICENSE.TXT for license details
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=* 
import time
import numpy.ma as ma
import math

from PySide import QtGui as gui
from PySide import QtCore as core
from numpy import *
from pylab import *
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib import pyplot
from matplotlib.colorbar import ColorbarBase
from matplotlib.pyplot import figure, show
from matplotlib.lines import Line2D
# RadialDisplay Widget
import math

RENDER_PIXELS=300
MIN_DECIMATE = 3.0
SCALE_RATE = 1.1
SCALE = 300.0
ZOOM_WINDOW_WIDTH_LIMIT = 1.0
ZOOM_WINDOW_PIXEL_LIMIT = 20.0
FIGURE_CANCAS_RATIO = 0.78
R = 150.0

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=3, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, self.fig)

        FigureCanvas.setSizePolicy(self,
                                   gui.QSizePolicy.Expanding,
                                   gui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.AZIMUTH = False
        self.RANGE_RING = False
        self.COLORBAR = True
        self.PICKER_LABEL = False

    def sizeHint(self):
        w, h = self.get_width_height()
        return core.QSize(w, h)

    def minimumSizeHint(self):
        return core.QSize(10, 10)

class MplCanvas(MyMplCanvas):#,gui.QWidget):#(MyMplCanvas):
    """
    A class for displaying radar data in basic mode. In this mode, the width and height of plot are equal.

    Parameters 
    ----------
    title : string
        Plotting header label.
    colormap : ColorMap
        ColorMap object.

    Attributes
    ----------
    figurecanvas : FigureCanvas
        The canvas for display.
    zoomer : list
        Storing zoom windows.
    _zoomWindow : QRectF
        Storing current zoom window.
    origin : list
        Storing the coordinates for onPress event.
    var_ : dict
        Storing variables for display.
    AZIMUTH : boolean
        Flag for azimuth display.
    RANGE_RING : boolean
        Flag for RANGE_RING display.
    COLORBAR : boolean
        Flag for colorbar display.
    PICKER_LABEL : boolean
        Flag for picker label display.
    cb : ColorbarBase
        Colorbar object.
    cMap : ColorMap
        ColorMap object.
    pressEvent : event
        Press event.
    pressed : boolean
        Flag for press event.
    deltaX : float
        X change of rubberband. Zoom window only when the change is greater than ZOOM_WINDOW_PIXEL_LIMIT.
    deltaY : float
        Y change of rubberband.
    startX : float
        Rubberband start x value.
    startY : float
        Rubberband start y value.
    moveLabel : QLabel
        Picker label
    sweep : Sweep 
        Sweep object.
    ranges : list
        Sweep ranges
    varName : string
        Storing current display variable name.
    x : list
        Storing sweep x values.
    y : list
        Storing sweep y values.
    label : string
        Storing header label and sweep time stamp
    """

    def __init__(self, title, colormap, parent=None, width=3, height=3, dpi=100):
        self.fig = Figure()#plt.figure()#figsize=(width, height), dpi=dpi)
        plt.axis('off')
        self.axes = self.fig.add_subplot(111,aspect='equal')
        self.fig.set_dpi( dpi )
        self.headerLabel = title
        #self.axes.hold(False)
        #self.fig.canvas.mpl_connect('pick_event', self.onpick)

        self.figurecanvas = FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   gui.QSizePolicy.Expanding,
                                   gui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.setWindow(core.QRectF(-1. * RENDER_PIXELS/2., 1. * RENDER_PIXELS/2., 1. * RENDER_PIXELS, -1. * RENDER_PIXELS))
#        self.origins = core.QPoint()
        self.ignorePaint = False
        #self.bottomRight = core.QPoint()
        self.rubberBand = gui.QRubberBand(gui.QRubberBand.Rectangle, self)
        self.zoomer = []
#        self.picker = []
            
        self.origin = [RENDER_PIXELS,RENDER_PIXELS]
        self.scaleFactor = 1.0
#        self.offsetX = 0.0
#        self.offsetY = 0.0
        self.var_ = {}
        self.AZIMUTH = False
        self.RANGE_RING = False
        self.COLORBAR = True
        self.PICKER_LABEL = False
        self.cb = None
        self.cMap = colormap

        self.pressEvent = None
        self.pressed = False
        self.deltaX = 0.
        self.deltaY = 0.
        self.startX = None
        self.startY = None

        self.moveLabel = gui.QLabel("",self)
        self.moveLabel.setText("")
        self.moveLabel.hide()
        self.moveLabel.setStyleSheet("font-size:12px; margin:3px; padding:4px; background:#FFFFFF; border:2px solid #000;")

        self.mpl_connect('button_press_event', self.onPress)
        self.mpl_connect('button_release_event', self.onRelease)
        self.mpl_connect('motion_notify_event', self.onMove)

    def onPress(self,event):
        """ method called when mouse press"""
        if event.button == 1: ## left button
            xdata = event.xdata
            ydata = event.ydata
            # check if mouse is outside the figure        
            if xdata is None or ydata is None:
                return       

            self.pressed = True
            self.pressEvent = event

            self.origin = core.QPoint(event.x, self.height() - event.y)
            self.rubberBand.setGeometry(core.QRect(self.origin, core.QSize()))
            self.rubberBand.show()

            # start point        
            self.startX = xdata
            self.startY = ydata

        if event.button == 2: ## middle botton - zoom in the center
            pass
        if event.button == 3:
            pass

    def onMove(self,event):
        """ method called when mouse moves """
        xdata = event.xdata
        ydata = event.ydata
        if xdata is None or ydata is None:
            self.moveLabel.hide()
            return

        if self.pressed:  ## display rubberband
            if self.PICKER_LABEL:
                self.moveLabel.hide()

            deltaX = event.x - self.pressEvent.x  ## moved distance
            deltaY = event.y - self.pressEvent.y  ## for rubberband
            dx = dy = min(fabs(deltaX),fabs(deltaY))
            if deltaX<0: 
                dx = -dx
            if deltaY<0:
                dy = -dy
            newRect = core.QRect(self.origin.x(), self.origin.y(), int(dx), -int(dy))
            newRect = newRect.normalized()
            self.rubberBand.setGeometry(newRect)
            self.deltaX = dx
            self.deltaY = dy

        else:  ## display label
            if self.PICKER_LABEL:
                i,j = self.retrieve_z_value(xdata,ydata)
                self.moveLabel.show()
                if i is not None and j is not None:
#                    self.moveLabel.setText(core.QString(r"x=%g, y=%g, z=%g" % (xdata,ydata,self.var_[i][j]))) ## TODO: should use xdata or self.x[i][j]
                    self.moveLabel.setText(r"x=%g, y=%g, z=%g" % (xdata,ydata,self.var_[i][j])) ## TODO: should use xdata or self.x[i][j]
                    
                else:
#                    self.moveLabel.setText(core.QString(r"x=%g, y=%g, z=n/a" % (xdata,ydata)))
                    self.moveLabel.setText(r"x=%g, y=%g, z=n/a" % (xdata,ydata))
                self.moveLabel.adjustSize()
                offset = 10
                if self.width()-event.x < self.moveLabel.width():
                    offset = -10 - self.moveLabel.width()
                self.moveLabel.move(event.x+offset,self.height()-event.y)

    def retrieve_z_value(self, xdata, ydata):
        #xpos = np.argmin(np.abs(xdata-self.x))
        #ypos = np.argmin(np.abs(ydata-self.y))
        MIN = 99999
        iv = None
        jv = None
        for i in range(len(self.x)):
            j = self.findNearest(np.copy(self.x[i]),xdata)
            if j is not None:
                d = self.distance(xdata,ydata,self.x[i][j],self.y[i][j]) 
                if d < MIN:
                    iv = i
                    jv = j
                    MIN = d
        return iv,jv

    def onRelease(self,event):
        """ method called when mouse button is released """
        if event.button == 1:
            self.pressed = False
            self.rubberBand.hide()

            xdata = event.xdata ## mouse real position
            ydata = event.ydata
            if xdata is None or ydata is None or self.startX is None or self.startY is None:
                return

            d0 = self.width() * FIGURE_CANCAS_RATIO
            x_range = self.axes.get_xlim()[1]-self.axes.get_xlim()[0]
            y_range = self.axes.get_ylim()[1]-self.axes.get_ylim()[0]
            (x1,y1) = self.startX, self.startY
            (x2,y2) = x1 + self.deltaX/d0 * x_range, y1+self.deltaY/d0 * y_range

            oldRect = core.QRectF() # last rubberband rect
            oldRect.setLeft(self.axes.get_xlim()[0])
            oldRect.setRight(self.axes.get_xlim()[1])
            oldRect.setBottom(self.axes.get_ylim()[0])
            oldRect.setTop(self.axes.get_ylim()[1])

            rect = core.QRectF()  # current rubberband rect
            rect.setLeft(min(x1,x2))
            rect.setRight(max(x1,x2))
            rect.setBottom(min(y1,y2))
            rect.setTop(max(y1,y2))

            ## react only when draged region is greater than 0.01 times of old rect
            if fabs(self.deltaX)>ZOOM_WINDOW_PIXEL_LIMIT and \
               fabs(rect.width())>ZOOM_WINDOW_WIDTH_LIMIT and \
               fabs(rect.width()) >= 0.01*fabs(oldRect.width()): 
                self.zoomer.append(oldRect)
                self.zoomTo(rect)
                self._zoomWindow = rect

    def zoomTo(self,rect):
        """ adjust zoom winodw to rect """
        self.axes.set_xlim(rect.left(),rect.right())
        self.axes.set_ylim(rect.bottom(),rect.top())
        self.draw()

    def findNearest(self, array, target):
        """ find nearest value to target and return its index """
        diff = abs(array - target)
        mask = np.ma.greater(diff, 0.151) ## TODO: select a threshold (range:meters_between_gates = 150.000005960464)
        if np.all(mask):
            return None # returns None if target is greater than any value
        masked_diff = np.ma.masked_array(diff, mask)
        return masked_diff.argmin()
    
    def distance(self, x1, y1, x2, y2):
        """ calculate distance between two points """
        return sqrt((x1-x2)**2 + (y1-y2)**2) ## TODO: formula

    def sizeHint(self):
        w, h = self.get_width_height()
        return core.QSize(w, h)

    def minimumSizeHint(self):
        return core.QSize(10, 10)

    def setWindow(self, window):
        """ initialize the full window to use for this widget """
        self._zoomWindow = window
        self._aspectRatio = window.width() / window.height()

    def resizeEvent(self, event):
        """ method called when resize window """
        sz = event.size()
        width = sz.width()
        height = sz.height()
        dpival = self.fig.dpi
        winch = float(width)/dpival
        hinch = float(height)/dpival
        self.fig.set_size_inches( winch, hinch )
        #self.draw()
        #self.update()
        self.fig.canvas.draw()
        self.origin = [width,height]
        
    def drawSweep(self, sweep, varName, beamWidth):
        """ draw sweep """
        self.beamWidth = beamWidth
        self.ranges = sweep.ranges
        self.sweep = sweep
        self.varName = varName.lower()
        self.var_ = sweep.vars_[varName] #in list
        self.x = sweep.x
        self.y = sweep.y
        self.label = self.headerLabel + sweep.timeLabel
        self.update_figure() #update figure

    def update_figure(self):
        """ update figure - need to call it explicitly """
        if len(self.var_) > 0:
            self.axes.clear()

            vmin = min(min(x) for x in self.var_)
            vmax = max(max(x) for x in self.var_)

            im = self.axes.pcolormesh(self.x,self.y,self.var_, vmin=vmin, vmax=vmax, cmap=self.cMap(self.varName)) 
            ## setup zeniths, azimuths, and colorbar
            if self.RANGE_RING:
                self.draw_range_ring()
            if self.AZIMUTH:
                self.draw_azimuth_line()
            if self.COLORBAR:
                self.draw_colorbar(im,vmin,vmax)
            #self.x[0:359]/1e3,self.y[0:359]/1e3,self.var_,vmin=vmin, vmax=vmax)

            #plt.axis('off') ## show x, y axes or not
            #self.adjustZoomWindow() ## zoomWindow will not change for different variable - keep using the current zoom window
            self.zoomTo(self._zoomWindow)
            self.axes.set_title(self.label, size=9) ## TODO: change size to be adaptive
            self.fig.canvas.draw()
            ## draw contour - a new feature - grayscale, no zoom in/out support
            ## self.axes.contour(self.x,self.y,self.var_,[0.5], linewidths=2., colors='k')
            #self.fig.canvas.blit(self.axes.bbox)

    def draw_azimuth_line(self):
        """ draw azimuths with 30-degree intervals """
        angles = np.arange(0, 360, 30)
        labels = [90,60,30,0,330,300,270,240,210,180,150,120]
        x = R * np.cos(np.pi*angles/180)
        y = R * np.sin(np.pi*angles/180)

        for xi,yi,ang,lb in zip(x,y,angles,labels):
            line = plt.Line2D([0,xi],[0,yi],linestyle='dashed',color='lightgray',lw=0.8)
            self.axes.add_line(line)
            xo,yo = 0,0
            if ang>90 and ang<180:
                xo = -10
                yo = 3
            elif ang == 180:
                xo = -15
                yo = -3
            elif ang>180 and ang<270:
                xo = -12
                yo = -10
            elif ang == 270:
                xo = -10
                yo = -8
            elif ang >270 and ang<360:
                yo = -5
            self.axes.annotate(str(lb), xy=(xi,yi), xycoords='data',
                               xytext=(xo,yo), textcoords='offset points',
                               arrowprops=None,size=10)

    def draw_range_ring(self):
        """ draw zeniths with 30 intervals """
        zeniths = np.arange(0,R+1,30)
        angle = 135.
        for r in zeniths:
            circ = plt.Circle((0, 0),radius=r,linestyle='dashed',color='lightgray',lw=0.8,fill=False)
            self.axes.add_patch(circ)
            x = R * np.cos(np.pi*angle/180.) * r/R
            y = R * np.sin(np.pi*angle/180.) * r/R
            print 'r=',r, x, y
            self.axes.annotate(int(r), xy=(x,y), xycoords='data', arrowprops=None,size=10)

    def draw_colorbar(self,im,vmin,vmax):
        """ draw colorbar """
        if self.cb:
            self.fig.delaxes(self.fig.axes[1])
            self.fig.subplots_adjust(right=0.90)

        pos = self.axes.get_position()
        l, b, w, h = pos.bounds
        cax = self.fig.add_axes([l, b-0.06, w, 0.03]) # colorbar axes
        cmap=self.cMap(self.varName)
        substName = self.varName
        if not self.cMap.ticks_label.has_key(self.varName):
            # we couldn't find 'vel_f', so try searching for 'vel'
            u = self.varName.find('_')
            if u:
                substName = self.varName[:u]
                if not self.cMap.ticks_label.has_key(substName):
                
                    msgBox = gui.QMessageBox()
                    msgBox.setText(
    """ Please define a color scale for '{0}' in your configuration file """.format(self.varName))
                    msgBox.exec_()
                    raise RuntimeError(
   """ Please define a color scale for '{0}' in your configuration file """.format(self.varName))
        bounds = self.cMap.ticks_label[substName]
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
        self.cb = ColorbarBase(cax, cmap=cmap, norm=norm,  orientation='horizontal',  boundaries=bounds,ticks=bounds)#, format='%1i')  ## spacing='proportional' -- divide proportionally by the value
        self.cb.ax.tick_params(labelsize=8) 
        #t = [str(int(i)) for i in bounds]
        t = [str(i) for i in bounds]
        self.cb.set_ticklabels(t,update_ticks=True)
        self.cb.set_label('Color Scale', size=8)

    def resetFactors(self):
        """ reset factors """
        self.zoomer = []
        self.setWindow(core.QRect(-1 * RENDER_PIXELS/2, 1 * RENDER_PIXELS/2, 1 * RENDER_PIXELS, 1 * RENDER_PIXELS))
#        self.update_figure()
        self.fig.canvas.draw()

    def changeZoomerPointer(self, ind=None):
        """ method called when mouse button is pressed, changing zoomer pointer """
        if ind is None:
            if len(self.zoomer)>0:
                zoomWindow = self.zoomer[-1]
                self.zoomTo(zoomWindow)
                self.zoomer.pop()
        else:
            if len(self.zoomer)>0:
                zoomWindow = self.zoomer[0]
                self.zoomTo(zoomWindow)
                self.zoomer=[]      
            
    def getAspectRatio(self):
        return self._aspectRatio

    def keyPressEvent(self, event):
        """ method called when key press """
        print 'RadialDisplay::keyPressEvent: ', event.key()
        if event.key() == core.Qt.Key_C:
            self.resetFactors()
            event.accept()

    '''
    def mousePressEvent(self, event):
        """ method called when mouse press"""
        pos = event.pos()
        print 'Mpl::mousePressEvent: [%d , %d]' % (pos.x(), pos.y()) #, (event.xdata,event.ydata)

        if event.button() == core.Qt.LeftButton:
#            if not self.rubberBand:
            self.origins = core.QPoint(event.pos())
            self.ignorePaint =  True
            self.rubberBand.setGeometry(core.QRect(self.origins, core.QSize()))
            self.rubberBand.show()
            self.oldMouseX = event.pos().x()
            self.oldMouseY = event.pos().y()

    def mouseMoveEvent(self, event):
        """ method called when mouse button is pressed and moved """
        pos = event.pos()
        if not self.origins.isNull():
            self.bottomRight = event.pos()
            deltaX = pos.x() - self.oldMouseX
            deltaY = pos.y() - self.oldMouseY
            dx = dy = min(deltaX,deltaY)
            newRect = core.QRect(self.origins.x(), self.origins.y(), int(dx), int(dy))
            newRect = newRect.normalized()
            self.rubberBand.setGeometry(newRect)

    def mouseReleaseEvent(self, event):
        """ method called when mouse button is released, changing paint center """
        self.ignorePaint = False

        if event.button() == core.Qt.LeftButton:
            self.rubberBand.hide()

            if not self.origins.isNull() and not self.bottomRight.isNull():
                g = self.rubberBand.geometry()
                if g.width() <= 20:
                    pass
                else:
                    mywindow = core.QRect()
                    mywindow.setRect(self._zoomWindow.x(), self._zoomWindow.y(), self._zoomWindow.width(), self._zoomWindow.height())
                    self.zoomer.append(mywindow)

                    curr_x = self._zoomWindow.x()
                    curr_y = self._zoomWindow.y()
                    curr_width = self._zoomWindow.width()
                    curr_height = self._zoomWindow.height()
                    zoom_x = float(g.x()) * curr_width / self.origin[0] + curr_x
                    zoom_y =  -1. * (float(g.y()) * curr_height / self.origin[0] )+ curr_y 
                    zoom_width  = float(g.width())/self.origin[0] * curr_width
                    zoom_height = zoom_width
                    self.setZoomWindow(zoom_x, zoom_y, zoom_width, zoom_height)
                    #self.update_figure()

    def setZoomWindow(self,x,y,width,height):
        """ set current zoom window """
        self._zoomWindow.setRect((int)(x), (int)(y), (int)(width), (int)(height))
        self.adjustZoomWindow()

    def adjustZoomWindow(self):
        x1 = self._zoomWindow.x()
        y1 = self._zoomWindow.y()
        x2 = x1 + self._zoomWindow.width()
        y2 = y1 - self._zoomWindow.height()
        print 'adjustZoomWindow ---', x1,y1,x2,y2
        if x1<x2:
            self.axes.set_xlim(x1,x2)
        else:
            self.axes.set_xlim(x2,x1)
        if y1<y2:
            self.axes.set_ylim(y1,y2)
        else:
            self.axes.set_ylim(y2,y1)
        self.fig.canvas.draw()
    '''


class MplCanvasBSCAN(MyMplCanvas):
    """
    A class for displaying radar data in BSCAN mode. In this mode, the width and height of plot are not equal.

    Parameters 
    ----------
    title : string
        Plotting header label.
    colormap : ColorMap
        ColorMap object.

    Attributes
    ----------
    figurecanvas : FigureCanvas
        The canvas for display.
    zoomer : list
        Storing zoom windows.
    _zoomWindow : QRectF
        Storing current zoom window.
    origin : list
        Storing the coordinates for onPress event.
    var_ : dict
        Storing variables for display.
    COLORBAR : boolean
        Flag for colorbar display.
    PICKER_LABEL : boolean
        Flag for picker label display.
    cb : ColorbarBase
        Colorbar object.
    cMap : ColorMap
        ColorMap object.
    pressEvent : event
        Press event.
    pressed : boolean
        Flag for press event.
    deltaX : float
        X change of rubberband. Zoom window only when the change is greater than ZOOM_WINDOW_PIXEL_LIMIT.
    deltaY : float
        Y change of rubberband.
    startX : float
        Rubberband start x value.
    startY : float
        Rubberband start y value.
    moveLabel : QLabel
        Picker label
    sweep : Sweep 
        Sweep object.
    ranges : list
        Sweep ranges
    varName : string
        Storing current display variable name.
    x : list
        Storing sweep x values.
    y : list
        Storing sweep y values.
    label : string
        Storing header label and sweep time stamp
    y_limits : list
        Storing updated y-limits.
    v_limits : list
        Storing y-limits. No change.
    """

    def __init__(self, title, colormap, parent=None, width=3, height=3, dpi=100):
        self.fig = Figure(figsize=[15,5])
        plt.axis('off')
        self.axes = self.fig.add_subplot(111)
        self.fig.set_dpi( dpi )
        self.headerLabel = title

        self.figurecanvas = FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   gui.QSizePolicy.Expanding,
                                   gui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.setWindow(core.QRectF(-1. * RENDER_PIXELS/2., 1. * RENDER_PIXELS/2., 1. * RENDER_PIXELS, -1. * RENDER_PIXELS))
        self.ignorePaint = False
        self.rubberBand = gui.QRubberBand(gui.QRubberBand.Rectangle, self)
        self.zoomer = []
            
        self.origin = [RENDER_PIXELS,RENDER_PIXELS]
        self.scaleFactor = 1.0
        self.offsetX = 0.0
        self.offsetY = 0.0
        self.var_ = {}
        self.COLORBAR = True
        self.PICKER_LABEL = False
        self.cb = None
        self.cMap = colormap

        self.pressEvent = None
        self.pressed = False
        self.deltaX = 0.
        self.deltaY = 0.
        self.startX = None
        self.startY = None

        self.moveLabel = gui.QLabel("",self)
        self.moveLabel.setText("")
        self.moveLabel.hide()
        self.moveLabel.setStyleSheet("font-size:12px; margin:3px; padding:4px; background:#FFFFFF; border:2px solid #000;")

    def setWindow(self, window):
        """ initialize the full window to use for this widget """
        self._zoomWindow = window
        self._aspectRatio = window.width() / window.height()

    def resizeEvent(self, event):
        """ method called when resize window """
        sz = event.size()
        width = sz.width()
        height = sz.height()
        dpival = self.fig.dpi
        winch = float(width)/dpival
        hinch = float(height)/dpival
        self.fig.set_size_inches( winch, hinch )
        self.fig.canvas.draw()
        self.origin = [width,height]
        
    def drawSweep(self, sweep, varName, beamWidth):
        """ draw sweep """
        self.beamWidth = beamWidth
        self.ranges = sweep.ranges
        self.sweep = sweep
        self.varName = varName.lower()
        self.var_ = sweep.vars_[varName] #in list
        self.x = sweep.x
        self.y = sweep.y
        self.label = sweep.timeRange ## ['2012-02-22T20:15:00Z', '2012-02-22T20:22:59Z']

        vmin = int(ma.MaskedArray.min(self.var_)-1.)
        vmax = int(ma.MaskedArray.max(self.var_)+1.)
        self.y_limits = [vmin, vmax]
        self.v_limits = [vmin, vmax] ## will not change

        self.update_figure() #update figure

    def update_figure(self):
        """ re-plot figure """
        vmin = self.y_limits[0]
        vmax = self.y_limits[1]

        if len(self.var_) > 0:
            self.axes.clear()
            im = self.axes.pcolormesh(self.x,self.y,np.transpose(self.var_),vmin=vmin,vmax=vmax)

            if self.COLORBAR:
                self.draw_colorbar(im)

            self.axes.set_title(self.label, size=10) ## TODO: change size to be adaptive
            self.axes.set_xlabel('time (seconds since ' + self.label[0] + ')', fontsize=10)
            self.axes.set_ylabel(self.varName + ' (log scale)', fontsize=10)
            self.axes.tick_params(axis='both', which='major', labelsize=10)
            self.fig.canvas.draw()

    def draw_colorbar(self,im):
        """ draw colorbar """
        if self.cb:
            self.fig.delaxes(self.fig.axes[1])
            self.fig.subplots_adjust(right=0.90)
        self.cb = self.fig.colorbar(im)
        self.cb.ax.tick_params(labelsize=8) 
        self.cb.ax.set_picker(5)
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)

    def on_pick(self,event):
        """ method called when mouse is pressed on colorbar"""
        if True:#event.mouseevent 
            from SliderDialog import SliderDialog
            sld = SliderDialog(self.v_limits,self) ## QSlider only supports range in integer
            sld.exec_()

    def on_limit_update(self,vmin,vmax):
        """ update y limits """
        self.y_limits = [vmin,vmax]

################ below is not used ###########################################

class MyFrame(gui.QFrame):
    """ frame widget that sends an event when resized """
    sizeChanged = core.Signal(int, int, name='sizeChanged')
    
    def __init__(self, parent=None):
        super(MyFrame, self).__init__(parent)
    
    def resizeEvent(self, event):
        sz = event.size()
        width = sz.width()
        height = sz.height()
        print 'MyFrame::resizeEvent: [%d, %d] '% (width, height)
        self.sizeChanged.emit(width, height)

    def connectSizeChanged(self, method):
        """ connect a slot to our sizeChanged signal """
        self.sizeChanged.connect(method)

class RadialDisplay(gui.QWidget):
    """ display radial data

        render an array of radar/lidar data 
    """
    def __init__(self, params, parent=None):
        """ create a new Radial Display widget """
        super(RadialDisplay, self).__init__(parent)
        self.parent = parent
        
        self.PAINTED = False

        self._backgroundBrush = gui.QBrush((gui.QColor(params.background_color)))
        
        self.setWindow(core.QRect(-1 * RENDER_PIXELS, -1* RENDER_PIXELS, 2 * RENDER_PIXELS, 2 * RENDER_PIXELS))
#        policy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
#                                   QtGui.QSizePolicy.MinimumExpanding)
#        self.setSizePolicy(policy)
        new_palette = self.palette()
        new_palette.setColor(gui.QPalette.Dark, self._backgroundBrush.color())
        self.setBackgroundRole(gui.QPalette.Dark)
        self.setAutoFillBackground(True)
#        self.setAttribute(Qt.WA_OpaquePaintEvent)
        
        self.setFocusPolicy(core.Qt.StrongFocus)
        self.rays = []
        self.origin = [400,400]	
        # hack the colors for now
        self._colors = [ gui.QColor(255, 0, 0),
                         gui.QColor(0, 255, 0),
                         gui.QColor(0, 0, 255),
                         gui.QColor(50, 50, 0),
                         gui.QColor(0, 50, 50),
                         gui.QColor(50, 0, 50),
                         gui.QColor(150, 150, 0),
                         gui.QColor(0, 150, 150),
                         gui.QColor(150, 0, 150)
                         ]
        self.colorIndex = 0
        self.drawIndex = self.colorIndex
        self.pixPerGate = 6
        self.decimate_factor = 30.0
        self.decimate_factor_fixed = 30.0
        self.colorTable = Color()
        self.scaleFactor = 1.0
        self.offsetX = 0.0
        self.offsetY = 0.0

        self.ignorePaint = False
        self.origins = core.QPoint()
        self.bottomRight = core.QPoint()
        self.rubberBand = gui.QRubberBand(gui.QRubberBand.Rectangle, self)
        self.zoomer = []
        self.picker = []

#    def sizeHint(self):
#        return QtCore.QSize(800,800)
#

    def drawRay_checker(self):
        self.emit(core.SIGNAL("progressChanged"), self.i, self.nrows)
        self.timer.stop()
    
    def configure(self, gateSpacingMeters, beamWidthDeg, maxGates):
        self.gateSpacingMeters = gateSpacingMeters
        self.beamWidthDeg = beamWidthDeg
        self.maxGates = maxGates

    def setColorScale(self, color_scale_file):
        pass
    
    def setWindow(self, window):
        """ initialize the full window to use for this widget """
        self._fullWindow = window
        self._zoomWindow = window
        self._aspectRatio = window.width() / window.height()

    def drawSweep(self, sweep, varName, beamWidth):
        self.rays = sweep.rays
        self.beamWidth = beamWidth
        self.varName = varName
        self.ranges = sweep.ranges
#        self.update()  # force a paintEvent

    def drawRay(self, ray, varName):
        """ draw one ray """
        varData = ray.varDict[varName]
        angle = ray.az  ##TODO - RHI support
#        print "drawRay : ", varData.size, varName
        halfWidth = self.beamWidth / 2.0
        maxGates = varData.size

        az_a = (angle-halfWidth)/180.0 * math.pi
        az_b = (angle+halfWidth)/180.0 * math.pi

        sin1 = math.sin(az_a)
        cos1 = math.cos(az_a)
        sin2 = math.sin(az_b)
        cos2 = math.cos(az_b)

        ra = 0
        rb = 0
        decimate_factor = int(self.decimate_factor)
        
        for g in xrange(0,maxGates-decimate_factor, decimate_factor):  ##polt 1 gate for every 3 gates

            if g == 0:
                r1 = 0
            else:
                r1 = self.ranges[g-1]
            r2 = self.ranges[g]
            
            r3 = self.ranges[g+decimate_factor-1]
            r4 = self.ranges[g+decimate_factor]
            
            ra = (r1+r2)/2/1e3
            rb = (r3+r4)/2/1e3
            
            if not varData[g+1] is ma.masked: 
                color = self.colorTable(varData[g+1])  # use the value from the middle gate in the 3 gates
                self.painter.setPen(gui.QColor(color))  # QPen is for the line
                self.painter.setBrush(gui.QBrush(gui.QColor(color))) # QBrush is for the fill

                poly = gui.QPolygon([
                core.QPoint( ra * sin1, ra * cos1),
                core.QPoint( ra * sin2, ra * cos2),
                core.QPoint( rb * sin2, rb * cos2),
                core.QPoint( rb * sin1, rb * cos1),
                ])
                self.painter.drawConvexPolygon(poly)
        
        '''
        for g in xrange(0,maxGates-decimate_factor, decimate_factor):  ##polt 1 gate for every 3 gates

            if g == 0:
                r1 = 0
            else:
                r1 = self.ranges[g-1]
            r2 = self.ranges[g]
            
            r3 = self.ranges[g+decimate_factor-1]
            r4 = self.ranges[g+decimate_factor]
            
            ra = (r1+r2)/2/1e3
            rb = (r3+r4)/2/1e3
            
            import numpy.ma as ma
            if not varData[g+1] is ma.masked: 
                color = self.colorTable(varData[g+1])  # use the value from the middle gate in the 3 gates
                self.painter.setPen(gui.QColor(color))  # QPen is for the line
                self.painter.setBrush(gui.QBrush(gui.QColor(color),style=core.Qt.SolidPattern)) # QBrush is for the fill

                poly = gui.QPolygon([
                core.QPoint( ra * sin1, ra * cos1),
                core.QPoint( ra * sin2, ra * cos2),
                core.QPoint( rb * sin2, rb * cos2),
                core.QPoint( rb * sin1, rb * cos1),
                ])
                self.painter.drawConvexPolygon(poly)
        '''
        
    def paintEvent(self, event):
        rect = event.rect()
        tl = rect.topLeft()
        print 'RadialDisplay::paintEvent: [%d,%d -size = %d, %d]' % \
              (tl.x(), tl.y() , rect.width(), rect.height())
 
        self.painter = gui.QPainter()
        start = time.time()
        self.painter.begin(self)
        self.painter.setBackground(gui.QBrush(gui.QColor("white")))
        if not self.ignorePaint:

            self.painter.setWindow(self._zoomWindow)
            ## painter setup
#            self.painter.translate(self.width() / 2+self.offsetX, self.height() / 2+self.offsetY)
            side = min(self.width(), self.height())
            print 'side = ', side
            scale = side/SCALE #/ self.scaleFactor
            self.painter.scale(scale, scale)
            #self.painter.scale(side/300.00, side/300.00)
            #scale = self.scaleFactor * side/300.0
            #self.scaleFactor = scale
            self.painter.rotate(180)
            
            ## draw sweep
            self.painter.save()
            
            for r in self.rays:
                self.drawRay(r, self.varName)

            self.painter.restore()
    
        self.painter.end()
        print "RadialDisplay::paintEvent lasted %4.1f secs" %\
              (time.time() - start)

    def resizeEvent(self, event):
        """ method called when resize window """
        sz = event.size()
        width = sz.width()
        height = sz.height()
        print 'RadialDisplay::resizeEvent: [%d, %d] '% (width, height)
        d = min(width, height)
        self.updateZoomWindow(self.origin[0],int(d/2.0))
        self.origin = [int(d/2), int(d/2)]

        '''
        width_old = event.oldSize().width()
#        height_old = event.oldSize().height()
        if width_old <=0:
            width_old = width
        f = float(height) / self.origin[1]
        if self.decimate_factor >= MIN_DECIMATE and f != 1.0:
            self.decimate_factor = max(MIN_DECIMATE,self.decimate_factor_fixed/f)
        elif f == 1.0:
            self.decimate_factor = self.decimate_factor_fixed
        '''
        
    def updateZoomWindow(self,d1,d2):
        """ update zoom window when resizing the main window """
        curr_x = self._zoomWindow.x()
        curr_y = self._zoomWindow.y()
        curr_width = self._zoomWindow.width()
        curr_height = self._zoomWindow.height()
    
        zoom_x = curr_x * float(d2)/d1
        zoom_y = curr_y * float(d2)/d1
        zoom_width  = curr_width * float(d2)/d1
        zoom_height = zoom_width

        self.setZoomWindow(zoom_x, zoom_y, zoom_width, zoom_height)
        self.zoomer = []
        self.update()
        
    def getAspectRatio(self):
        return self._aspectRatio
        
    @core.Slot(int, int)
    def resize(self, width, height):
        """ method called to force a resize """
        print 'RadialDisplay::resize [%d, %d] '% (width, height)
        square_size = int(width / self.getAspectRatio() + 0.5)
        if height < square_size:
            square_size = height
        
        width = (square_size * self.getAspectRatio() + 0.5)
        # this will trigger a resize event
        self.setGeometry(0, 0, width, square_size)
        
#        self.origin = [width/2, square_size/2]
        self.origin = [int(width/2), int(square_size/2)]

    def keyPressEvent(self, event):
        """ method called when key press """
        print 'RadialDisplay::keyPressEvent: ', event.key()
        if event.key() == core.Qt.Key_C:
            self.resetFactors()
            self.update()
            event.accept()

    def mousePressEvent(self, event):
        """ method called when mouse press"""
        pos = event.pos()
        print 'RadialDisplay::mousePressEvent: [%d , %d]' % (pos.x(), pos.y())

        if event.button() == core.Qt.LeftButton:
#            if not self.rubberBand:
                self.origins = core.QPoint(event.pos())
                self.ignorePaint =  True
                self.rubberBand.setGeometry(core.QRect(self.origins, core.QSize()))
                self.rubberBand.show()
                self.oldMouseX = event.pos().x()
                self.oldMouseY = event.pos().y()
        '''
        if len(self.rays) != 0:
            if event.buttons() & core.Qt.LeftButton: ## mouse left button
                self.mouseEventLeftBtn()
#                self.dragPosition=event.globalPos()-self.frameGeometry().topLeft() 
                self.startX=event.x()
                self.startY=event.y() 
                print 'start = ', self.startX, self.startY
            
            event.accept()
        '''
    def mouseMoveEvent(self, event):
        """ method called when mouse button is pressed and moved """
        pos = event.pos()
        if not self.origins.isNull():
            self.bottomRight = event.pos()
            deltaX = pos.x() - self.oldMouseX
            deltaY = pos.y() - self.oldMouseY
            dx = dy = min(deltaX,deltaY)
            newRect = core.QRect(self.origins.x(), self.origins.y(), int(dx), int(dy))
            newRect = newRect.normalized()
            self.rubberBand.setGeometry(newRect)

    def mouseEventLeftBtn(self):
        """ method called when mouse left button is clicked on the plot """
        """ for plot zoom in """
        self.scaleFactor = self.scaleFactor * SCALE_RATE
        if self.decimate_factor > MIN_DECIMATE:
            self.decimate_factor = self.decimate_factor/SCALE_RATE
#        self.update()

    def mouseReleaseEvent(self, event):
        """ method called when mouse button is released, changing paint center """
        self.ignorePaint = False

        if event.button() == core.Qt.LeftButton:
            self.rubberBand.hide()

            if not self.origins.isNull() and not self.bottomRight.isNull():
                g = self.rubberBand.geometry()
                if g.width() <= 20:
                    ''' If the mouse hasn't moved much, assume we are clicking - zooming at the center '''
                    pass
                else:
                    mywindow = core.QRect()
                    mywindow.setRect(self._zoomWindow.x(), self._zoomWindow.y(), self._zoomWindow.width(), self._zoomWindow.height())
                    self.zoomer.append(mywindow)

                    curr_x = self._zoomWindow.x() # + self.width()/2
                    curr_y = self._zoomWindow.y() # + self.height()/2
                    curr_width = self._zoomWindow.width()
                    curr_height = self._zoomWindow.height()

                    zoom_x = float(g.x()) * curr_width / (self.origin[0]*2) + curr_x
                    zoom_y = float(g.y()) * curr_height / (self.origin[0]*2) + curr_y
                    zoom_width  = float(g.width())/(self.origin[0]*2) * curr_width
                    zoom_height = zoom_width
                                                            
                    self.setZoomWindow(zoom_x, zoom_y, zoom_width, zoom_height)
                    self.update()

        '''
        if len(self.rays) != 0:
            if event.button() == core.Qt.LeftButton: ## mouse left button
                self.offsetX = self.offsetX + (event.x() - self.startX)#/self.scaleFactor
                self.offsetY = self.offsetY + (event.y() - self.startY)#/self.scaleFactor

            self.update()
            event.accept()
        '''
            
    def resetFactors(self):
        """ reset factors """
        self.scaleFactor = 1.0
        self.decimate_factor = 30.0
        self.offsetX = 0.0
        self.offsetY = 0.0
        width = self.origin[0]
        height = self.origin[1]
        pixels = min(width, height)
        self._zoomWindow.setRect(-1 * pixels, -1* pixels, 2 * pixels, 2 * pixels)
        self.zoomer = []
        
    def changeZoomerPointer(self):
        """ method called when mouse button is pressed, changing zoomer pointer """
        if len(self.zoomer)>=1:
            zoomWindow = self.zoomer[-1]
            self._zoomWindow.setRect(zoomWindow.x(),zoomWindow.y(),zoomWindow.width(),zoomWindow.height())
            self.zoomer.pop()
            self.update()
            
    def setZoomWindow(self,x,y,width,height):
        """ set current zoom window """
        self._zoomWindow.setRect((int)(x + 0.5), (int)(y + 0.5), (int)(width + 0.5), (int)(height + 0.5))
    
