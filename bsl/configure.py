#-*- encoding: utf8 -*-
import ConfigParser, collections
class Opt(object):
    def __init__(self, group, key, default=None):
        self.group = group
        self.key = key
        self.default = default
    def parse(self, value):
        raise NotImplementedError("Please implement the Class")


class BoolOpt(Opt):
    def __init__(self, group, key, default=False):
        super(BoolOpt, self).__init__(group, key, default)
    def parse(self, value):
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            if value.upper() in ('NO', '0', 'FALSE', 'WRONG'):
                return  False
            else:
                return True
        elif isinstance(value, int):
            return True if value else False
        else:
            return False

class StrOpt(Opt):
    def __init__(self, group, key, default=''):
        super(StrOpt, self).__init__(group, key, default)
    def parse(self, value):
        if value is None:
            return ''
        try:
            return str(value)
        except Exception as e:
            return str(self.default)

class IntOpt(Opt):
    def __init__(self, group, key, default=0):
        super(IntOpt, self).__init__(group, key, default)
    def parse(self, value):
        try:
            return int(value)
        except Exception as e:
            return int(self.default)

class FloatOpt(Opt):
    def __init__(self, group, key, default=0):
        super(FloatOpt, self).__init__(group, key, default)
    def parse(self, value):
        try:
            return float(value)
        except Exception as e:
            return float(self.default)

class ListOpt(Opt):
    def __init__(self, group, key, default=[], sep=','):
        super(ListOpt, self).__init__(group, key, default)
        self.sep = sep
    def parse(self, value):
        if value is None:
            if self.default is not None:
                return self.parse(self.default)
            else:
                return list()
        if isinstance(value, list):
            return value
        elif isinstance(value, str):
            return value.split(self.sep)
        else:
            rc = list()
            rc.append(value)
            return rc

class DictOpt(Opt):
    def __init__(self, group, key, default={}, sep=','):
        super(DictOpt, self).__init__(group, key, default)
        self.sep = sep
    def parse(self, value):
        if value is None:
            if self.default is not None:
                return self.parse(self.default)
            else:
                return dict()
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            tmps = value.split(self.sep)
            rc = dict()
            for tmp in tmps:
                try:
                    key, value = tmp.split(":")
                except Exception as e:
                    key = tmp
                    value = None
                rc[key] = value
            return rc
        else:
            return dict()

class ConfigOpts(object):
    def __init__(self):
        self.__cache = dict()
    def setup(self, path):
        self.path = path
        self.fp = None
        self._reload()
    def _reload(self):
        if self.fp:
            self.fp = None
        self.fp = ConfigParser.ConfigParser()
        self.fp.read(self.path)
    def __getitem__(self, group='default'):
        if self.fp.has_section(group):
            return None
        else:
            return None
    def __iter__(self):
        return self.__cache.__iter__()
    def __len__(self):
        return len(self.__cache)
    def register_opts(self, opts):
        for opt in opts:
            self.register_opt(opt)
    def register_opt(self, opt):
        if not isinstance(opt, Opt):
            raise TypeError("Options type ERROR")
        if opt.group not in self.__cache:
            if self.fp.has_section(opt.group):
                self.__cache[opt.group] = dict()
            else:
                return
        if not self.fp.has_option(opt.group, opt.key):
            self.__cache[opt.group][opt.key] = opt.parse(opt.default)
        else:
            self.__cache[opt.group][opt.key] = opt.parse(self.fp.get(opt.group, opt.key))
    def get(self, key, group='default', default=None):
        if group not in self.__cache:
            self._reload_group(group)
        try:
            return self.__cache[group][key]
        except ConfigParser.NoOptionError as e:
            self.__cache[group][key] = default
        return self.__cache[group][key]


s = ConfigOpts()

# class Config(object):
#     def __init__(self, path):
#         self.path = path
#         self.groups = dict()
#         self.fp = None
#         self._reload()
#     def _reload(self):
#         if self.fp:
#             self.fp = None
#         self.fp = ConfigParser.ConfigParser()
#         self.fp.read(self.path)
#     def _reload_group(self, group):
#         self.groups[group] = dict()
#         ops = self.fp.options(group)
#         for op in ops:
#             self.groups[group][op] = self.fp.get(group, op)
#     def _parse_boolean(self, default):
#         if isinstance(default, bool):
#             return default
#         elif isinstance(default, str):
#             if default.upper() in ('NO', '0', 'FALSE', 'WRONG'):
#                 return  False
#             else:
#                 return True
#         elif isinstance(default, int):
#             return True if default else False
#         else:
#             return False
#     def register_list(self, group, key, split=',', default=None):
#         pass
#     def register_dict(self, group, key, split=',', default=None):
#         pass
#     def register_int(self, group, key, default=0):
#         self.register_group(group)
#         try:
#             tmp = self.fp.get(group, key)
#         except ConfigParser.NoOptionError as e:
#             tmp = default
#         try:
#             self.groups[group][key] = int(tmp)
#         except ValueError as e:
#             self.groups[group][key] = int(default)
#         return self.groups[group][key]
#     def register_float(self, group, key, default=0):
#         self.register_group(group)
#         try:
#             tmp = self.fp.get(group, key)
#         except ConfigParser.NoOptionError as e:
#             tmp = default
#         try:
#             self.groups[group][key] = float(tmp)
#         except ValueError as e:
#             self.groups[group][key] = float(default)
#         return self.groups[group][key]
#     def register_boolean(self, group, key, default=False):
#         self.register_group(group)
#         try:
#             tmp = self.fp.get(group, key)
#             self.groups[group][key] = self._parse_boolean(tmp)
#         except ConfigParser.NoOptionError as e:
#             self.groups[group][key] = self._parse_boolean(default)
#
#     def register_group(self, group):
#         if group not in self.groups:
#             self._reload_group(group)
#         return self.groups[group]
#
#     def register(self, group, key, default=None):
#         self.register_group(group)
#         try:
#             self.groups[group][key] = self.fp.get(group, key)
#         except ConfigParser.NoOptionError as e:
#             self.groups[group][key] = default
#
#     def __getitem__(self, group):
#         if self.fp.has_section(group):
#             return self.register_group(group)
#         else:
#             return None
#     def __iter__(self):
#         return self.groups.__iter__()
#     def get(self, group, key, default=None):
#         if group not in self.groups:
#             self._reload_group(group)
#         try:
#             self.groups[group][key] = self.fp.get(group, key)
#         except ConfigParser.NoOptionError as e:
#             self.groups[group][key] = default
#         return self.groups[group][key]



