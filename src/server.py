#!/usr/bin/python -B

# FractType:
#  1 = Mandelbrot
#  2 = Julia
#  3 = Burning Ship
#  4 = Collatz
#  5 = Mandelbar

from Queue import Empty
from multiprocessing.managers import BaseManager
from multiprocessing import Lock, Queue, Process, Pipe
from multiprocessing.reduction import reduce_connection
import threading
import random
import time
import pickle
from PyQt4 import QtCore
import config

class FractalServer(QtCore.QObject):
    clientNumber = QtCore.pyqtSignal(int)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.generation = 1
        self.clients = 0
        self.clientID = 0
        self.iterations = 1024
        self.generationLock = Lock()
        self.clientLock = Lock()

        self.fractInfo = (1,-0.4,0.6)
        
        self.serverThread = threading.Thread(target=self.startServer)
        self.serverThread.daemon = True
        self.serverThread.start()

        self.resultThreads = []
        self.clientPipes = []
        self.healdPipes = dict()
        self.newFractal = lambda *args: None

    def startGenerator(self, fractalX, fractalY, windowWidth, windowHeight, scaleX, scaleY, onFinishedPoints):
        self.generationLock.acquire()
        self.generation += 1
        self.fractalX = fractalX
        self.fractalY = fractalY
        self.windowWidth = windowWidth
        self.windowHeight = windowHeight
        self.scaleX = scaleX
        self.scaleY = scaleY
        self.onFinishedPoints = onFinishedPoints
        
        if self.clients < 1:
            self.generationLock.release()
            return #dont do anything wait for more clients 
        else:
            clients = self.clients
        # make all the pixles
        for c in xrange(0, clients):
            self.clientPipes[c].send((self.generation, self.iterations, self.fractInfo, c, clients, self.windowWidth, 
                                         self.windowHeight, self.fractalX, self.fractalY, self.scaleX, self.scaleY))
        self.generationLock.release()

    def startServer(self):
        QueueManager.register('registerClient', callable=self.registerClient)
        QueueManager.register('getGeneration', callable=lambda: self.generation)
        QueueManager.register('getResultsPipe', callable=self.getResultsPipe)
        QueueManager.register('getPollPipe', callable=self.getPollPipe)
        m = QueueManager(address=('', config.config['ServerPort']), authkey=config.config['AuthKey'])
        print "starting"
        s = m.get_server()
        s.serve_forever()
        
    def registerClient(self):
        self.clientLock.acquire()
        clientID = self.clientID
        self.clientID += 1
        self.clients += 1
        self.clientNumber.emit(self.clients)
        
        print "got new client", clientID

        resultsClientPipe, resultsServerPipe = Pipe(duplex=True)
        pollClientPipe, pollServerPipe = Pipe(duplex=True)

        thread = threading.Thread(target=self.resultsCollector, args=(resultsServerPipe, pollServerPipe, clientID))
        thread.daemon = True

        self.clientPipes.append(resultsServerPipe)
        self.healdPipes[clientID] = (resultsClientPipe, pollClientPipe)
        thread.start()
        self.clientLock.release()
        
        return clientID

    def getResultsPipe(self, clientID):
        return self.healdPipes[clientID][0]

    def getPollPipe(self, clientID):
        return self.healdPipes[clientID][1]

    def resultsCollector(self, resultsPipe, pollPipe, cid):
        lastPoll = time.time()
        try:        
            while True:
                time.sleep(0.2)
                if resultsPipe.poll():
                    generation, iteration, points, black = resultsPipe.recv()
                    if generation is self.generation:
                        self.onFinishedPoints(iteration, points, black)
                while pollPipe.poll(0):
                    pollPipe.recv()
                    lastPoll = time.time()
                if time.time() - lastPoll > 5: 
                    raise EOFError()
        except EOFError:
            print "lost client", cid
            self.clientLock.acquire()
            thread = threading.currentThread()
            self.clientPipes.remove(resultsPipe)
            self.clients -= 1
            self.clientNumber.emit(self.clients)
            self.clientLock.release()
                
class QueueManager(BaseManager): pass




if __name__ == "__main__":
    from display import FractalDisplay
    from PyQt4 import QtGui
    
    # setup Server    
    server = FractalServer()
    
    # setup GUI
    app = QtGui.QApplication([])
    display = FractalDisplay()
    
    # link canvas and server
    display.startGenerator = server.startGenerator   
    server.onFinishedPoints = display.onFinishedPoints
    display.newFractal()
    
    # open GUI will call spark resize event that will kick off the generators
    app.exec_()
