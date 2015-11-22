#!/usr/bin/env python2

import os
import sys

parent,child = os.pipe()

pid = os.fork()
if pid == 0:
    os.close(parent)
    os.dup2(child, 1)
    print("CHILD EXIT")
    sys.exit(0)

os.close(child)
import select
ep = select.epoll()
ep.register(parent, select.EPOLLIN)
while True:
    evts = ep.poll(-1,-1)
    for (fd, ev) in evts:
        print("event fd=%d, ev=%d" % (fd, ev))
        if ev & select.EPOLLIN == select.EPOLLIN:
            msg = os.read(parent, 8192)
        more = ev & (~select.EPOLLIN)
        if more:
            print("got more events: %d" % more)
            if more & select.EPOLLHUP:
                print("got HUP on pipe")
            os.close(parent)
            os.waitpid(-1, 0)
            print("waitpid %d (%d)" % (pid, os.getpid()))
            sys.exit(0)
