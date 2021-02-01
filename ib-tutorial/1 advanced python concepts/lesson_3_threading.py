# -*- coding: utf-8 -*-
"""
IB API - Daemon Threads

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""

import threading
import numpy as np
import time

def randNumGen():
    for a in range(10):
        print(a, np.random.randint(1,1000))
        time.sleep(1)

def greeting(text):
    for i in range(10):
        print(i, 'Hello',text)
        time.sleep(1)

# now things are running in one single thread subsequently
randNumGen()
greeting('world')

# let's see how we can change this by splitting up the process in two threads

thr1 = threading.Thread(target=greeting, args=["world"])
thr1.start() #start execution of randNumGen function on the parallel thread
thr2 = threading.Thread(target=randNumGen) #creating a separate thread to execute the randNumGen function
thr2.start()