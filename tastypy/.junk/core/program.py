# vim: set fileencoding=utf-8 :
# -*- coding:utf-8 -*-

import os
import sys

from tastypy.core.logger import callerinfo


# from tastypy.libs.core.utils import load_program_configuration


def program_name():
    return os.path.basename(os.path.dirname(sys.argv[0]))


class Config(object):
    def __init__(self):
        pass

    def load(self, envname=None):
        if envname is None:
            envname = '_'.join(['TASTYPY', program_name().upper(), 'CONFIG'])
        configfile = os.getenv(envname, "tastypy.program.%s.config" % program_name())
        if os.path.exists(configfile):
            if configfile.endswith('.py'):
                if not os.path.dirname(configfile) in sys.path:
                    sys.path.append(os.path.dirname(configfile))
                configmod = __import__(os.path.basename(configfile).split('.')[0])
                self.compile(configmod.configuration_program)
            else:
                # asume this is a raw configuration program
                with open(configfile, 'r') as cf:
                    self.compile(cf.read(-1))
        else:
            try:
                configmod = __import__(configfile)
            except ImportError:
                raise RuntimeError("can't import config %s, try adding path to $PYTHONPATH?")
            self.compile(configmod.configuration_program)

    def compile(self, cfprogram):
        pass

    def __getitem__(self, name):
        (obj, func, filename, line) = callerinfo()


class Program(object):
    def __init__(self):
        pass

    def config(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def run(self):
        pass
