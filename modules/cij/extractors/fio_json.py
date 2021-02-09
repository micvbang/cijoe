#!/usr/bin/env python3
from __future__ import annotations
import os
import json
import glob
import dataclasses
from typing import List

import yaml

from cij.runner import TestCase
import cij

"""
DEV NOTES:

The purpose with this file  is to provide basic functionality to make it easier
to implement custom extractors for fio.
It should probably be placed somewhere else, but I'm not sure where...
"""


def _make_context(d: dict, fname: str, job_id: int) -> dict:
    opt = d["global options"]
    return {
        "timestamp": d["timestamp"],
        "ioengine": opt["ioengine"],
        "bs": opt["bs"],
        "iodepth": opt["iodepth"],
        "fname": fname,
        "job_id": job_id,
    }


@dataclasses.dataclass
class IOPS:
    ctx: dict
    read: float
    write: float
    trim: float


def extract_iops(fio_fpaths: List[str]) -> List[IOPS]:
    """
    Parse fio-output files and return the iops for the `job_index`th job
    """
    metrics = []

    for fpath in fio_fpaths:
        pmetric = parse_fio_output_file(fpath)

        for n, job in enumerate(pmetric["jobs"]):
            ctx = _make_context(
                pmetric,
                fname=os.path.basename(fpath),
                job_id=n,
            )

            metrics.append(IOPS(
                ctx=ctx,
                read=job["read"]["iops"],
                write=job["write"]["iops"],
                trim=job["trim"]["iops"],
            ))

    return metrics

def dump_metrics_to_file(metrics: List[dict], aux_root: str):
    """
    Dump a list of measured metrics to metrics.yml at aux_root.
    """

    fpath = os.path.join(aux_root, "metrics.yml")
    with open(fpath, 'w') as yml_file:
        data = yaml.dump(
            metrics, explicit_start=True, default_flow_style=False
        )
        yml_file.write(data)


def get_fio_output_files(tcase: TestCase) -> List[str]:
    """ Return a list of fio-output files from the TestCase aux directory """
    return list(glob.glob(os.path.join(tcase.aux_root, "fio-output*")))


def parse_fio_output_file(fpath: str) -> dict:
    """ Read and parse json from fio json outputs """
    lines = []

    with open(fpath, 'r') as fiof:
        do_append = False
        for l in fiof:
            if l.startswith('{'):
                do_append = True

            if do_append:
                lines.append(l)

            if l.startswith('}'):
                break

    return json.loads(''.join(lines))
