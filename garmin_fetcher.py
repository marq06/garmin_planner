"""
Garmin Fetcher - Standalone CLI to fetch last activity's INTERVAL_ACTIVE split.

Usage:
  python -m garmin_planner.fetcher_main [--output {table,json,csv}]
  or
  python garmin_fetcher.py [--output {table,json,csv}]
"""

from garmin_planner.fetcher_main import main

if __name__ == "__main__":
    main()
