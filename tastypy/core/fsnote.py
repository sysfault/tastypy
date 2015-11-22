import ctypes
import errno
import os
import shutil
import struct
from loadlib import libc
from logger import debug

buflen = ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_uint32) * 3

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


def inotify_init1(flags):
    fd__ = libc.inotify_init1(flags)
    if fd__ == -1:
        raise OSError("can't create inotify fd")
    return fd__


def inotify_add_watch(fd__, pathname, events):
    wd_ = libc.inotify_add_watch(fd__, ctypes.c_char_p(pathname), events)
    if wd_ == -1:
        raise OSError("can't add watch for path %s" % pathname)
    return wd_


def inotify_rm_watch(fd__, wd__):
    rc = libc.inotify_rm_watch(fd__, wd__)
    if rc == -1:
        raise OSError
    return rc


def inotify_read1(fd):
    buf = bytearray(buflen)
    with os.fdopen(fd) as fh:
        while True:
            try:
                bytes_read = fh.readinto(buf)
            except IOError as ee:
                if ee.errno == errno.EAGAIN:
                    raise StopIteration()
                else:
                    raise ee

            if bytes_read != 16:
                raise StopIteration()
            
            (wd, mask, cookie, flen) = struct.unpack('iIII', buf)
            fname = None
            # man inotify: may include further null bytes ('\0') to align subsequent reads to a suitable
            # address boundary
            if flen > 0:
                fname = struct.unpack("%ds" % flen, fh.read(flen))
                fname = fname[0].rstrip('\0')
            yield wd, mask, cookie, fname


class FSNotifier(object):
    def __init__(self, flags=IN_FLAGS):
        self.flags = flags
        self.fd = inotify_init1(flags)
        self.fh = os.fdopen(self.fd)
        self.targets = dict()
        self.paths = dict()
        self.buf = bytearray(buflen)

    def fileno(self):
        return self.fd

    def close(self):
        self.fh.close()
        os.close(self.fd)

    def _makepath(self, pathname, filetype):
        if os.path.exists(pathname):
            raise RuntimeError("path %s exists, won't remove" % pathname)
        if filetype == 'd':
            os.makedirs(pathname)
        elif filetype == 'f':
            os.makedirs(os.path.dirname(pathname))
            open(pathname, 'w').close()
        else:
            raise RuntimeError("makepath can be one of 'False', 'd' for directory of 'f' for a regular file")

    def cleanup_(self, pathname):
        target = self.targets.pop(self.paths.pop(pathname, None), None)
        cleanup = target['rmpath']
        if not cleanup:
            return
        if cleanup == 'f':
            os.unlink(pathname)
        elif cleanup == 'd':
            shutil.rmtree(pathname)
        else:
            raise RuntimeError("didn't thought about it")

    def callback_once_(self, callback):
        def cb(pathname, wid, eventmask, cookie, fname):
            rc = callback(pathname, wid, eventmask, cookie, fname)
            # may throw, fine!
            self.cleanup_(target)
            return rc
        return cb

    def once(self, pathname, eventmask, callback, makepath=False):
        eventmask |= IN_ONESHOT
        self.watch(pathname, eventmask, self.callback_once_(callback), makepath)

    def watch(self, pathname, eventmask, callback, makepath=False):
        if not callable(callback): raise RuntimeError
        # TODO: implement makepath flag
        if makepath:
            self._makepath(pathname, makepath)

        wd = inotify_add_watch(self.fd, pathname, eventmask)
        self.targets[wd] = {
            'pathname': pathname,
            'eventmask': eventmask,
            'callback': callback,
            'rmpath': makepath
        }
        self.paths[pathname] = wd

    def unwatch(self, pathname):
        inotify_rm_watch(self.fd, self.paths[pathname])
        self.cleanup_(pathname)

    forget = unwatch
    ignore = unwatch

    def __iter__(self):
        return self

    def __next__(self):
        try:
            bytes_read = self.fh.readinto(self.buf)
        except IOError as ee:
            if ee.errno == errno.EAGAIN:
                raise StopIteration()
            else:
                raise ee

        if bytes_read != 16:
            raise StopIteration()
        (wd, mask, cookie, flen) = struct.unpack('iIII', self.buf)
        fname = None
        # man inotify: may include further null bytes ('\0') to align subsequent reads to a suitable address boundary
        if flen > 0:
            fname = struct.unpack("%ds" % flen, self.fh.read(flen))
            fname = fname[0].rstrip('\0')
        return wd, mask, cookie, fname

    next = __next__

    def callback(self, events):
        return self.__call__(events)

    def __call__(self, events):
        for (wd, mask, cookie, fname) in self:
            target = self.targets.get(wd, None)
            if target is None:
                debug("missing target for wd=%d, fname=%s (see BUGS in inotify manpage)" % (wd, fname))
                continue
            target['callback'](target['pathname'], wd, mask, cookie, fname)


if '__main__' == __name__ and os.getenv('OOLOVE'):
    import sys
    notifier = FSNotifier()

    def note_cb(pathname, wd, mask, cookie, fname):
        print("path=%s, wd=%d, mask=%d, cookie=%d, fname=%s" % (pathname, wd, mask, cookie, fname))

    target = os.path.join('/tmp/q', "%d" % os.getpid())
    notifier.watch(target, IN_CREATE, note_cb, makepath='d')
    print(notifier.targets)
    print(notifier.paths)
    import select
    e = select.epoll()
    e.register(notifier.fileno(), select.EPOLLIN)
    for fn in 'a b c d e f g h'.split(' '):
        open(os.path.join(target, fn), 'w').close()
    for (fd, ev) in e.poll(-1, -1):
        if fd == notifier.fileno():
            notifier(ev)
    notifier.forget(target)
    print(notifier.targets)
    print(notifier.paths)

    print("TEST: NOTIFIER ONCE")
    notifier.once(target, IN_CREATE, note_cb, makepath='d')
    print(notifier.targets)
    print(notifier.paths)
    import select
    e = select.epoll()
    e.register(notifier.fileno(), select.EPOLLIN)
    for fn in 'a b c d e f g h'.split(' '):
        open(os.path.join(target, fn), 'w').close()
    for (fd, ev) in e.poll(-1, -1):
        if fd == notifier.fileno():
            notifier(ev)
    # notifier.forget(target)
    print(notifier.targets)
    print(notifier.paths)

    sys.exit(0)


if '__main__' == __name__:
    from shutil import rmtree
    import sys
    target = os.path.join('/tmp', "%d" % os.getpid())
    if os.path.exists(target):
        if os.path.isdir(target):
            rmtree(target)
        else:
            os.unlink(target)
    os.mkdir(target)
    fd = inotify_init1()
    wd = inotify_add_watch(fd, target, IN_CREATE)
    import select
    e = select.epoll()
    e.register(fd, select.EPOLLIN)
    for fn in 'a b c d e f g h'.split(' '):
        with open(os.path.join(target, fn), 'w'):
            pass

    events = e.poll(-1, -1)
    for (fd_, ev) in events:
        # debug("got events (%d, %d)" % (fd_, ev))
        if fd_ == fd:
            for (wd, mask, cookie, fname) in inotify_read1(fd):
                print("wd=%d, mask=%d, cookie=%d, fname=%s" % (wd, mask, cookie, fname))
    rmtree(target)

    sys.exit(0)

