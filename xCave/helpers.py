"""
    Helper functions for xCave.
"""
import sys

def parse_config(config):
    conf = {}
    for section in config.sections():
        conf[section] = {}
        for name, raw_value in config.items(section):
            try:
                # Ugly fix to avoid '0' and '1' to be parsed as a boolean value.
                # We raise an exception to goto fail^w parse it as integer.
                if config.get(section, name) in ["0", "1"]:
                    raise ValueError
                value = config.getboolean(section, name)
            except ValueError:
                try:
                    value = config.getint(section, name)
                except ValueError:
                    value = config.get(section, name)
            conf[section][name] = value
    return conf

def curate_tuples(d, type="int"):
    dd = {}
    for i in d:
        dd[i] = str2tuple(d[i], type)
    return dd

def str2tuple(d, type="int"):
    dd = None
    st = d.strip().strip(")").strip("(").split(",")
    if type == "int":
        dd = (int(st[0]), int(st[1]))
    elif type == "float":
        dd = (float(st[0]), float(st[1]))
    return dd
