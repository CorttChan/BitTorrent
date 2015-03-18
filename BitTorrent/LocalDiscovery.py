# Zeroconf discovery of other BT clients on the local network.
#
# by Greg Hazel

import sys
import random
import socket
import logging
import Zeroconf
from BitTorrent.HostIP import get_deferred_host_ip, get_host_ip

discovery_logger = logging.getLogger('LocalDiscovery')
discovery_logger.setLevel(logging.DEBUG)
#discovery_logger.addHandler(logging.StreamHandler(sys.stdout))

server = None
def _get_server():
    global server
    if not server:
        server = Zeroconf.Zeroconf()
    return server

class LocalDiscovery(object):

    def __init__(self, rawserver, port, got_peer):
        self.rawserver = rawserver
        self.port = port
        self.got_peer = got_peer
        self.server = _get_server()
        self.services = []

    def announce(self, infohash, peerid):
        discovery_logger.info("announcing: %s", infohash)
        service_name = "_BitTorrent-%s._tcp.local." % infohash
        
        # do I need to keep the browser around?
        browser = Zeroconf.ServiceBrowser(self.server, service_name, self)

        df = get_deferred_host_ip()
        df.addCallback(self._announce2, peerid, service_name)
        return df

    def _announce2(self, ip, peerid, service_name):
        addr = socket.inet_aton(ip)
        service = Zeroconf.ServiceInfo(service_name,
                                       '%s.%s' % (peerid, service_name),
                                       address = addr,
                                       port = self.port,
                                       weight = 0, priority = 0,
                                       properties = {}
                                      )
        self.server.registerService(service)
        self.services.append(service)

    def addService(self, server, type, name):
        discovery_logger.info("Service %s added", repr(name))
        # Request more information about the service
        info = server.getServiceInfo(type, name)
        if info and info.address is not None:
            host = socket.inet_ntoa(info.address)
            try:
                port = int(info.port)
            except:
                discovery_logger.exception("Invalid Service (port not an int): "
                                           "%r" % info.__dict__)
                return

            addr = (host, port)
            ip = get_host_ip()

            if addr == (ip, self.port):
                # talking to self
                return

            infohash = name.split("_BitTorrent-")[1][:-len("._tcp.local.")]

            discovery_logger.info("Got peer: %s:%d %s", host, port, infohash)

            # BUG: BitTorrent is so broken!
            t = random.random() * 3

            self.rawserver.external_add_task(t, self._got_peer, addr, infohash)

    def removeService(self, server, type, name):
        discovery_logger.info("Service %s removed", repr(name))

    def _got_peer(self, addr, infohash):
        if self.got_peer:
            self.got_peer(addr, infohash)
            
    def stop(self):
        self.port = None
        self.got_peer = None
        for service in self.services:
            self.server.unregisterService(service)
        del self.services[:]

        
if __name__ == '__main__':
    import string
    import threading
    from BitTorrent.RawServer_twisted import RawServer

    rawserver = RawServer()

    def run_task_and_exit():
        l = LocalDiscovery(rawserver, 6881,
                           lambda *a:sys.stdout.write("GOT: %s\n" % str(a)))
        l.announce("63f27f5023d7e49840ce89fc1ff988336c514b64",
                   ''.join(random.sample(string.letters, 5)))
    
    rawserver.add_task(0, run_task_and_exit)

    rawserver.listen_forever()
         
    
