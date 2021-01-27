# -*- coding: utf-8 -*-
"""
IB API - Daemon Threads

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""

# deamon programms are generally programs that are running in the background

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

# with the therading module we can control for threads to run as a deamon

thr1 = threading.Thread(target=greeting, args=["world"])
thr1.deamon=True #defining the thread as daemon
thr1.start()

thr2 = threading.Thread(target=randNumGen)
thr2.daemon=True #defining the thread as daemon
thr2.start()

