# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

import os
import pty
import sys


# from tastypy.libs.core.utils import load_program_configuration, load_cf_param

# make sure we don't have pending tasks in slave queues from previous crashes
from tastypy.core.events import EventService, EVREAD
from tastypy.core.logger import debug
from tastypy.core.fsnote import FSNotifier, IN_CREATE  # , IN_DELETE
from tastypy.programs.taskmaster import config
from signal import SIGTERM


class TaskManager(object):

    def cleanup(self, que):
        qdir = os.path.join(config.runqueues, que)
        try:
            os.kill(int(que), 0)
        except OSError:
            for qtask in os.listdir(qdir):
                os.rename(os.path.join(qdir, qtask), os.path.join(config.pendingqueue, qtask))
                self.pendingtasks.append(qtask)

    def __init__(self):
        for path in (config.pendingqueue, config.runqueues):
            if not os.path.exists(path):
                os.makedirs(path)
            else:
                if not os.path.isdir(path):
                    raise RuntimeError("%s is not a directory" % path)

        self.runners = dict()
        self.pipes = dict()
        self.pendingtasks = list()
        self.events = EventService.instance()

        for que in filter(lambda q: os.path.isdir(os.path.join(config.slavequeues, q)), os.listdir(config.slavequeues)):
            self.cleanup(int(que))

        self.notifier = FSNotifier()
        self.notifier.watch(config.masterqueue, IN_CREATE, self.assign)
        self.notifier.watch(config.runqueues, IN_CREATE, self.enslave)

    def start(self):
        for _ in range(0, config.runnercount):
            self.spawn()
        self.events.listen()

    def spawn(self):
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
                self.pipes[parent] = pid
                self.runners[pid] = {
                    'taskcount': 0,
                    'pipe': parent,
                    'pid': pid,
                    'state': 'STARTING',
                    'current_task': None
                }
            self.events.register(parent, EVREAD, self.child_event)

    def close(self, fd):
        self.events.remove(fd)
        os.close(fd)

    def child_event(self, fd, events):
        """
        called when a child writes to stdout or exits

        :param fd: int
        :param events: int
        :return: None
        """
        pid = self.pipes[fd]
        child = self.runners[pid]

        debug("spawner: callback(pid=%d,events=%d,fd=%d)" % (pid, events, fd))
        if events & EVREAD:
            debug("spawner: EVREAD")
            # TODO: reading from fh=fdopen(self.fd) was causing too much of a buffering, check WHY
            buf = os.read(fd, 32768)
            print("CHILD-%d: %s" % (pid, buf))
            self.runners[pid]['taskcount'] += 1
            if self.runners[pid]['taskcount'] == 3:
                self.runners[pid]['state'] = 'RESTARTING'
                os.kill(pid, SIGTERM)
        more = events & (~EVREAD)
        if more:
            debug("CHILD %d died" % pid)
            self.close(fd)
            try:
                (epid, status) = os.waitpid(pid, 0)
            except OSError as ose:
                raise ose
                # debug(ose)
                # pass
            else:
                sig = status & 0x0f
                rc = (status >> 8) & 0x0f
                debug("pid=%d, status=%d, sig=%d, rc=%d" % (epid, status, sig, rc))
                self.pipes.pop(fd, None)
                self.runners.pop(pid, None)

            if child['state'] == 'RESTARTING':
                self.spawn()

    def enslave(self, path, wid, eventmask, cookie, fname):
        pass

    def free(self, path, wid, eventmask, cookie, fname):
        pass

    def assign(self, path, wid, eventmask, cookie, fname):
        """
        when a task is registered into masterqueue, this callback is called from FSNotifier with the task filename
        the task will be registered with the best available slave
        :param path: str
        :param wid: int
        :param eventmask: int
        :param cookie: int
        :param fname: str
        :return: None
        """
        pass

