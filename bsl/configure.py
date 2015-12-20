#-*- encoding: utf8 -*-
import ConfigParser

class Config(object):
    def __init__(self, path):
        self.path = path
        self.groups = dict()
        self.fp = None
        self._reload()
    def _reload(self):
        if self.fp:
            self.fp = None
        self.fp = ConfigParser.ConfigParser()
        self.fp.read(self.path)
    def _reload_group(self, group):
        self.groups[group] = dict()
        ops = self.fp.options(group)
        for op in ops:
            self.groups[group][op] = self.fp.get(group, op)
    def _parse_boolean(self, default):
        if isinstance(default, bool):
            return default
        elif isinstance(default, str):
            if default.upper() in ('NO', '0', 'FALSE', 'WRONG'):
                return  False
            else:
                return True
        elif isinstance(default, int):
            return True if default else False
        else:
            return False
    def register_list(self, group, key, split=',', default=None):
        pass
    def register_dict(self, group, key, split=',', default=None):
        pass
    def register_int(self, group, key, default=0):
        self.register_group(group)
        try:
            tmp = self.fp.get(group, key)
        except ConfigParser.NoOptionError as e:
            tmp = default
        try:
            self.groups[group][key] = int(tmp)
        except ValueError as e:
            self.groups[group][key] = int(default)
        return self.groups[group][key]
    def register_float(self, group, key, default=0):
        self.register_group(group)
        try:
            tmp = self.fp.get(group, key)
        except ConfigParser.NoOptionError as e:
            tmp = default
        try:
            self.groups[group][key] = float(tmp)
        except ValueError as e:
            self.groups[group][key] = float(default)
        return self.groups[group][key]
    def register_boolean(self, group, key, default=False):
        self.register_group(group)
        try:
            tmp = self.fp.get(group, key)
            self.groups[group][key] = self._parse_boolean(tmp)
        except ConfigParser.NoOptionError as e:
            self.groups[group][key] = self._parse_boolean(default)

    def register_group(self, group):
        if group not in self.groups:
            self._reload_group(group)
        return self.groups[group]

    def register(self, group, key, default=None):
        self.register_group(group)
        try:
            self.groups[group][key] = self.fp.get(group, key)
        except ConfigParser.NoOptionError as e:
            self.groups[group][key] = default

    def __getitem__(self, group):
        if self.fp.has_section(group):
            return self.register_group(group)
        else:
            return None
    def __iter__(self):
        return self.groups.__iter__()
    def get(self, group, key, default=None):
        if group not in self.groups:
            self._reload_group(group)
        try:
            self.groups[group][key] = self.fp.get(group, key)
        except ConfigParser.NoOptionError as e:
            self.groups[group][key] = default
        return self.groups[group][key]




CONF = Config('abc')


