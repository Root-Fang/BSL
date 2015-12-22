# -*- coding: utf-8 -*-
import logging, os, inspect, json
LOGGING = None
def setup(path):
    global LOGGING
    with open(path) as fp:
        LOGGING = json.load(fp)

def dec(fn):
    if 'LOGGER' not in fn.__dict__:
        fn.__dict__["LOGGER"] = dict()
    def wrapped(*args, **kwargs):
        if "logname" in kwargs and kwargs["logname"] in fn.__dict__["LOGGER"]:
            return fn.__dict__["LOGGER"][kwargs["logname"]]
        elif len(args)>0 and args[0] is not None and args[0] in fn.__dict__["LOGGER"]:
            return fn.__dict__["LOGGER"][args[0]]
        else:
            name = kwargs["logname"] if "logname" in kwargs else args[0]
            fn.__dict__["LOGGER"][name] = fn(*args, **kwargs)
            return fn.__dict__["LOGGER"][name]
    return wrapped

@dec
def getLogger(logname="indoor"):
    if logname not in LOGGING['loggers']:
        raise LookupError(logname + " is not exist")
    logger = logging.getLogger(logname)
    for handler in LOGGING['loggers'][logname]['handlers']:
        if handler not in LOGGING['handlers']:
            continue
        category = LOGGING['handlers'][handler]['class']
        fm = LOGGING['handlers'][handler]['formatter']
        level = getattr(logging, LOGGING['handlers'][handler]['level'], logging.INFO)
        module = __import__(str(category).rsplit(".", 1)[0], fromlist=[str(category).rsplit(".", 1)[-1],])
        cls = getattr(module, category.rsplit(".", 1)[-1])
        if cls is None:
            raise LookupError("Module is not exist")

        args = dict()
        for arg in inspect.getargspec(cls.__dict__["__init__"]).args:
            if arg in LOGGING['handlers'][handler]:
                args[arg] = LOGGING['handlers'][handler][arg]
        if handler == "files":
            args['filename'] = os.path.join(args['filename'].rsplit("/", 1)[0], "_".join(logname.split("."))+".log")
        instance = cls(**args)
        instance.setFormatter(logging.Formatter(LOGGING['formatters'][fm]['format']))
        instance.setLevel(level)
        logger.addHandler(instance)
    logger.setLevel(getattr(logging, LOGGING['loggers'][logname]['level'], logging.INFO))
    logger.propagate = LOGGING['loggers'][logname]['propagate']
    return logger



if __name__ == "__main__":
    logger = getLogger(logname="indoor.sdk.server")
    logger.info("Just for test")

