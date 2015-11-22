import ctypes
import os
from select import epoll, EPOLLIN

from struct import unpack

epfd = epoll()

libc = ctypes.cdll.LoadLibrary('libc.so.6')
flags = 0x80000 | 0x800
inofd = libc.inotify_init1(0)
fh = os.fdopen(inofd)
if inofd == -1:
    raise SystemError
IN_CREATE = 0x00000100
wd = libc.inotify_add_watch(inofd, '/tmp', IN_CREATE)
eventmap = dict()
fsmap = dict()

def handle_tmp_write():
    pass

def handle_fs_event(fd, events):
    buf = fh.read(16)
    print("read %d bytes buffer=%s" % (len(buf), buf))
    
    (wd, event, cookie, flen) = unpack('iIII', buf)
    print("wd=%d, events=%s, cookie=%d, flen=%d" % (wd, event, cookie, flen))
    if flen > 0:
        fname = fh.read(flen)
        fname = fname.rstrip('\0')
        print("fname=%s" % fname)

eventmap[inofd] = handle_fs_event
fsmap[wd] = handle_tmp_write

epfd.register(inofd, EPOLLIN)
print(fh)
while True:
    print("waiting for events")
    for (fd, events) in epfd.poll(-1,-1):
        if fd == inofd && events == EPOLLIN:
            print("got watcher event")
            continue
        raise RuntimeError("unknown (fd=%d,event=%d)" % (fd, events))
    #bytes_read = libc.read(inofd, buf, 16)

