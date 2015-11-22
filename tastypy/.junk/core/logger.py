# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
"""
logger module
"""
import time
import logging as logging_
import inspect
import os

if os.getenv('TASTYPYDEBUG', None) is None:
    logging_.basicConfig(level=logging_.WARN)
else:
    logging_.basicConfig(level=logging_.DEBUG)

logging = logging_
debug_ = logging_.debug


class TimingService:
    @staticmethod
    def instance():
        if not hasattr(TimingService, '_instance'):
            setattr(TimingService, '_instance', TimingService())
        return getattr(TimingService, '_instance')

    def __init__(self):
        self.timings = dict()

    def start(self, target):
        self.timings[target] = time.time()

    def stop(self, target):
        return time.time() - self.timings.pop(target)


def callerinfo():
    callerframe = inspect.currentframe().f_back.f_back
    _self = callerframe.f_locals.get('self', None)
    frameinfo = inspect.getframeinfo(callerframe)
    # pyfile = os.path.split(frameinfo[0])[-1]
    pyfile = frameinfo[0]
    # (object, function, filename, lineno)
    return _self, frameinfo[2], pyfile, frameinfo[1]


def debug(msg, *args, **kwargs):
    callerframe = inspect.currentframe().f_back
    if callerframe.f_locals.get('self', None) is not None:
        caller = "%r" % callerframe.f_locals['self']
    else:
        caller = ''
    #TODO: remove following line
    #caller = ''
    frameinfo = inspect.getframeinfo(callerframe)
    f = os.path.split(frameinfo[0])[-1]
    debug_(' '.join(["[%s.%s@%s:%d]" % (caller, frameinfo[2], f, frameinfo[1]), msg ]), *args, **kwargs)
    #debug_("[%s@%s:%d] %s" % (frameinfo[2], frameinfo[0], frameinfo[1], msg), args, kwargs)
