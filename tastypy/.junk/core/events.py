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


class EventObject(object):
    """
    use events.make_eventobject(baseclass) to create an EventObject subclass
    """
    def __init__(self, eventmask=0):
        self.events_ = eventmask
        EventService.instance().register(self)

    @property
    def events(self):
        return self.events_

    @events.setter
    def events(self, events_):
        EventService.instance().update(self)
        self.events_ = events_

    def callback(self, events):
        raise NotImplementedError

    def destroy(self):
        eventservice.remove(self)
        self.events = 0
        self.close()

    def close(self):
        raise NotImplementedError

    def fileno(self):
        raise NotImplementedError


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
        self.eventmap = dict()

    def once(self, eventobject):
        def once_cb(firedevents):
            self.eventmap.pop(eventobject, None)
            return eventobject.event_callback(firedevents)
        self.eventmap[eventobject.fileno()] = once_cb
        self.register(eventobject)

    def register(self, eventobject):
        if eventobject.fileno() in self.eventmap:
            raise KeyError
        self.epoll.register(eventobject.fileno(), eventobject.events)
        self.eventmap[eventobject.fileno()] = eventobject
        debug("eventobject %r registered on fileno %d, eventmask=%d" % (eventobject, eventobject.fileno(),
                                                                        eventobject.events))
        # if eventobject.events & EPOLLONESHOT:
        #    self.eventmap[eventobject.fileno()] = functools.partial(self.once, eventobject)

    def update(self, eventobject):
        if eventobject.fileno() not in self.eventmap:
            raise KeyError
        self.epoll.modify(eventobject.fileno(), eventobject.events)

    def remove(self, eventobject):
        self.epoll.unregister(eventobject.fileno())
        return self.eventmap.pop(eventobject.fileno(), None)

    def listen(self):
        debug("listening for events")
        while True:
            for(fd, events) in self.epoll.poll(-1, -1):
                debug("eventmask %d received on fd %d" % (events, fd))
                self.eventmap[fd].callback(events)

    def fileno(self):
        return self.epoll.fileno()

    def file(self):
        return self.epoll

    def close(self):
        return self.epoll.close()

# eventservice = EventService.instance()


