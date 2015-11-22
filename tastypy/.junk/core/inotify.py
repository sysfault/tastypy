# vim: set fileencoding=utf-8 :

from fcntl import ioctl
import errno
import os
import struct
# from termios import FIONREAD
from .events import EventObject, EVREAD, EventService
from .logger import debug
from .loader import libc
import ctypes

__author__ = 'system fault <sysfault@yahoo.com>'

IN_ACCESS = 0x00000001
IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_CLOSE_NOWRITE = 0x00000010
IN_CLOSE = (IN_CLOSE_WRITE | IN_CLOSE_NOWRITE)
IN_OPEN = 0x00000020
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_MOVE = (IN_MOVED_FROM | IN_MOVED_TO)
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_DELETE_SELF = 0x00000400
IN_MOVE_SELF = 0x00000800
IN_UNMOUNT = 0x00002000
IN_Q_OVERFLOW = 0x00004000
IN_IGNORED = 0x00008000
IN_ONLYDIR = 0x01000000
IN_DONT_FOLLOW = 0x02000000
IN_EXCL_UNLINK = 0x04000000
IN_MASK_ADD = 0x20000000
IN_ISDIR = 0x40000000
IN_ONESHOT = 0x80000000
IN_ALL_EVENTS = (
    IN_ACCESS | IN_MODIFY | IN_ATTRIB | IN_CLOSE_WRITE |
    IN_CLOSE_NOWRITE | IN_OPEN | IN_MOVED_FROM |
    IN_DELETE_SELF | IN_MOVE_SELF)

IN_CLOEXEC = 0x80000
IN_NONBLOCK = 0x800
IN_FLAGS = IN_CLOEXEC | IN_NONBLOCK
# IN_FLAGS = 0


class INotifyWatch(object):

    @property
    def wd(self):
        return self.wd_

    @wd.setter
    def wd(self, val):
        if self.wd_ != -1:
            raise RuntimeError("wd already set!")
        self.wd_ = val

    @property
    def events(self):
        return self.events_

    @events.setter
    def events(self, eventmask):
        self.events_ = eventmask

    @property
    def pathname(self):
        return self.pathname_

    @pathname.setter
    def pathname(self, value):
        raise RuntimeError("inotifywatcher pathname is readonly")

    def __init__(self, pathname, eventmask=0):
        self.pathname_ = pathname
        self.events_ = eventmask
        self.wd_ = -1

    def callback(self, wd, mask, cookie, fname):
        raise NotImplementedError


class INotifyFD(EventObject):
    flags = 0
    buflen = ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_uint32) * 3

    def __init__(self):
        self.inotifyfd = libc.inotify_init1(IN_FLAGS)
        if self.inotifyfd == -1:
            raise OSError
        self.fh = os.fdopen(self.inotifyfd)
        debug("inotifyfd=%d" % self.inotifyfd)
        self.watchers = dict()
        self.buf = bytearray(self.buflen)
        EventObject.__init__(self, EVREAD)

    def __iadd__(self, watch):
        # TODO: str to char * conversion below won't work in python 3.x
        wd = libc.inotify_add_watch(self.inotifyfd, ctypes.c_char_p(watch.pathname), watch.events)
        if wd == -1:
            raise OSError
        debug("watcher added on path %s for events 0x%08x (wd=%d)" % (watch.pathname, watch.events, wd))
        self.watchers[wd] = watch
        watch.wd = wd

    def __isub__(self, pathname):
        # removing the watch from inotify object will generate IN_IGNORE event
        # so postpone clean up of the internals when the event is handled
        rc = libc.inotify_rm_watch(self.inotifyfd, self.watchers[pathname][0])
        if rc == -1:
            raise OSError

    def close(self):
        # TODO: this probably doesn't work as it should
        self.fh.close()
        os.close(self.inotifyfd)
        # do fucking this instead:
        # libc.close(self.inotifyfd)

    def fileno(self):
        return self.inotifyfd

    def next(self):
        # maybe try to read bigger buffer at once?
        # q = ctypes.c_int(0)
        # libc.ioctl(self.inotifyfd, FIONREAD, ctypes.pointer(q))

        try:
            bytes_read = self.fh.readinto(self.buf)
        except IOError as ee:
            if ee.errno == errno.EAGAIN:
                raise StopIteration
            raise ee

        if bytes_read != 16:
            raise StopIteration
        
        (wd, mask, cookie, flen) = struct.unpack('iIII', self.buf)
        fname = None
        # man inotify: may include further null bytes ('\0') to align subsequent reads to a suitable address boundary
        if flen > 0:
            fname = struct.unpack("%ds" % flen, self.fh.read(flen))
            fname = fname[0].rstrip('\0')

        return wd, mask, cookie, fname

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def callback(self, events):
        debug("inotify callback event, reading inotify events")
        for (wd, mask, cookie, fname) in self:
            if mask & IN_IGNORED:
                self.watchers.pop(wd)
                # if watcher choses to ignore the event there's no reason in forwarding any other
                # reported events to it
                return
            self.watchers[wd].callback(wd, mask, cookie, fname)


if __name__ == '__main__':

    class TMPWatcher(INotifyWatch):
        def callback(self, wd, mask, cookie, fname):
            print("event=0x%08X, cookie=%d, wd=%d, fname=%s" % (mask, cookie, wd, fname))

    inofd = INotifyFD()
    x = TMPWatcher('/tmp', IN_ALL_EVENTS)
    inofd += x
    EventService.instance().listen()
