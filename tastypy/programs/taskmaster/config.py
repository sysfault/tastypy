# vim: set fileencoding=utf-8 :
# -*- coding:utf-8 -*-
"""
tastypy objects configurations
"""
import os

nrcpus = os.sysconf(os.sysconf_names['SC_NPROCESSORS_ONLN'])
queuedir = '/var/www/sites/ponycloak.com/data/event_queue'
masterqueue = os.path.join(queuedir, 'master')
slavequeues = os.path.join(queuedir, 'slaves')
slaves_per_cpu = 1
slavecount = nrcpus * slaves_per_cpu

masterqueue = '/var/run/eventqueue/master'
runqueues = '/var/run/eventqueue/slave'
pendingqueue = '/var/run/eventqueue/master/pending'

max_tasks_pending_per_runner = 1
runnercount = 1
max_tasks_per_runner = 2


def slavequeue(proc):
    return os.path.join(slavequeues, "%d" % proc.pid)

configuration_program = """
tastypy.libs.core
    task_queue.QueueListener
        eventqueue = '/tmp/eventqueue'
    events.EventService
        epoll_timeout = -1
        max_events = -1
tastypy.libs.http
    HTTPService
        defaultport = 80
        ssl = True
"""


"""
class Configuration(object):
    def __init__(self):
        self.root_ = None

    @property
    def root(self):
        return self.root_

    @root.setter
    def root(self, val):
        pass

    def __setitem__(self, k, v):
        pass


config = Configuration()
config.root = '.tastypy.libs.core'
config.root = 'task_queue.QueueListener'
config['eventqueue'] = '/tmp/eventqueue'

config['tastypy.libs.core.task_queue.QueueListener.eventqueue'] = '/tmp/eventqueue'
"""
# configuration program
configuration_program = """
> tastypy.libs.core
> task_queue.QueueListener
eventqueue = /tmp/eventqueue
maxevents = 300
<
> loader.Loader
= nativepath, ${programroot}
"""