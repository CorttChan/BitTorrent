# Written by Edward Keyes
# see LICENSE.txt for license information

from time import time
from copy import copy

true = 1
false = 0

class Statistics:
    def __init__(self, upmeasure, downmeasure, connecter, httpdl, rerequest, fdatflag):
        self.upmeasure = upmeasure
        self.downmeasure = downmeasure
        self.connecter = connecter
        self.httpdl = httpdl
        self.downloader = connecter.downloader
        self.picker = connecter.downloader.picker
        self.storage = connecter.downloader.storage
        self.torrentmeasure = connecter.downloader.totalmeasure
        self.rerequest = rerequest
        self.fdatflag = fdatflag
        self.fdatactive = false
        self.upTotal = 0.0
        self.downTotal = 0.0
        self.shareRating = 0.0
        self.numSeeds = 0
        self.numOldSeeds = 0
        self.numCopies = 0.0
        self.numCopies2 = 0.0
        self.numPeers = 0
        self.last_failed = 1
        self.external_connection_made = 0
        self.piecescomplete = None
        self.backgroundallocating = false
        self.storage_totalpieces = len(self.storage.hashes)


    def set_dirstats(self, files, numpieces, piece_length):
        self.piecescomplete = 0
        self.filelistupdated = true
        self.bgalloc_wasactive = false
#        self.filenames = {}
        self.filepieces = {}
        self.filepieces2 = {}
        self.filecomplete = {}
        self.fileinplace = {}
        start = 0L
        for i in range(len(files)):
#            self.filenames[i] = files[i][0]
            self.filepieces[i] = []
            self.filepieces2[i] = []
            l = files[i][1]
            if l == 0:
                self.filecomplete[i] = true
                self.fileinplace[i] = true
            else:
                self.filecomplete[i] = false
                self.fileinplace[i] = false
                for piece in range(int(start/piece_length),
                                   int((start+l-1)/piece_length)+1):
                    self.filepieces[i].append(piece)
                    self.filepieces2[i].append(piece)
                start += l


    def update(self):
        self.upTotal = self.upmeasure.get_total()
        self.downTotal = self.downmeasure.get_total()
        self.last_failed = self.rerequest.last_failed
        if self.connecter.external_connection_made:
            self.external_connection_made = 1
        if self.downTotal > 0:
            self.shareRating = float(self.upTotal)/self.downTotal
        else:
            if self.upTotal == 0:
               self.shareRating = 0.0
            else:
               self.shareRating = -1.0
        self.downloader = self.connecter.downloader
        self.picker = self.downloader.picker
        self.torrentmeasure = self.downloader.totalmeasure
        self.torrentRate = self.torrentmeasure.get_rate()
        self.torrentTotal = self.torrentmeasure.get_total()
        self.numSeeds = 0
        for download in self.downloader.downloads:
            if download.unhave == 0:
                self.numSeeds+=1
        self.numOldSeeds = self.downloader.num_disconnected_seeds()
        self.numPeers = len(self.downloader.downloads)-self.numSeeds
        self.numCopies = -self.numSeeds
        for i in range(len(self.picker.crosscount)):
            if self.picker.crosscount[i]==0:
                self.numCopies+=1
            else:
                self.numCopies+=1-float(self.picker.crosscount[i])/self.picker.numpieces
                break
        self.numCopies2 = -self.numSeeds
        for i in range(len(self.picker.crosscount2)):
            if self.picker.crosscount2[i]==0:
                self.numCopies2+=1
            else:
                self.numCopies2+=1-float(self.picker.crosscount2[i])/self.picker.numpieces
                break
        self.numSeeds += self.httpdl.seedsfound
        if self.numPeers==0:
            self.percentDone = 0.0
        else:
            self.percentDone = 100.0*(float(self.picker.totalcount)/self.picker.numpieces-self.numSeeds)/self.numPeers

        self.backgroundallocating = self.storage.bgalloc_active
        self.storage_active = len(self.storage.stat_active)
        self.storage_new = len(self.storage.stat_new)
        self.storage_dirty = len(self.storage.dirty)
        self.storage_numcomplete = self.storage.stat_numfound + self.storage.stat_numdownloaded
        self.storage_justdownloaded = self.storage.stat_numdownloaded
        self.storage_numflunked = self.storage.stat_numflunked

        self.peers_kicked = self.downloader.kicked.items()
        self.peers_banned = self.downloader.banned.items()

        if self.fdatflag.isSet():
            if not self.fdatactive:
                self.fdatactive = true
                if self.piecescomplete is not None:
                    self.piecescomplete = 0
        else:
            self.fdatactive = false

        if self.fdatflag.isSet() and self.piecescomplete is not None:
            if ( self.piecescomplete != self.picker.numgot
                 or self.bgalloc_wasactive or self.storage.bgalloc_active ) :
                    self.piecescomplete = self.picker.numgot
                    self.bgalloc_wasactive = self.storage.bgalloc_active
                    self.filelistupdated = true
                    for i in range(len(self.filecomplete)):
                        if not self.filecomplete[i]:
                            newlist = []
                            for piece in self.filepieces[i]:
                                if not self.storage.have[piece]:
                                    newlist.append(piece)
                            self.filepieces[i] = newlist
                            if not newlist:
                                self.filecomplete[i] = true
                        if self.filecomplete[i] and not self.fileinplace[i]:
                            while self.filepieces2[i]:
                                piece = self.filepieces2[i][-1]
                                if self.storage.places[piece] != piece:
                                    break
                                del self.filepieces2[i][-1]
                            if not self.filepieces2[i]:
                                self.fileinplace[i] = true