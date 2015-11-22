# coding=utf-8
"""
events.py
"""

import functools

from select import EPOLLIN, EPOLLOUT, EPOLLHUP, EPOLLERR, EPOLLONESHOT, \
    EPOLLET, \
    EPOLLRDNORM,  EPOLLWRNORM, EPOLLPRI, epoll
from .logger import debug

__author__ = 'system fault <sysfault@yahoo.com>'

EPOLLRDHUP = 1 << 13
EPOLLWRBAND = 1 << 9
EPOLLRDBAND = 1 << 7


EVREAD = EPOLLIN
EVONESHOT = EPOLLONESHOT
EVWRITE = EPOLLOUT
EVHUP = EPOLLHUP
EVERR = EPOLLERR | EVHUP | EPOLLRDHUP


class EventService(object):
    """
    EventService class
    """
    @classmethod
    def instance(cls):
        """
        :return: EventService
        """
        if not hasattr(cls, '_instance'):
            setattr(cls, '_instance', cls())
            debug("new eventservice instance created at %r" % getattr(cls, '_instance'))
        return getattr(cls, '_instance')
        # return cls._instance

    def __init__(self):
        self.epoll = epoll()
        self.fds = dict()

    def register_once(self, fd, events, callback):
        return self.once_(fd, events, callback, self.register)

    def update_once(self, fd, events, callback):
        return self.once_(fd, events, callback, self.update)

    def once_(self, fd, events, callback, op):
        def once_cb(fd_, firedevents_):
            self.fds.pop(fd_, None)
            callback(fd_, firedevents_)
            self.fds.pop(fd_, None)[1](fd_, firedevents_)
        op(fd, events | EVONESHOT, once_cb)

    def once(self, fd, events, callback):
        try:
            self.once_(fd, events, callback, self.register)
        except KeyError:
            self.once_(fd, events, callback, self.update)

    def register(self, fd, events, callback):
        if fd in self.fds:
            raise KeyError
        self.epoll.register(fd, events)
        self.fds[fd] = [events, callback]
        debug("listening for events %d on fd %d" % (fd, events))

    def update(self, fd, events=None, callback=None):
        if fd not in self.fds:
            raise KeyError
        if events is not None and self.fds[fd][0] != events:
            self.epoll.modify(fd, events)
            self.fds[fd][0] = events
        if callback is not None:
            self.fds[fd][1] = callback

    def remove(self, fd):
        self.epoll.unregister(fd)
        self.fds.pop(fd, None)

    def listen(self):
        debug("listening for events")
        while True:
            for(fd, events) in self.epoll.poll(-1, -1):
                debug("eventmask %d received on fd %d" % (events, fd))
                self.fds[fd][1](fd, events)

    def fileno(self):
        return self.epoll.fileno()

    def file(self):
        return self.epoll

    def close(self):
        return self.epoll.close()


class EventObject(object):
    """
    use events.make_eventobject(baseclass) to create an EventObject subclass
    """
    def __init__(self, eventmask=0):
        self.events_ = eventmask
        EventService.instance().register(self.fileno(), self.events_, self.callback)

    @property
    def events(self):
        return self.events_

    @events.setter
    def events(self, events_):
        # EventService.instance().update(self)
        oldmask = self.events_
        self.events_ = events_
        try:
            EventService.instance().update(self.fileno(), self.events_)
        except KeyError:
            self.events_ = oldmask
            raise

    def callback(self, fd, events):
        raise NotImplementedError

    def destroy(self):
        EventService.instance().remove(self.fileno())
        self.events = 0
        self.close()

    def close(self):
        raise NotImplementedError

    def fileno(self):
        raise NotImplementedError



