# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-

from tastypy.core.fsnote import FSNotifier, IN_CREATE
from tastypy.programs.taskmaster import config
import os


def load_plugins():
    print("loading plugins from %s" % os.path.join(__file__, 'plugins'))


def process_task():
    pass


taskwatch = FSNotifier()
pid = os.getpid()
taskqueue = os.path.join(config.runqueues, "%d" % pid)
taskwatch.watch(taskqueue, IN_CREATE, process_task, makepath='d')
load_plugins()

