#!/usr/bin/env python3
"""
    Library functions for cij_extractor
"""
from typing import List, Optional, Callable

import cij.runner
from cij import extractors
from cij.runner import TestRun, TestCase
from cij.errors import CIJError, InitializationError

Extractor = Callable[[TestCase], None]

def extract_metrics(trun: TestRun, extractors: List[Extractor]) -> int:
    for tsuite in trun.testsuites:
        for tcase in tsuite.testcases:
            for extractor in extractors:
                extractor.extract_metrics(tcase)

    return 0


def _get_extractor(name: Optional[str]) -> Extractor:
    if not name:
        return None

    extractor = getattr(extractors, name, None)
    if not extractor:
        raise InitializationError(f"extractor '{name}' not recognized")

    return extractor


def main(args):
    """
    Run cij extractor.

    """
    trun = cij.runner.trun_from_file(args.trun_fpath)

    err = 0
    try:
        extractors = [_get_extractor(args.extractor)]
        err += extract_metrics(trun, extractors)
    except CIJError as ex:
        cij.err(f"main:FAILED to run data extraction: {ex}")
        err += 1

    return err
