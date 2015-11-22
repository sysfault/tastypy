import ctypes
from loadlib import libc

class INotifyFD(object):
    flags = 0
    buflen = ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_uint32) * 3

    def __init__(self):
        self.fd = libc.inotify_init1(IN_FLAGS)
        if self.fd == -1:
            raise OSError
        self.fh = os.fdopen(self.fd)
        debug("inotifyfd=%d" % self.inotifyfd)
        self.watchers = dict()
        self.buf = bytearray(self.buflen)

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

