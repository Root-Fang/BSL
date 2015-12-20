#-*- encoding: utf8 -*-
import ConfigParser

class Config(object):
    def __init__(self, path):
        self.path = path
        self.groups = dict({'a':'b'})
    def _reload(self):
        pass
    def register_list(self, group, key, default=None):
        pass
    def register_dict(self, group, key, default=None):
        pass
    def register_int(self, group, key, default=None):
        pass
    def register_float(self, group, key, default=None):
        pass
    def register_group(self, group):
        pass
    def register(self, group, key, default=None):
        pass
    def __getitem__(self, group):
        pass
    def __delitem__(self, group):
        pass
    def __setitem__(self, group, value):
        pass
    def __iter__(self):
        return self.groups.__iter__()
    def get(self, group, key, default=None):
        pass


CONF = Config('abc')


