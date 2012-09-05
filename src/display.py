#!/usr/bin/python -B

from Queue import Queue
#from multiprocessing import Process, Pipe
#from threading import Thread
import math

from PyQt4 import QtGui, QtCore

class FractalDisplay(QtGui.QWidget):
    madeProgress = QtCore.pyqtSignal(int)
    newProgressMax = QtCore.pyqtSignal(int)
    
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        #(-10,10,-2,2
        self.initUI()
        self.finishedPoints = Queue()
        self.fractalX = -2.5
        self.fractalWidth = 3.5
        self.fractalY = -1.75
        self.fractalHeight = 3.5
        self.scaleX = 0
        self.scaleY = 0
        self.startGenerator = lambda *args: None
        self.newImage = True

    def newFractal(self, newImage=True):
        print "Making new Fractal"
        self.count = 0
        self.madeProgress.emit(0)
        self.scaleX = self.fractalWidth / self.windowWidth
        self.scaleY = self.fractalHeight / self.windowHeight

        
        #make a new image
        self.newImage = newImage
        #dump any undrawn points
        while not self.finishedPoints.empty(): 
            self.finishedPoints.get()
        
        self.startGenerator(self.fractalX, self.fractalY, self.windowWidth, self.windowHeight,
                            self.scaleX, self.scaleY, self.onFinishedPoints)
        #clear screen 
        self.update()

    def updateFractalPos(x, y, size):
            windowSize = min(self.windowWidth, self.windowHeight)
            scale = windowSize / size
            self.fractalWidth = scale / self.windowWidth
            self.fractalHeight = scale / self.windowHeight
            
            origXCenter = x + size / 2
            self.fractalX = -(self.fractalWidth - size) / 2 + origXCenter

            origYCenter = y + size / 2
            self.fractalY = (self.fractalHeight - size) / 2 + origYCenter

    def initUI(self):
        self.windowWidth = 600
        self.windowHeight = 600

        self.setMinimumSize(self.windowWidth, self.windowHeight)
        
        #self.colors = []
        #frequency = 3
        #for i in xrange(0,1024):
        #    red   = int(math.sin(frequency*i + 0) * 127 + 128) << 16;
        #    green = int(math.sin(frequency*i + 2) * 127 + 128) << 8;
        #    blue  = int(math.sin(frequency*i + 4) * 127 + 128);
        #    self.colors.append(0xFF000000 + red + green + blue)

        #self.colors.append(0xFF000000)
        #print self.colors

    def mouseReleaseEvent(self, event):
        move = event.pos() - self.lastPress
        if move.manhattanLength() > 10:
            print "Moving"
            x = -move.x()
            y = -move.y()
            
            self.fractalX += x * self.scaleX
            self.fractalY += y * self.scaleY
            self.newFractal()

    def mousePressEvent(self, event):
        self.lastPress = event.pos()

    def resizeEvent(self, event):
        print "Resizing"
        nw = event.size().width()
        nh = event.size().height()
        ow = event.oldSize().width()
        oh = event.oldSize().height()
        if oh is not -1:
            oldWidth = self.fractalWidth
            oldHeight = self.fractalHeight
            self.fractalWidth *= (float(nw) / ow)
            self.fractalHeight *= (float(nh) / oh)
            self.fractalX -= (self.fractalWidth - oldWidth) / 2
            self.fractalY -= (self.fractalHeight - oldHeight) / 2
            self.windowWidth = nw
            self.windowHeight = nh
            self.newProgressMax.emit(nw * nh)
        self.newFractal()

    def wheelEvent(self, event):
        print "MOUSE WHEEL"
        if event.delta() > 0:
            xScale = (self.fractalWidth) / float(self.windowWidth)
            yScale = (self.fractalHeight) / float(self.windowHeight)
            mx = event.x() * xScale
            my = event.y() * yScale
            self.fractalX = self.fractalX + mx * 0.5
            self.fractalY = self.fractalY + my * 0.5
            self.fractalWidth *= 0.5
            self.fractalHeight *= 0.5
            self.newFractal()
        else:
            xScale = (self.fractalWidth) / float(self.windowWidth)
            yScale = (self.fractalHeight) / float(self.windowHeight)
            mx = event.x() * xScale
            my = event.y() * yScale
            self.fractalX = self.fractalX - mx
            self.fractalY = self.fractalY - my
            self.fractalWidth *= 2
            self.fractalHeight *= 2
            self.newFractal()

    def paintEvent(self, event):
        if self.newImage:
            self.internalImage = QtGui.QImage(self.windowWidth, self.windowHeight, QtGui.QImage.Format_RGB32)
            self.internalImage.fill(0)
            self.newImage = False
        while not self.finishedPoints.empty():
            iteration, points, black = self.finishedPoints.get(timeout=0.0001)
            
            for x, y, color in points:
                self.count += 1
                self.internalImage.setPixel(x, y, color)
            self.madeProgress.emit(self.count)

        qp = QtGui.QPainter()
        qp.begin(self)
        qp.drawImage(0, 0, self.internalImage)
        qp.end()
        if not self.finishedPoints.empty():
            self.update()

    def onFinishedPoints(self, iteration, points, black):
        self.finishedPoints.put((iteration, points, black))
        self.update()





