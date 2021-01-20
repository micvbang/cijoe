"""
    Collection of Python utilities for CIJOE and CIJOE testing
"""
from __future__ import print_function
import time
import sys
import os

VERSION_MAJOR = 0
VERSION_MINOR = 0
VERSION_PATCH = 38
VERSION = "%d.%d.%d" % (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

PR_EMPH_CC = "\033[0;36m"
PR_GOOD_CC = "\033[0;32m"
PR_WARN_CC = "\033[0;33m"
PR_ERR_CC = "\033[0;31m"
PR_NC = "\033[0m"

ENV = os.environ
CIJ_ECHO_TIME_STAMP = ENV.get("CIJ_ECHO_TIME_STAMP")

EXTS = {
    "TPLANS": [".plan"],
    "TSUITES": [".suite"],
    "TCASES": [".py", ".sh"],
    "HOOKS": [".py", ".sh"],
}


def index(search_path, ext=None):
    """@returns a set of filenames with extension 'ext' in 'search_path'"""

    if ext is None:
        ext = "TCASES"

    fnames = set([])
    for _, _, files in os.walk(search_path):
        for fname in files:
            if os.path.splitext(fname)[-1] in EXTS[ext]:
                fnames.add(fname)

    return fnames


def get_time_stamp():
    """Get time stampe if CIJ_ECHO_TIME_STAMP is 1"""

    if CIJ_ECHO_TIME_STAMP == "1":
        return time.strftime('[%Y-%m-%d %H:%M:%S] ', time.localtime(time.time()))

    return ""


def _flush(fd):
    if callable(getattr(fd, 'flush', None)):
        fd.flush()


def info(txt, fd=sys.stdout):
    """Print, emphasized 'neutral', the given 'txt' message"""

    print("%s# %s%s%s" % (PR_EMPH_CC, get_time_stamp(), txt, PR_NC))
    _flush(fd)


def good(txt, fd=sys.stdout):
    """Print, emphasized 'good', the given 'txt' message"""

    print("%s# %s%s%s" % (PR_GOOD_CC, get_time_stamp(), txt, PR_NC), file=fd)
    _flush(fd)


def warn(txt, fd=sys.stdout):
    """Print, emphasized 'warning', the given 'txt' message"""

    print("%s# %s%s%s" % (PR_WARN_CC, get_time_stamp(), txt, PR_NC), file=fd)
    _flush(fd)


def err(txt, fd=sys.stdout):
    """Print, emphasized 'error', the given 'txt' message"""

    print("%s# %s%s%s" % (PR_ERR_CC, get_time_stamp(), txt, PR_NC), file=fd)
    _flush(fd)


def emph(txt, rval=None, fd=sys.stdout):
    """Print, emphasized based on rval"""

    if rval is None:    # rval is not specified, use 'neutral'
        info(txt, fd=fd)
    elif rval == 0:     # rval is 0, by convention, this is 'good'
        good(txt, fd=fd)
    else:               # any other value, considered 'bad'
        err(txt, fd=fd)

def paths_from_env(prefix=None, names=None):
    """Construct dict of paths from environment variables'"""


    def expand_path(path):
        """Expands variables in 'path' and turns it into absolute path"""

        return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


    if prefix is None:
        prefix = "CIJ"
    if names is None:
        names = [
            "ROOT", "ENVS", "TESTPLANS", "TESTCASES", "TESTSUITES", "MODULES",
            "HOOKS", "TEMPLATES"
        ]

    conf = {v: os.environ.get("_".join([prefix, v])) for v in names}

    for env in (e for e in conf.keys() if e[:len(prefix)] in names and conf[e]):
        conf[env] = expand_path(conf[env])
        if not os.path.exists(conf[env]):
            err("%s_%s: %r, does not exist" % (prefix, env, conf[env]))

    return conf

def env_to_dict(prefix, names):
    """
    Construct dict from environment variables named: PREFIX_NAME

    @returns dict of names
    """

    env = {}
    for name in names:
        env[name] = ENV.get("_".join([prefix, name]))
        if env[name] is None:
            return None

    return env


def env_export(prefix, exported, env):
    """
    Define the list of 'exported' variables with 'prefix' with values from 'env'
    """

    for exp in exported:
        ENV["_".join([prefix, exp])] = env[exp]
