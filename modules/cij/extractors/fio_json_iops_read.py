
from typing import Collection, List, Dict

from cij.runner import TestCase
from cij.extractors import fio_json


def extract_metrics(tcase: TestCase) -> List[dict]:
    """
    Locate testcase fio-output files and parse them.
    Writes metrics to aux_root/metrics.yml and returns them.
    """
    fpaths = fio_json.get_fio_output_files(tcase)

    metrics = []
    for iops in fio_json.extract_iops(fpaths):
        metrics.append({
            'ctx': iops.ctx,
            'iops': iops.read,
        })


    fio_json.dump_metrics_to_file(metrics, tcase.aux_root)

    return metrics


if __name__ == "__main__":
    """
    input: path to trun

    1. parse trun
    2. loop over testcases
    3. get_measurements for each testcase
    """
