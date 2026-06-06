#!/usr/bin/env python3
"""
B+ Plus ERP Centralize — Daily Batch
Usage examples:
  python run_batch.py                          # daily incremental, all branches
  python run_batch.py --frequency weekly       # weekly master sync
  python run_batch.py --frequency once         # first-time config tables
  python run_batch.py --full                   # force full reload (all daily tables)
  python run_batch.py --table DOCINFO --full   # full reload one table
  python run_batch.py --branch-id 1            # one branch only
"""
import argparse
import logging
import sys
from etl import orchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('batch.log', encoding='utf-8'),
    ]
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='B+ ERP Centralize Batch')
    parser.add_argument(
        '--frequency', '-f',
        choices=['daily', 'weekly', 'monthly', 'once'],
        default='daily',
        help='Which frequency group to sync (default: daily)'
    )
    parser.add_argument(
        '--branch-id', '-b',
        type=int,
        metavar='ID',
        help='Sync specific branch only'
    )
    parser.add_argument(
        '--table', '-t',
        metavar='TABLE_NAME',
        help='Sync specific table only (case-insensitive)'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Force full load (truncate branch rows then reload)'
    )
    args = parser.parse_args()

    orchestrator.run(
        frequency=args.frequency,
        branch_id=args.branch_id,
        table_name=args.table,
        force_full=args.full,
    )
