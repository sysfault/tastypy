import os
import ctypes
import struct
from .loader import libc
from .logger import debug
from .events import EventObject

__author__ = 'system fault <sysfault@yahoo.com>'


CLOCK_MONOTONIC = 1
CLOCK_REALTIME = 0


class TimeSpec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_uint32),
        ('tv_nsec', ctypes.c_long)
    ]


class ITimerSpec(ctypes.Structure):
    _fields_ = [
        ('it_interval', TimeSpec),
        ('it_value', TimeSpec)
    ]


exptime_unpack_fmt = 'Q'
exptime_sz = ctypes.sizeof(ctypes.c_uint64)
if exptime_sz == 4:
    exptime_unpack_fmt = 'L'


class Timer(object):
    def __init__(self, clocktype=CLOCK_MONOTONIC, flags=0):
        self.timerfd = libc.timerfd_create(clocktype, flags)
        if self.timerfd == -1:
            raise os.error
        self.once_ = False
        self.spec = None
        self.callback = lambda t, e: False

    def fileno(self):
        return self.timerfd

    def close(self):
        os.close(self.timerfd)

    def set(self, intsec, intnsec=0, startsec=-1, startnsec=-1):
        if startsec == -1:
            startsec = intsec
        if startnsec == -1:
            startnsec = intnsec
        self.spec = ITimerSpec()
        self.spec.it_interval = TimeSpec()
        self.spec.it_interval.tv_sec = intsec
        self.spec.it_interval.tv_nsec = intnsec
        self.spec.it_value = TimeSpec()
        self.spec.it_value.tv_sec = startsec
        self.spec.it_value.tv_nsec = startnsec
        return self

    def once(self):
        self.once_ = True
        return self

    def start(self, callback, flags=0):
        rc = libc.timerfd_settime(
            self.timerfd,
            flags,
            ctypes.pointer(self.spec),
            ctypes.POINTER(ITimerSpec)()
        )
        if rc == -1:
            raise os.error

        return self

    def __eq__(self, other):
        return self.timerfd == other.timerfd

    def __call__(self, t, e):
        exptime = struct.unpack(exptime_unpack_fmt, os.read(self.timerfd, exptime_sz))[0]
        debug("runcallback(expiration_count=%d)" % (exptime,))
        self.callback(exptime)

    def __repr__(self):
        return "Timer(@%s, cb=%r)" % (hex(id(self)), self.callback)

    def get(self):
        pass

    def disable(self):
        pass

    def remove(self):
        pass


class TimerEvent(Timer, EventObject):
    def event_callback(self, events):
        raise NotImplementedError
