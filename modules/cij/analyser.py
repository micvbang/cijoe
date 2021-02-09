#!/usr/bin/env python3
"""
    Library functions for cij_analyser
"""

import re
import glob
import os
import json
from typing import List, Optional
import dataclasses

import yaml

from cij.runner import Status, TestRun, TestCase
import cij.runner
import cij
from cij.errors import CIJError, InvalidRangeError, InitializationError

_units = {
    # general
    '': 1,          # no unit
    'B': 1,         # bytes
    'k': 1000,      # kilo
    'M': 1000**2,   # mega
    'G': 1000**3,   # giga

    # kibi
    'KiB': 1024**1,  # kibibytes
    'MiB': 1024**2,  # mibibytes
    'GiB': 1024**3,  # gibibytes
    'TiB': 1024**4,  # tibibytes

    # kilo
    'kB': 1000**1,  # kilobytes
    'MB': 1000**2,  # megabytes
    'GB': 1000**3,  # gigabytes
    'TB': 1000**4,  # gigabytes

    # time
    'nsec': 1000**3,  # nanoseconds
    'usec': 1000**2,  # microseconds
    'msec': 1000**1,  # milliseconds
    'sec': 1,         # seconds
    'min': 1/60       # minutes
}


class Range:
    """
    Range implements parsing and validation of mathematical range notation,
    e.g. `[-5;100[` which translates to "must be >= -5 and < 100".
    """

    # pylint: disable=no-self-use
    # pylint: disable=too-few-public-methods

    _rng_re = re.compile(
        r"^(?P<elower>\[|\])\s*(?P<rstart>-inf|-?\d+(\.\d*)?)\s*;"  # [1.0;
        r"\s*(?P<rend>inf|-?\d+(\.\d*)?)\s*(?P<eupper>\[|\])"       # 1.0]
        fr"\s*(?P<unit>({'|'.join(_units)}))$"                      # ms
    )

    def __init__(self, rng: str):
        match = self._rng_re.match(rng)
        if not match:
            raise InvalidRangeError(f"invalid range \"{rng}\"")

        rng_start = float(match["rstart"])
        rng_end = float(match["rend"])
        if rng_start > rng_end:
            raise InvalidRangeError(
                "expected lower bound <= upper bound, "
                f"{rng_start} <= {rng_end}"
            )

        if match["unit"] not in _units:
            raise InvalidRangeError(
                f"unexpected unit '{match['unit']}', "
                f"supported units are: {list(_units.keys())}"
            )

        unit_val = _units[match["unit"]]

        self._rng_start = rng_start
        self._rng_end = rng_end
        self._elower = match["elower"]
        self._eupper = match["eupper"]
        self._unit = match["unit"]

        self._check_lower = self._make_check_lower(match["elower"],
                                                   rng_start * unit_val)
        self._check_upper = self._make_check_upper(match["eupper"],
                                                   rng_end * unit_val)

    def contains(self, val: float) -> bool:
        """ Check whether n is contained in range.
        """
        return self._check_lower(val) and self._check_upper(val)

    def _make_check_lower(self, edge_lower: str, rng_start: float):
        if edge_lower == '[':
            return lambda n: n >= rng_start
        if edge_lower == ']':
            return lambda n: n > rng_start
        raise InvalidRangeError("invalid input _make_check_lower")

    def _make_check_upper(self, edge_upper: str, rng_end: float):
        if edge_upper == '[':
            return lambda n: n < rng_end
        if edge_upper == ']':
            return lambda n: n <= rng_end
        raise InvalidRangeError("invalid input _make_check_upper")

    def __str__(self):
        return (f"{self._elower}{self._rng_start};"
                f"{self._rng_end}{self._eupper} {self._unit}")


def preqs_from_file(fpath):
    """ Read yaml-formatted performance requirements from fpath """

    with open(fpath, 'r') as preqf:
        return yaml.safe_load(preqf)


def plog_from_file(fpath):
    """ Read json-formatted performance log from fpath """

    with open(fpath, 'r') as plogf:
        return json.load(plogf)


@dataclasses.dataclass
class CheckedPreq:
    """ Contains information about checked performance requirements """
    key: str
    error: bool
    msg: str
    ctx: dict


def check_preqs(preqs, metrics) -> List[CheckedPreq]:
    """
    Check performance requirements against measured metrics.
    """

    checked_preqs = []

    def add_preq(key: str, msg: str, error: bool, ctx: dict):
        checked_preqs.append(
            CheckedPreq(key=key, msg=msg, error=error, ctx=ctx)
        )

    for pkey, rng_str in preqs.items():
        ctx = metrics.get('ctx', {})
        mval = metrics.get(pkey, None)
        if mval is None:
            add_preq(key=pkey, error=True, ctx=ctx,
                     msg="expected to be measured, but wasn't")
            continue

        try:
            rng = Range(rng_str)
        except InvalidRangeError as ex:
            add_preq(key=pkey, error=True, ctx=ctx,
                     msg=f"invalid range \"{rng_str}\": {ex}")
            continue

        if not rng.contains(mval):
            add_preq(key=pkey, error=True, ctx=ctx,
                     msg=f"{mval:.3f} in {rng_str} failed")
            continue

        add_preq(key=pkey, error=False, ctx=ctx,
                 msg=f"{mval:.3f} in {rng_str} satisfied")

    return checked_preqs


def analyse_prequirements(trun: TestRun, preqs_declr):
    """
    Analyse trun and enforce test pass/fail based on the given performance
    requirements declaration.

    NOTE: updates relevant trun fields.
    """
    global_conf = preqs_declr.get("global", {})
    global_preqs = global_conf.get("testcases", {})

    tr_err = 0

    for tsuite in trun.testsuites:
        ts_err = 0
        tsuite_preqs = preqs_declr.get(tsuite.name, {})

        for tcase in tsuite.testcases:
            tcase_preqs = global_preqs.get(tcase.name, {})
            tcase_preqs.update(tsuite_preqs.get(tcase.name, {}))
            if not tcase_preqs:
                continue

            cij.info(f"{tsuite.name}/{tcase.name} checking {set(tcase_preqs)}")

            tc_err = 0

            test_metrics = _get_metrics(tcase.aux_root)
            if not test_metrics:
                tc_err += 1
                cij.err(f"Expected {set(tcase_preqs)} to be measured")

            # Check performance requirements against measured metrics
            with open(tcase.analysis_log_fpath, 'a') as alog:
                for metrics in test_metrics:
                    checked_preqs = check_preqs(tcase_preqs, metrics)
                    for cp in checked_preqs:
                        cij.emph(f"{cp.key}: {cp.msg}", rval=int(cp.error))
                        cij.emph(f"{cp.key}: {cp.msg} {cp.ctx}",
                                 rval=int(cp.error), file=alog)

                tc_err += sum(cp.error for cp in checked_preqs)

            cij.info(f"Flushed analysis log ({tcase.analysis_log_fpath})")
            tcase.status_preq = Status.Fail if tc_err else Status.Pass
            ts_err += tc_err

        tsuite.status_preq = Status.Fail if ts_err else Status.Pass
        tr_err += ts_err

    trun.status_preq = Status.Fail if tr_err else Status.Pass
    return 0


def _get_metrics(aux_root: str) -> List[dict]:
    fpath = os.path.join(aux_root, "metrics.yml")

    if not os.path.exists(fpath):
        return []

    with open(fpath, 'r') as yml_file:
        return yaml.safe_load(yml_file)


def main(args):
    """
    Run cij analyser steps.

    If `preqs` is set, log files in the given TRUN path are searched
    for metric.yml-files and the TRUN will be updated with pass/fail for
    performance requirements.
    """
    trun = cij.runner.trun_from_file(args.trun_fpath)

    try:
        err = 0
        if args.preqs:
            preqs_declr = preqs_from_file(args.preqs)
            preq_err = analyse_prequirements(trun, preqs_declr)
            if preq_err:
                cij.err('Failed to analyse prequirements')
            else:
                cij.info('Successfully analyzed prequirements')

            err += preq_err

        cij.runner.trun_to_file(trun)
    except CIJError as ex:
        cij.err(f"main:FAILED to run analysis: {ex}")

    return err
