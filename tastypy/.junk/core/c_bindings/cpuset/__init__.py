import os
from ._cpuset import sched_setcpumask, sched_getcpumask


class Scheduler(object):
    def __init__(self):
        self.nrcpus = os.sysconf(os.sysconf_names['SC_NPROCESSORS_ONLN'])

    def setcpu(self, pid, cpuid):
        pass

    def getcpu(self, pid):
        pass

    def assign(self, pids):
        pass
