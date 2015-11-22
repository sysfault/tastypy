# vim: set fileencoding=utf-8 :
# -*- coding:utf-8 -*-

import os

from tastypy.core.inotify import INotifyWatch, IN_CREATE
from tastypy.core.logger import callerinfo, debug
from tastypy.core.plugin import PluginManager
from tastypy.core.utils import load_program_configuration, load_cf_param


class QueueListener(INotifyWatch):

    def callback(self, wd, mask, cookie, filename):
        debug("NEWTASK: %s" % filename)

    def __init__(self):
        cf = load_program_configuration()
        self.queuedir = load_cf_param(cf, 'queuedir', lambda f: os.path.isdir(f))
        INotifyWatch.__init__(self, self.queuedir, IN_CREATE)
        (obj, func, filename, line) = callerinfo()
        self.plugin_manager = PluginManager(os.path.join(os.path.abspath(os.path.dirname(filename)), 'queue_plugins'))
        debug("initialized")


class WorkerTaskListener(INotifyWatch):
    def callback(self, wd, mask, cookie, filename):
        pass

    def __init__(self):
        pass
