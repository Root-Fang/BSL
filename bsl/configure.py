#-*- encoding: utf8 -*-
import ConfigParser
class Opt(object):
    """Opt is a Abstract Base Class which is used to wrap the options in configuration file.

    """
    def __init__(self, key, group='default', default=None):
        self.group = group
        self.key = key
        self.default = default
    def parse(self, value):
        """ The method is a abstract method which should be overrided in derived class.

        :param value: The value load from configration file.
        :return: The value after being parsed.
        """
        raise NotImplementedError("Please implement the Class")


class BoolOpt(Opt):
    """ The class is used to parse value to Boolean.

    """
    def __init__(self, key, group='default', default=False):
        super(BoolOpt, self).__init__(key, group, default)
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
    """ The class is used to parse value to String.

    """
    def __init__(self, key, group='default', default=''):
        super(StrOpt, self).__init__(key, group, default)
    def parse(self, value):
        if value is None:
            return ''
        try:
            return str(value)
        except Exception as e:
            return str(self.default)

class IntOpt(Opt):
    """ The class is used to parse value to Int.

    """
    def __init__(self, key, group='default', default=0):
        super(IntOpt, self).__init__(key, group, default)
    def parse(self, value):
        try:
            return int(value)
        except Exception as e:
            return int(self.default)

class FloatOpt(Opt):
    """ The class is used to parse value to Float.

    """
    def __init__(self, key, group='default', default=0):
        super(FloatOpt, self).__init__(key, group, default)
    def parse(self, value):
        try:
            return float(value)
        except Exception as e:
            return float(self.default)

class ListOpt(Opt):
    """ The class is used to parse value to Python List.

    """
    def __init__(self, key, group='default', default=[], sep=','):
        super(ListOpt, self).__init__(key, group, default)
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
    """ The class is used to parse value to Python Dict.

    """
    def __init__(self, key, group='default', default={}, sep=','):
        super(DictOpt, self).__init__(key, group, default)
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
    """ The class used to parse the configuration file which is based on python standard module ConfigParser.

        The class is not only to load the configuration file, but also support to override the value in
        configuration file and parse the value to some known type such as dict, list  via register_opts/
        register_opt. The unregister_opt is used to eliminate the options(registered by register_opts/
        register_opt) in the cache.
    """
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
    def _reload_group(self, group):
        self.__cache[group] = dict()
        ops = self.fp.options(group)
        for op in ops:
            self.__cache[group][op] = self.fp.get(group, op)
    def __getitem__(self, group='default'):
        if self.fp.has_section(group):
            if group not in self.__cache:
                self._reload_group(group)
            return self.__cache[group]
        else:
            return None
    def __iter__(self):
        return self.__cache.__iter__()
    def __len__(self):
        return len(self.__cache)
    def __getattr__(self, group='default'):
        return self.__getitem__(group)
    def register_opts(self, opts):
        """The method is used to register the options.

        :param opts: opts must be a list or tuple and its elements must be derived class of Opt
        :return:
        """
        for opt in opts:
            self.register_opt(opt)
    def register_opt(self, opt):
        if not isinstance(opt, Opt):
            raise TypeError("Options type ERROR")
        if opt.group not in self.__cache:
            if self.fp.has_section(opt.group):
                self._reload_group(opt.group)
            else:
                return
        if not self.fp.has_option(opt.group, opt.key):
            self.__cache[opt.group][opt.key] = opt.parse(opt.default)
        else:
            self.__cache[opt.group][opt.key] = opt.parse(self.fp.get(opt.group, opt.key))
    def unregister_opt(self, key, group='default'):
        """ The method is used to unregister the options

        :param key: key in section of configuration file
        :param group: section in configuration file, default is 'default'
        :return: True: execute successfully; False: execute failure
        """
        if group not in self.__cache:
            return True
        if key not in self.__cache[group]:
            return True
        try:
            del self.__cache[group][key]
            if not self.__cache[group]:
                del self.__cache[group]
        except Exception as e:
            return False
        return True
    def get(self, key, group='default', default=None):
        """ The method is used to get the corresponding value of the key.

        :param key: key in section of configuration file
        :param group: section in configuration file, default is 'default'
        :param default: default value corresponding to the key given by client
        :return: the corresponding value of the key.
        """
        if group not in self.__cache:
            self._reload_group(group)
        try:
            return self.__cache[group][key]
        except KeyError as e:
            if self.fp.has_option(group, key):
                self.__cache[group][key] = self.fp.get(group, key)
            else:
                self.__cache[group][key] = default
        return self.__cache[group][key]


CONF = ConfigOpts()

if __name__ == "__main__":
    path = "../etc/bsl.conf"
    CONF.setup(path)
    opts = [BoolOpt('bool', 'default'),
            IntOpt('abc', 'default'),
            FloatOpt('zip', 'default'),
            ListOpt('s', 'skp'),
            DictOpt('d', 'skp'),
            ListOpt('unknown', 'skp', default=['a','b','c'])]
    CONF.register_opts(opts)
    print type(CONF['default']['bool']), CONF['default']['bool']
    print type(CONF['default']['abc']), CONF['default']['abc']
    print type(CONF['default']['zip']), CONF['default']['zip']
    print type(CONF['skp']['s']), CONF['skp']['s']
    print type(CONF['skp']['d']), CONF['skp']['d']
    print type(CONF['skp']['unknown']), CONF['skp']['unknown']
    CONF.unregister_opt('unknown', 'skp')
    print CONF.get('unknown', 'skp')




