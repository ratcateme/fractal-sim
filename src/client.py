#!/usr/bin/python -B

# FractType:
#  1,0 = Mandelbrot
#  2,0 = Julia
#  3,1 = Burning Ship
#  4,2 = Collatz
#  5,3 = Mandelbar

import math
import time
import colorsys
from multiprocessing.managers import BaseManager
from multiprocessing import Process
import multiprocessing
import multiprocessing.reduction
from threading import Thread
import pickle
import sys

class FractalClient(Process):
    def run(self):
        QueueManager.register('registerClient')
        QueueManager.register('getGeneration')
        QueueManager.register('getResultsPipe')
        QueueManager.register('getPollPipe')
       
        self.manager = QueueManager(address=('127.0.0.1', 50000), authkey='FRACTALZ')
        self.manager.connect()
        clientID = self.manager.registerClient()._getvalue()
        print "connected", clientID
        self.resultsPipe = self.manager.getResultsPipe(clientID)
        self.pollPipe = self.manager.getPollPipe(clientID)
        
        self.OK = False
        self.NOT_DEAD = True
        self.generation = -1

        self.solveThread = Thread(target=self.solve)
        self.solveThread.daemon = True
        self.solveThread.start()

        self.pollThread = Thread(target=self.poll)
        self.pollThread.daemon = True
        self.pollThread.start()

        self.checker()
        
    def checker(self):
        try:
            while self.NOT_DEAD:
                if self.OK and self.generation is not self.manager.getGeneration()._getvalue():
                    self.OK = False
                time.sleep(0.2)
        except IOError:
            self.NOT_DEAD = False
        except EOFError:
            self.NOT_DEAD = False
        sys.exit(0)

    def poll(self):
        try:
            while self.NOT_DEAD:
                self.pollPipe.send((1,))
                time.sleep(1.0)
        except IOError:
            self.NOT_DEAD = False
        except EOFError:
            self.NOT_DEAD = False

    def solve(self):
        #build color map
        colors = []
        for h in xrange(0,3600):
            r, g, b = colorsys.hsv_to_rgb(float(h) / float(3600), 1.0, 1.0)
            rgba = 0xFF000000 + (int(r * 255) << 16) + (int(g * 255) << 8) + int(b * 255)
            colors.append(rgba)
        try:
            while self.NOT_DEAD:
                self.generation, maxIterations, fractInfo, c, step, windowWidth, windowHeight, fractalX, fractalY, scaleX, scaleY = self.resultsPipe.recv()
                if self.generation is not self.manager.getGeneration()._getvalue():
                    continue
                if fractInfo[0] == 3:
                    caculationType = 1
                elif fractInfo[0] == 4:
                    caculationType = 2
                elif fractInfo[0] == 5:
                    caculationType = 3
                else:
                    caculationType = 0
                
		self.OK = True
                print "SOLVING"
                
                #make points
                count = 0
                toSolve = [0] * ((windowWidth * windowHeight) / step + 1)
                toSolveLen = 0
                for x in xrange(0, windowWidth):
                    for y in xrange(0, windowHeight):
                        if count % step is c:
                            # Mandelbrot, Bunring Ship, Mandelbar
                            if fractInfo[0] is 1 or fractInfo[0] is 3 or fractInfo[0] is 5: 
                                toSolve[toSolveLen] = (x, y, fractalX + x * scaleX, fractalY + y * scaleY, 0, 0)
                            # Julia Set
                            elif fractInfo[0] is 2:
                                toSolve[toSolveLen] = (x, y, fractInfo[1], fractInfo[2],
                                                        fractalX + x * scaleX, fractalY + y * scaleY)
                            # Collatz conjecture
                            elif fractInfo[0] is 4:
                                toSolve[toSolveLen] = (x, y, 0, 0, fractalX + x * scaleX, fractalY + y * scaleY)
                            toSolveLen += 1
                        count += 1
                notSolved = [0] * toSolveLen
                iteration = 0
                while toSolveLen is not 0 and iteration < maxIterations:
                    solved = [0] * toSolveLen
                    solvedLen = 0
                    notSolvedLen = 0

                    for i in xrange(0, toSolveLen):
                        if not self.OK or not self.NOT_DEAD:
                            break
                        xs, ys, x0 , y0, x, y = toSolve[i]
                        if caculationType is 2: # Collatz
                            xtemp = 0.25 * (2 + 7 * x - (2 + 5 * x) *  math.cos(math.pi * x) * math.cosh(math.pi * y))
                            y     = 0.25 * (    7 * y - (    5 * y) * -math.sin(math.pi * x) * math.sinh(math.pi * y))
                            x = xtemp
                            if x*x + y*y >= 100: #dont really know what thsi knumber should be...
                                solved[solvedLen] = (xs, ys, colors[iteration % 3600])
                                solvedLen += 1
                            else:
                                notSolved[notSolvedLen] = (xs, ys, x0, y0, x, y)
                                notSolvedLen += 1
                        else: #Mandelbrot, Julia, Burning Ship, Mandelbar 
                            if caculationType is 1: # abs for burning ship
                                x = abs(x)
                                y = abs(y)
                            if caculationType is 3: # bar for Mandelbar
                                y = -y
                            xtemp = x*x - y*y + x0
                            y = 2*x*y + y0
                            x = xtemp
                            if x*x + y*y >= 4:
                                mu = iteration + 1 - math.log(math.log(x*x + y*y)) / math.log(2)
                                solved[solvedLen] = (xs, ys, colors[int((mu * 50)) % 3600])
                                solvedLen += 1
                            else:
                                notSolved[notSolvedLen] = (xs, ys, x0, y0, x, y)
                                notSolvedLen += 1
                                
                    if not self.OK or not self.NOT_DEAD:
                        break
                    tmpToSolve = toSolve
                    toSolve = notSolved
                    notSolved = tmpToSolve
                    toSolveLen = notSolvedLen
                    if solvedLen is not 0:
                        self.resultsPipe.send((self.generation, iteration, solved[0:solvedLen], False))
                    iteration += 1
                if not self.OK or not self.NOT_DEAD:
                    continue
                solved = [0] * notSolvedLen
                solvedLen = 0
                while solvedLen < notSolvedLen and self.OK:
                    xs, ys, x0 , y0, x, y = toSolve[solvedLen]
                    solved[solvedLen] = (xs, ys, 0)
                    solvedLen += 1
                if solvedLen > 0: # balck parts
                    self.resultsPipe.send((self.generation, iteration, solved[0:solvedLen], True))
                print "Finished Making Render"
        except IOError:
            self.NOT_DEAD = False
        except EOFError:
            self.NOT_DEAD = False

class QueueManager(BaseManager): pass

if __name__ == "__main__":
    import multiprocessing
    clients = set()
    for i in xrange(0, multiprocessing.cpu_count()):
    #for i in xrange(0, 1):
        client = FractalClient()
        client.daemon = True
        client.start()
        clients.add(client)

    while True:
        time.sleep(0.5)
        dead = set()
        for c in clients:
            if not c.is_alive():
                dead.add(c)
        if len(dead) is not 0:
            print "making new clients"
            clients -= dead
            for i in xrange(0, len(dead)):
                client = FractalClient()
                client.daemon = True
                client.start()
                clients.add(client)







