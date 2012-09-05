#!/usr/bin/python -B

from Queue import Queue
from multiprocessing import Process, Pipe
from threading import Thread
import math

from PyQt4 import QtGui, QtCore

class Canvas(QtGui.QWidget):
    
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.initUI()
        self.nextPoint = QtCore.QPoint(0,0)
        self.finishedPoints = Queue()
        self.fractalX = -2.5
        self.fractalWidth = 3.5
        self.fractalY = -1.75
        self.fractalHeight = 3.5
        self.fractalGenerator = None
        self.newFractal()

        self.show()

    def newFractal(self):
        self.scale = self.fractalHeight / self.windowHeight
        
        if self.fractalGenerator is not None:
                self.fractalGenerator.stop()

        self.fractalGenerator = FractalGenerator(self.fractalX, self.fractalY, self.scale, self.windowWidth, self.windowHeight, self.onFinishedLevel)

        #make a new image
        self.internalImage = QtGui.QImage(self.windowWidth, self.windowHeight, QtGui.QImage.Format_RGB32)
        self.internalImage.fill(0)

        #dump any undrawn points
        while not self.finishedPoints.empty(): 
            self.finishedPoints.get()

        #make more points
        self.fractalGenerator.start()
        #clear screen 
        self.update()

    def initUI(self):
        self.windowWidth = 500
        self.windowHeight = 500
        #print "calling set geo"
        self.setGeometry(0, 0, self.windowWidth, self.windowHeight)
        #print "end call geo"        
        self.setWindowTitle('Fractal')
        #self.setStyleSheet("QWidget { background-color: White }")

        self.colors = []
        frequency = 3
        for i in xrange(0,1024):
            red   = int(math.sin(frequency*i + 0) * 127 + 128) << 16;
            green = int(math.sin(frequency*i + 2) * 127 + 128) << 8;
            blue  = int(math.sin(frequency*i + 4) * 127 + 128);
            self.colors.append(0xFF000000 + red + green + blue)

        self.colors.append(0xFF000000)
        #print self.colors

    def resizeEvent(self, event):
        nw = event.size().width()
        nh = event.size().height()
        ow = event.oldSize().width()
        oh = event.oldSize().height()
        if oh is not -1:
            self.fractalWidth *= (float(nw) / ow)
            self.fractalHeight *= (float(nh) / oh)
            self.windowWidth = nw
            self.windowHeight = nh
            self.newFractal()

    def wheelEvent(self, event):
        #print "MOUSE WHEEL", event.delta()
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
        #QtGui.QWidget.paintEvent(self,event) #super call
        #print event
        #update internal QImage
        if not self.finishedPoints.empty():
#            print "doing Something"
            iteration, points, pointsLen = self.finishedPoints.get(timeout=0.0001)
            #print iteration
            color = self.colors[iteration]
            #print iteration
            for i in xrange(0, pointsLen):
                x, y = points[i]
                
                self.internalImage.setPixel(x, y, color)
            #print "finished plotting"
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.drawImage(0, 0, self.internalImage)
        qp.end()
        if not self.finishedPoints.empty():
            self.update()
        #print "finish render"

    def onFinishedLevel(self, iteration, points, pointsLen):
        self.finishedPoints.put((iteration, points, pointsLen))
        self.update()


class FractalGenerator():
    def __init__(self, x, y, scale, width, height, onFinishLevel):
        #print x, ", ",y, ", ",scale, ", ",width, ", ",height
        self.x = x
        self.y = y
        #self.maxX = maxX
        #self.maxY = maxY
        self.width = width
        self.height = height
        self.scale = scale
        self.onFinishLevel = onFinishLevel
        self.OK = True

        self.threadPipe, self.processPipe = Pipe()

        self.thread = Thread(target=self.thread)
        self.thread.daemon = True
        self.thread.OK = True
        self.process = Process(target=self.process)
        self.process.daemon = True

    def stop(self):
        self.thread.OK = False
        self.process.terminate()

    def start(self):
        self.thread.start()
        self.process.start()

    def thread(self):
        try:
            while self.OK:
                if self.threadPipe.poll(1):
                    a = self.threadPipe.recv()
                    self.onFinishLevel(a[0],a[1],a[2])
        except EOFError:
            pass

    def process(self):
        toSolve = [0] * (self.width * self.height)
        toSolveLen = 0
        notSolved = [0] * (self.width * self.height)

        for x in range(0, self.width):
            for y in range(0, self.height):
                toSolve[toSolveLen] = (x, y, self.x + x * self.scale, self.y + y * self.scale, 0, 0)
                toSolveLen += 1

        iteration = 0
        while toSolveLen is not 0 and iteration < 1024:
            solved = [0] * toSolveLen
            #notSolved = [0] * toSolveLen
            solvedLen = 0
            notSolvedLen = 0

            for i in xrange(0, toSolveLen):
                if not self.OK:
                    return
                xs, ys, x0 , y0, x, y = toSolve[i]
                xtemp = x*x - y*y + x0
                y = 2*x*y + y0
                x = xtemp
                if x*x + y*y >= 4:
                    solved[solvedLen] = (xs, ys)
                    solvedLen += 1
                else:
                    notSolved[notSolvedLen] = (xs, ys, x0, y0, x, y)
                    notSolvedLen += 1

            tmpToSolve = toSolve
            toSolve = notSolved
            notSolved = tmpToSolve
            toSolveLen = notSolvedLen
            if solvedLen is not 0:
                #print iteration
                self.processPipe.send((iteration, solved, solvedLen))
                #self.onFinishLevel(solved, solvedLen)
            iteration += 1

        solved = [0] * notSolvedLen
        solvedLen = 0
        while solvedLen < notSolvedLen and self.OK:
            xs, ys, x0 , y0, x, y = toSolve[solvedLen]
            solved[solvedLen] = (xs, ys)
            solvedLen += 1
        if solvedLen > 0:
            self.processPipe.send((iteration, solved, solvedLen))
            #self.onFinishLevel(solved, solvedLen)
        print "Finished Making Render"

if __name__ == "__main__":
    app = QtGui.QApplication([])
    canvas = Canvas()
    app.exec_()




