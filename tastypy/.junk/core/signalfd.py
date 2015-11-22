import ctypes
from ctypes import *
import io
from io import BlockingIOError
import os
from .loader import libc
from .logger import debug
# import signal

__author__ = 'system fault <sysfault@yahoo.com>'


SFD_NONBLOCK = 0x800
SFD_CLOEXEC = 0x80000
SIGSET_NWORDS = int(1024 / (8 * sizeof(c_ulong)))
SIGINFOLEN = 128
_NSIG = 64
SIGWORD_SIZE = sizeof(c_ulong)
SIG_BLOCK = 0
SIG_UNBLOCK = 1


class SigSet(Structure):
    _fields_ = [('val', c_ulong * SIGSET_NWORDS)]

    def __init__(self, *args):
        Structure.__init__(self)
        for sig in args:
            self.__iadd__(sig)

    def fill(self):
        for i in range(0, SIGSET_NWORDS):
            self.val[i] = 0xffffffffffffffff

    def empty(self):
        for i in range(0, SIGSET_NWORDS):
            self.val[i] = 0

    def __nonzero__(self):
        for i in range(0, SIGSET_NWORDS):
            if self.val[i] != 0:
                break
        else:
            return False
        return True

    def isempty(self):
        return not self.__nonzero__()

    def __iand__(self, sset):
        for i in range(0, SIGSET_NWORDS):
            self.val[i] &= sset.val[i]

    def __ior__(self, sset):
        for i in range(0, SIGSET_NWORDS):
            self.val[i] |= sset.val[i]

    def __contains__(self, signum):
        return self.sigismember(signum)

    @staticmethod
    def sigpos(signum):
        return SigSet.sigmask(signum), SigSet.sigword(signum)

    def sigismember(self, signum):
        mask, word = SigSet.sigpos(signum)
        if self.val[word] & mask != 0:
            return True
        return False

    def __iadd__(self, signum):
        mask, word = SigSet.sigpos(signum)
        self.val[word] |= mask
        return self

    def __isub__(self, signum):
        mask, word = SigSet.sigpos(signum)
        self.val[word] &= ~mask
        return self

    @staticmethod
    def sigmask(signum):
        """
        set signum in the word corresponding to it
        """
        return 0x0000000000000001 << ((signum - 1) % (8 * SIGWORD_SIZE))

    @staticmethod
    def sigword(signum):
        """
        returns the word index for signum
        """
        return int((signum - 1) / (8 * SIGWORD_SIZE))


def sigprocmask(how, sigset, oldset=0):
    return libc.sigprocmask(how, ctypes.pointer(sigset),
                            0 if oldset == 0 else ctypes.pointer(oldset))

# siginfo_packer = struct.Struct('IIIIIIIIIIIILLLL48s')


class SigInfo(Structure):
    _fields_ = [
        ('ssi_signo', c_uint32),
        ('ssi_errno', c_int32),
        ('ssi_code', c_int32),
        ('ssi_pid', c_uint32),
        ('ssi_uid', c_uint32),
        ('ssi_fd', c_int32),
        ('ssi_tid', c_uint32),
        ('ssi_band', c_uint32),
        ('ssi_overrun', c_uint32),
        ('ssi_trapno', c_uint32),
        ('ssi_status', c_int32),
        ('ssi_int', c_int32),
        ('ssi_ptr', c_uint64),
        ('ssi_utime', c_uint64),
        ('ssi_stime', c_uint64),
        ('ssi_addr', c_uint64),
        ('pad', c_int8 * 48)
    ]

    def __str__(self):
        return "signo=%d pid=%d uid=%d" % (self.ssi_signo, self.ssi_pid, self.ssi_uid)

signalfd_default_flags = SFD_CLOEXEC | SFD_NONBLOCK


class SignalFD:
    def __init__(self, *signals):
        """
        sigset: the SigSet() object containing the signals you want to listen for
        fd: the underlying signalfd file descriptor (should be kept default -1 when creating a new signalfd object)
        flags: SFD_CLOEXEC|SFD_NONBLOCK (these are set by default)
        """
        self.signalfd = -1
        self.sigset = SigSet(*signals)
        self.flags = signalfd_default_flags
        debug("INIT: signals=%r" % (signals,))
        self.__update__()
        # noinspection PyTypeChecker
        self.sifh = io.FileIO(self.signalfd, closefd=False)

    def __iadd__(self, signum):
        self.sigset += signum
        self.__update__()
        return self

    def __isub__(self, signum):
        self.sigset -= signum
        self.__update__()
        sigprocmask(SIG_UNBLOCK, SigSet(signum))
        return self

    def __update__(self):
        """
        internal method, don't use it from outside
        """
        self.signalfd = libc.signalfd(self.signalfd, ctypes.pointer(self.sigset), self.flags)
        if self.signalfd == -1:
            raise SystemError("can't update signalfd")
        sigprocmask(SIG_BLOCK, self.sigset)

    def fileno(self):
        return self.signalfd

    def close(self):
        self.sifh.close()
        return os.close(self.signalfd)

    def __iter__(self):
        return self

    def read(self):
        try:
            si = SigInfo()
            numbytes = self.sifh.readinto(si)
            if numbytes is None:
                return None
            if numbytes < SIGINFOLEN:
                raise SystemError("error reading signal descriptor")
        except BlockingIOError:
            return None
        return si

    def __next__(self):
        si = self.read()
        if si is None:
            raise StopIteration
        return si

    def __contains__(self, signum):
        return self.sigset.__contains__(signum)

    def next(self):
        return self.__next__()
