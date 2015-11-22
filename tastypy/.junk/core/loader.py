# vim: set fileencoding=utf-8 :
# -*- coding:utf-8 -*-
import ctypes
import os


def loadlib(libname, version=None):
    if version is not None:
        libn = "lib%s-linux-x86_64.so.%s" % (libname, version)
        shlibname = os.path.join(os.path.dirname(__file__), '.nativelibs', libn)
        print("loadfrom %s" % shlibname)
    else:
        import fnmatch
        targetdir = os.path.join(os.path.dirname(__file__), '.nativelibs')
        # debug("targetdir=%s" % targetdir)
        matches = fnmatch.filter(os.listdir(targetdir),
                                 "lib%s-linux-x86_64.so*" % libname)
        if len(matches) < 1:
            raise SystemError("library not found")
        shlibname = os.path.join(targetdir, matches[-1])
    try:
        shlib = ctypes.cdll.LoadLibrary(shlibname)
    except OSError:
        raise SystemError("can't load shared library %s" % shlib)
    return shlib


libc = ctypes.cdll.LoadLibrary('libc.so.6')
