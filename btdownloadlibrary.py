# Written by Bram Cohen
# see LICENSE.txt for license information

from BitTorrent import PSYCO
if PSYCO.psyco:
    try:
        import psyco
        assert psyco.__version__ >= 0x010100f0
        psyco.full()
    except:
        pass

import BitTorrent.download
from threading import Event

def dummychoose(default, size, saveas, dir):
    return saveas

def dummydisplay(fractionDone = None, timeEst = None, 
        downRate = None, upRate = None, activity = None):
    pass

def dummyerror(message):
    pass

def download(url, file):
    ev = Event()
    def fin(ev = ev):
        ev.set()
    BitTorrent.download.download(['--url', url, '--saveas', file], 
        dummychoose, dummydisplay, fin, dummyerror, ev, 80)
