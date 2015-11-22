#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
import sys
import os
import pty
from tastypy.core import config as coreconfig
from tastypy.core.logger import debug
from tastypy.core.events import EventObject, EventService, EVREAD
import copy
print("spawner %s " % ','.join(sys.argv[1:]))

# childcount = coreconfig.numcpus
childcount = 1
pmap = dict()
evsv = EventService.instance()

program = sys.argv[1]
cf_mod = "tastypy.programs.%s.configurations.spawner" % program
try:
    cf = __import__(cf_mod)
except ImportError:
    childcount = coreconfig.numcpus


class ChildPipe(EventObject):

    def __init__(self, fd, pid_):
        self.pid = pid_
        self.fd = fd
        # self.fh = os.fdopen(fd)
        EventObject.__init__(self, EVREAD)

    def close(self):
        # self.fh.close()
        os.close(self.fd)

    def fileno(self):
        return self.fd

    def callback(self, events):
        debug("spawner: callback(pid=%d,events=%d,fd=%d)" % (self.pid, events, self.fd))
        if events & EVREAD:
            debug("spawner: EVREAD")
            # TODO: reading from fh=fdopen(self.fd) was causing too much of a buffering, check WHY
            buf = os.read(self.fd, 32768)
            print("CHILD-%d: %s" % (self.pid, buf))
        more = events & (~EVREAD)
        if more:
            debug("CHILD %d died" % self.pid)
            self.close()
            try:
                (epid, status) = os.waitpid(self.pid, 0)
            except OSError as ose:
                debug(ose)
                pass
            else:
                sig = status & 0x0f
                rc = (status >> 8) & 0x0f
                debug("pid=%d, status=%d, sig=%d, rc=%d" % (epid, status, sig, rc))

for p in range(0, childcount):
    (parent, child) = pty.openpty()
    pid = os.fork()
    if pid == 0:
        os.close(parent)
        os.dup2(child, 1)
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['PYTHON'] = 'python2 -u'
        os.execvp(sys.argv[1], sys.argv[1:])
    else:
        print("forked %s parent=%d child=%d pid=%d" % (sys.argv[1], parent, child, pid))
        os.close(child)
        pmap[pid] = {'p0': ChildPipe(parent, pid)}

evsv.listen()
