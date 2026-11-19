#!/usr/bin/env python3
"""Run or resume the French Wikipedia category index on the host."""
import argparse
from pathlib import Path

import setup
from delivery_paths import locked
from pilot import category_index
from runtime_resources import background_worker


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--cancel',type=Path)
    parser.add_argument('--job-id')
    args=parser.parse_args()
    data=setup.safe_path(args.data_dir)
    state=data/'state/pilot'
    background_worker()
    with locked(state/'archive-index/operation.lock'):
        category_index.prepare(data/'library/zim',state,cancel=args.cancel,job_id=args.job_id)


if __name__=='__main__':
    main()
