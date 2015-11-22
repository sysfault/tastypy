# -*- fileencoding: utf-8 -*-
import os

from tastypy.core.logger import debug


class Plugin(object):
    def setup(self, *args, **kwargs):
        pass

    def initialize(self, *args, **kwargs):
        pass

    def destroy(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        raise NotImplementedError


class PluginManager(object):
    def __init__(self, plugin_dir, watchfolder=False):
        if not os.path.exists(plugin_dir) or not os.path.isdir(plugin_dir):
            raise RuntimeError("can't read plugin_dir %s" % plugin_dir)
        self.plugin_dir = plugin_dir
        self.scandir(self.plugin_dir)
        debug("initializing plugins from folder %s" % plugin_dir)
        if watchfolder:
            self.watch_plugins()

    def scandir(self, target):
        for (path, dirs, files) in os.walk(target):
            for mod in filter(lambda x: x.endswith('py'), files):
                self.scanfile(mod)
            for subdir in map(lambda x: os.path.join(path, x), dirs):
                self.scandir(subdir)

    def scanfile(self, mod):
        pass

    def watch_plugins(self):
        pass


