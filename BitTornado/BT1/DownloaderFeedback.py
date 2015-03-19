# Written by Bram Cohen
# see LICENSE.txt for license information

from time import time
from cStringIO import StringIO
from urllib import quote

try:
    True
except:
    True = 1
    False = 0

class DownloaderFeedback:
    def __init__(self, choker, httpdl, add_task, upfunc, downfunc,
            remainingfunc, leftfunc, file_length, finflag, sp, statistics,
            statusfunc = None, interval = None):
        self.choker = choker
        self.httpdl = httpdl
        self.add_task = add_task
        self.upfunc = upfunc
        self.downfunc = downfunc
        self.remainingfunc = remainingfunc
        self.leftfunc = leftfunc
        self.file_length = file_length
        self.finflag = finflag
        self.sp = sp
        self.statistics = statistics
        self.lastids = []
        self.spewdata = None
        if statusfunc:
            self.autodisplay(statusfunc, interval)
        
#        self.display()

    def _rotate(self):
        cs = self.choker.connections
        for id in self.lastids:
            for i in xrange(len(cs)):
                if cs[i].get_id() == id:
                    return cs[i:] + cs[:i]
        return cs

    def spews(self):
        l = []
        cs = self._rotate()
        self.lastids = [c.get_id() for c in cs]
        for c in cs:
            a = {}
            a['id'] = c.get_readable_id()
            a['ip'] = c.get_ip()
            a['optimistic'] = (c is self.choker.connections[0])
            if c.is_locally_initiated():
                a['direction'] = 'L'
            else:
                a['direction'] = 'R'
            u = c.get_upload()
            a['uprate'] = int(u.measure.get_rate())
            a['uinterested'] = u.is_interested()
            a['uchoked'] = u.is_choked()
            d = c.get_download()
            a['downrate'] = int(d.measure.get_rate())
            a['dinterested'] = d.is_interested()
            a['dchoked'] = d.is_choked()
            a['snubbed'] = d.is_snubbed()
            a['utotal'] = d.connection.upload.measure.get_total()
            a['dtotal'] = d.connection.download.measure.get_total()
            if len(d.connection.download.have) > 0:
                a['completed'] = float(len(d.connection.download.have)-d.connection.download.have.numfalse)/float(len(d.connection.download.have))
            else:
                a['completed'] = 1.0
            a['speed'] = d.connection.download.peermeasure.get_rate()
                                               
            l = l + [a]

        for dl in self.httpdl.get_downloads():
            if dl.goodseed:
                a = {}
                a['id'] = 'http seed'
                a['ip'] = dl.baseurl
                a['optimistic'] = False
                a['direction'] = 'L'
                a['uprate'] = 0
                a['uinterested'] = False
                a['uchoked'] = False
                a['downrate'] = int(dl.measure.get_rate())
                a['dinterested'] = True
                a['dchoked'] = not dl.active
                a['snubbed'] = not dl.active
                a['utotal'] = None
                a['dtotal'] = dl.measure.get_total()
                a['completed'] = 1.0
                a['speed'] = None

                l = l + [a]

        return l


    def gather(self, displayfunc = None):
        self.statistics.update()
        s = {'stats': self.statistics}
        if self.sp.isSet():
            s['spew'] = self.spews()
        else:
            s['spew'] = None
        s['up'] = self.upfunc()
        if self.finflag.isSet():
            s['done'] = self.file_length
            return s
        s['down'] = self.downfunc()
        s['time'] = self.remainingfunc()
        done = self.file_length - self.leftfunc()
        s['done'] = done
        if self.file_length > 0:
            s['frac'] = done / float(self.file_length)
        else:
            s['frac'] = 1.0
        return s        


    def display(self, displayfunc):
        stats = self.gather()
        if self.finflag.isSet():
            displayfunc(upRate = stats['up'],
                statistics = stats['stats'], spew = stats['spew'])
        elif stats['time'] is not None:
            displayfunc(fractionDone = stats['frac'], sizeDone = stats['done'],
                downRate = stats['down'], upRate = stats['up'],
                statistics = stats['stats'], spew = stats['spew'],
                timeEst = stats['time'])
        else:
            displayfunc(fractionDone = stats['frac'], sizeDone = stats['done'],
                downRate = stats['down'], upRate = stats['up'],
                statistics = stats['stats'], spew = stats['spew'])


    def autodisplay(self, displayfunc, interval):
        self.displayfunc = displayfunc
        self.interval = interval
        self._autodisplay()

    def _autodisplay(self):
        self.add_task(self._autodisplay, self.interval)
        self.display(self.displayfunc)
