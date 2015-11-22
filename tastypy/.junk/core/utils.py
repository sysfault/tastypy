# vim : set fileencoding=utf-8 :
# -*- coding:utf-8 -*-

import sys
import os

from tastypy.core.logger import debug


def find_classes_by_interface(implementing, classpath=None):
    pass


def tastypy_program_name():
    return os.path.basename(os.path.dirname(sys.argv[0]))


def load_program_configuration(envname=None):
    """
    :param envname: str
    :return: object
    envname can contain configuration's module name or path to the configuration name
    if envname is not specified, a default TASTYPY_<PROGRAM_NAME>_CF env var is queried
    if no env is found then program name is used as the name of configuration file
    """
    # TODO: isolate configuration loading in its own namespace for security reason (clean namespace pollution)
    #
    if envname is None:
        envname = '_'.join(['TASTYPY', tastypy_program_name().upper(), 'CF'])
    debug("envname=%s" % envname)
    cfname = os.getenv(envname, tastypy_program_name().lower())
    debug("configmodule=%s" % cfname)
    if os.path.exists(cfname):
        if os.path.isdir(cfname):
            sys.path.append(cfname)
            cfname = sys.argv[0].lower()
        elif os.path.isfile(cfname):
            sys.path.append(os.path.dirname(cfname))
            (cfname, ext) = os.path.basename(cfname).split('.')
            if not ext.startswith('py'):
                raise RuntimeError("config seems to be a filepath but does not end with .py*")
        else:
            raise RuntimeError("config is a path but not a folder or regular file")
    cf = None
    try:
        cf = __import__(cfname)
    except ImportError:
        raise RuntimeError("error importing configuration file")
    debug("configuration loaded at %r" % cf)
    return cf


def load_cf_param(cf, pname, check=lambda v: True, ignore_missing=False):
    pval = getattr(cf, pname, None)
    if pval is None and not ignore_missing:
        raise RuntimeError("missing configuration parameter (cf=%s, param=%s)" % (cf, pname))
    if not check(pval):
        raise RuntimeError("bad configuration value for (cf=%s, param=%s)" % (cf, pname))
    return pval

