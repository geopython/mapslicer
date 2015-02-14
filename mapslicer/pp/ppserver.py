#!/usr/bin/env python
# Parallel Python Software: http://www.parallelpython.com
# Copyright (c) 2005-2009, Vitalii Vanovschi
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the author nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
"""
Parallel Python Software, Network Server

http://www.parallelpython.com - updates, documentation, examples and support
forums
"""

import logging
import getopt
import sys
import socket
import thread
import random
import string
import time
import os

import pptransport
import ppauto
from pp import Server


copyright = "Copyright (c) 2005-2009 Vitalii Vanovschi. All rights reserved"
version = "1.5.7"

# compartibility with Python 2.6
try:
    import hashlib
    sha_new = hashlib.sha1
except ImportError:
    import sha
    sha_new = sha.new


class _NetworkServer(Server):
    """Network Server Class
    """

    def __init__(self, ncpus="autodetect", interface="0.0.0.0",
                broadcast="255.255.255.255", port=None, secret=None,
                timeout=None, loglevel=logging.WARNING, restart=False,
                proto=0):
        Server.__init__(self, ncpus, secret=secret, loglevel=loglevel,
                restart=restart, proto=proto)
        self.host = interface
        self.bcast = broadcast
        if port is not None:
            self.port = port
        else:
            self.port = self.default_port
        self.timeout = timeout
        self.ncon = 0
        self.last_con_time = time.time()
        self.ncon_lock = thread.allocate_lock()

        logging.debug("Strarting network server interface=%s port=%i"
                % (self.host, self.port))
        if self.timeout is not None:
            logging.debug("ppserver will exit in %i seconds if no "\
                    "connections with clients exist" % (self.timeout))
            thread.start_new_thread(self.check_timeout, ())

    def ncon_add(self, val):
        """Keeps track of the number of connections and time of the last one"""
        self.ncon_lock.acquire()
        self.ncon += val
        self.last_con_time = time.time()
        self.ncon_lock.release()

    def check_timeout(self):
        """Checks if timeout happened and shutdowns server if it did"""
        while True:
            if self.ncon == 0:
                idle_time = time.time() - self.last_con_time
                if idle_time < self.timeout:
                    time.sleep(self.timeout - idle_time)
                else:
                    logging.debug("exiting ppserver due to timeout (no client"\
                            " connections in last %i sec)", self.timeout)
                    os._exit(0)
            else:
                time.sleep(self.timeout)

    def listen(self):
        """Initiates listenting to incoming connections"""
        try:
            ssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # following allows ppserver to restart faster on the same port
            ssocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ssocket.bind((self.host, self.port))
            ssocket.listen(5)
        except socket.error:
            logging.error("Cannot create socket with port " + str(self.port)
                    + " (port is already in use)")

        try:
            while 1:
                #accept connections from outside
                (csocket, address) = ssocket.accept()
                #now do something with the clientsocket
                #in this case, we'll pretend this is a threaded server
                thread.start_new_thread(self.crun, (csocket, ))
        except:
            logging.debug("Closing server socket")
            ssocket.close()

    def crun(self, csocket):
        """Authenticates client and handles its jobs"""
        mysocket = pptransport.CSocketTransport(csocket)
        #send PP version
        mysocket.send(version)
        #generate a random string
        srandom = "".join([random.choice(string.ascii_letters)
                for i in xrange(16)])
        mysocket.send(srandom)
        answer = sha_new(srandom+self.secret).hexdigest()
        cleintanswer = mysocket.receive()
        if answer != cleintanswer:
            logging.warning("Authentification failed, client host=%s, port=%i"
                    % csocket.getpeername())
            mysocket.send("FAILED")
            csocket.close()
            return
        else:
            mysocket.send("OK")

        ctype = mysocket.receive()
        logging.debug("Control message received: " + ctype)
        self.ncon_add(1)
        try:
            if ctype == "STAT":
                #reset time at each new connection
                self.get_stats()["local"].time = 0.0
                mysocket.send(str(self.get_ncpus()))
                while 1:
                    mysocket.receive()
                    mysocket.send(str(self.get_stats()["local"].time))
            elif ctype=="EXEC":
                while 1:
                    sfunc = mysocket.creceive()
                    sargs = mysocket.receive()
                    fun = self.insert(sfunc, sargs)
                    sresult = fun(True)
                    mysocket.send(sresult)
        except:
            #print sys.excepthook(*sys.exc_info())
            logging.debug("Closing client socket")
            csocket.close()
            self.ncon_add(-1)

    def broadcast(self):
        """Initiaates auto-discovery mechanism"""
        discover = ppauto.Discover(self)
        thread.start_new_thread(discover.run,
                                ((self.host, self.port),
                                 (self.bcast, self.port)),
                               )


def parse_config(file_loc):
    """
    Parses a config file in a very forgiving way.
    """
    # If we don't have configobj installed then let the user know and exit
    try:
        from configobj import ConfigObj
    except ImportError, ie:
        print >> sys.stderr, "ERROR: You must have configobj installed to use \
configuration files. You can still use command line switches."
        sys.exit(1)

    if not os.access(file_loc, os.F_OK):
        print >> sys.stderr, "ERROR: Can not access %s." % arg
        sys.exit(1)

    # Load the configuration file
    config = ConfigObj(file_loc)
    # try each config item and use the result if it exists. If it doesn't
    # then simply pass and move along
    try:
        args['secret'] = config['general'].get('secret')
    except:
        pass

    try:
        autodiscovery = config['network'].as_bool('autodiscovery')
    except:
        pass

    try:
        args['interface'] = config['network'].get('interface',
                                                  default="0.0.0.0")
    except:
        pass

    try:
        args['broadcast'] = config['network'].get('broadcast')
    except:
        pass

    try:
        args['port'] = config['network'].as_int('port')
    except:
        pass

    try:
        args['loglevel'] = config['general'].as_bool('debug')
    except:
        pass

    try:
        args['ncpus'] = config['general'].as_int('workers')
    except:
        pass

    try:
        args['proto'] = config['general'].as_int('proto')
    except:
        pass

    try:
        args['restart'] = config['general'].as_bool('restart')
    except:
        pass

    try:
        args['timeout'] = config['network'].as_int('timeout')
    except:
        pass
    # Return a tuple of the args dict and autodiscovery variable
    return args, autodiscovery


def print_usage():
    """Prints help"""
    print "Parallel Python Network Server (pp-" + version + ")"
    print "Usage: ppserver.py [-hdar] [-n proto] [-c config_path]"\
            " [-i interface] [-b broadcast] [-p port] [-w nworkers]"\
            " [-s secret] [-t seconds]"
    print
    print "Options: "
    print "-h                 : this help message"
    print "-d                 : debug"
    print "-a                 : enable auto-discovery service"
    print "-r                 : restart worker process after each"\
            " task completion"
    print "-n proto           : protocol number for pickle module"
    print "-c path            : path to config file"
    print "-i interface       : interface to listen"
    print "-b broadcast       : broadcast address for auto-discovery service"
    print "-p port            : port to listen"
    print "-w nworkers        : number of workers to start"
    print "-s secret          : secret for authentication"
    print "-t seconds         : timeout to exit if no connections with "\
            "clients exist"
    print
    print "Due to the security concerns always use a non-trivial secret key."
    print "Secret key set by -s switch will override secret key assigned by"
    print "pp_secret variable in .pythonrc.py"
    print
    print "Please visit http://www.parallelpython.com for extended up-to-date"
    print "documentation, examples and support forums"


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 
            "hdarn:c:b:i:p:w:s:t:", ["help"])
    except getopt.GetoptError:
        print_usage()
        sys.exit(1)

    args = {}
    autodiscovery = False

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_usage()
            sys.exit()
        elif opt == "-c":
            args, autodiscovery = parse_config(arg)
        elif opt == "-d":
            args["loglevel"] = logging.DEBUG
        elif opt == "-i":
            args["interface"] = arg
        elif opt == "-s":
            args["secret"] = arg
        elif opt == "-p":
            args["port"] = int(arg)
        elif opt == "-w":
            args["ncpus"] = int(arg)
        elif opt == "-a":
            autodiscovery = True
        elif opt == "-r":
            args["restart"] = True
        elif opt == "-b":
            args["broadcast"] = arg
        elif opt == "-n":
            args["proto"] = int(arg)
        elif opt == "-t":
            args["timeout"] = int(arg)

    server = _NetworkServer(**args)
    if autodiscovery:
        server.broadcast()
    server.listen()
    #have to destroy it here explicitelly otherwise an exception
    #comes out in Python 2.4
    del server

# Parallel Python Software: http://www.parallelpython.com
