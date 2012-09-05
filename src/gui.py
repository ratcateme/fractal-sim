#!/usr/bin/python -B
from PyQt4 import QtGui, QtCore
from display import FractalDisplay
from server import FractalServer

class Window(QtGui.QMainWindow):
    def __init__(self, fractalDisplay, fractalServer, *args):
        QtGui.QMainWindow.__init__(self, *args)
        
        self.makeStatusBar(fractalDisplay, fractalServer)
        self.setCentralWidget(fractalDisplay)
        self.fullScreen = False
        self.show()

    def makeStatusBar(self, fractalDisplay, fractalServer):
        self._statusBar = StatusBar(fractalDisplay, fractalServer, self)
        self.setStatusBar(self._statusBar)
        self.showStatusBar = True

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F:
            if self.fullScreen:
                self.showNormal()
            else:
                self.showFullScreen()
            self.fullScreen = not self.fullScreen

class StatusBar(QtGui.QStatusBar):
    def __init__(self, fractalDisplay, fractalServer, *args):
        QtGui.QStatusBar.__init__(self, *args)
        self.fractalDisplay = fractalDisplay
        self.fractalServer = fractalServer
        
        self.iterationsButton = QtGui.QPushButton(self)
        self.iterationsButton.setText("Max Iterations: {0}".format(fractalServer.iterations))
        self.iterationsButton.clicked.connect(self.iterationClicked)
        self.addWidget(self.iterationsButton)
        
        self.progress = QtGui.QProgressBar(self)
        self.progress.setMinimum(0)
        self.progress.setMaximum(fractalDisplay.windowWidth * fractalDisplay.windowHeight)
        self.progress.setValue(0)

        fractalDisplay.madeProgress.connect(lambda val:self.progress.setValue(val))
        fractalDisplay.newProgressMax.connect(lambda val:self.progress.setMaximum(val))
        self.addWidget(self.progress)

        #  1 = Mandelbrot
        #  2 = Julia
        #  3 = Burning Ship
        #  4 = Collatz
        #  5 = Mandelbar
        self.fractalTypes = {'Mandelbrot'   : (1, -2.5,  -1.75, 3.5),
                             'Julia'        : (2, -2.25, -2.25, 4.5),
                             'Burning Ship' : (3, -2.5,  -1.75, 3.5),
                             'Collatz'      : (4, -2.5,  -1.75, 3.5),
                             'Mandelbar'    : (5, -2.5,  -1.75, 3.5)}
        self.typePicker = QtGui.QComboBox(self)
        for fractalType in ['Mandelbrot', 'Mandelbar', 'Julia', 'Burning Ship', 'Collatz']:
            self.typePicker.addItem(fractalType)
        #self.typePicker.
        
        self.connect(self.typePicker, QtCore.SIGNAL("activated(const QString&)"), self.updateFractalType)
        self.addWidget(self.typePicker)

        self.newFractalButton = QtGui.QPushButton("Restart Render", self)
        self.newFractalButton.clicked.connect(lambda: self.fractalServer.newFractal())
        self.addWidget(self.newFractalButton)

        self.clientNumber = QtGui.QLabel("0 Clients", self)
        self.fractalServer.clientNumber.connect(self.upadteClientNumber)
        self.addWidget(self.clientNumber)

    def upadteClientNumber(self, num):
        if num == 1:
            self.clientNumber.setText("1 Client")
        else:
            self.clientNumber.setText("{0} Clients".format(num))

    def updateFractalType(self, newType):
        code, fractalX, fractalY, size = self.fractalTypes[str(newType)]
        
        if self.fractalServer.fractInfo[0] is not code or code is 2:
            re = self.fractalServer.fractInfo[1]
            im = self.fractalServer.fractInfo[2]
            if code is 2:
                base = str(self.fractalServer.fractInfo[1]) + " "
                if self.fractalServer.fractInfo[2] >= 0:
                    base += "+"
                base += str(self.fractalServer.fractInfo[2])
                ok = True
                while ok:
                    text,ok = QtGui.QInputDialog.getText(self, "Complex c", "Please enter a new Complex", text=base)
                    parts = text.split(" ")
                    if len(parts) is 2:
                        try:
                            re, im = (float(parts[0]), float(parts[1]))
                            break
                        except ValueError:
                            pass
            windowSize = min(self.fractalDisplay.windowWidth, self.fractalDisplay.windowHeight)
            print windowSize
            scale = float(size) / windowSize 
            self.fractalDisplay.fractalWidth = scale * self.fractalDisplay.windowWidth
            self.fractalDisplay.fractalHeight = scale * self.fractalDisplay.windowHeight
            
            self.fractalDisplay.fractalX = fractalX - (self.fractalDisplay.fractalWidth - size) / 2
            self.fractalDisplay.fractalY = fractalY - (self.fractalDisplay.fractalHeight - size) / 2

            print self.fractalDisplay.fractalX, ",", self.fractalDisplay.fractalY
            print self.fractalDisplay.fractalWidth, "x", self.fractalDisplay.fractalHeight
            self.fractalServer.fractInfo = (code, re, im)
            self.fractalDisplay.newFractal()
        
    def updateProgress(self, amount=None, newMax=None):
        if amount is not None:
            #print "updating progress to:", amount, " ", self.progress.maximum(), " ", self.progress.minimum()
            self.progress.setValue(amount)
            self.progress.update()
        if newMax is not None:
            #print "Updating new Max"
            self.progress.setMaximum(newMax)
        
    def iterationClicked(self, event):
        iterations, ok = QtGui.QInputDialog.getInt(self, "Iterations", "Enter new Iterations",
                                                    value=self.fractalServer.iterations, min=1)
        if ok:
            self.fractalServer.iterations = iterations
            self.fractalDisplay.newFractal()
            self.iterationsButton.setText("Max Iterations: {0}".format(iterations))
            


if __name__ == "__main__":
    app = QtGui.QApplication([])
    display = FractalDisplay()
    server = FractalServer()
    display.startGenerator = server.startGenerator
    server.onFinishedPoints = display.onFinishedPoints
    server.newFractal = display.newFractal
    window = Window(display, server)
    app.exec_()











