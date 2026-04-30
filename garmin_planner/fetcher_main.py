from garmin_planner.client import Client
from garmin_planner.__init__ import logger
from datetime import datetime, timedelta
import argparse
import json
import csv
import sys
import os

def find_latest_activity(conn: Client):
    """Fetch latest activity by date from Garmin Connect."""
    try:
        activities = conn.getActivities(limit=10)
        if not activities:
            logger.error("No activities found")
            return None
        
        # Parse startTimeGMT and find the most recent activity
        latest_activity = None
        latest_time = None
        
        for activity in activities:
            try:
                start_time_str = activity.get('startTimeGMT')
                if start_time_str:
                    # Parse ISO format datetime
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    if latest_time is None or start_time > latest_time:
                        latest_time = start_time
                        latest_activity = activity
            except Exception as e:
                logger.warning(f"Failed to parse activity time: {e}")
                continue
        
        if latest_activity:
            logger.info(f"Found latest activity: {latest_activity.get('activityId')}")
        return latest_activity
    
    except Exception as e:
        logger.error(f"Failed to fetch activities: {e}")
        return None


def extract_interval_active_splits(splits_response: dict):
    """Extract all INTERVAL_ACTIVE splits from splits response."""
    try:
        splits = splits_response.get('splits', [])
        if not splits:
            logger.warning("No splits found in response")
            return []
        
        active_splits = [s for s in splits if s.get('type') == 'INTERVAL_ACTIVE']
        if not active_splits:
            logger.warning("No INTERVAL_ACTIVE splits found")
            return []
        
        logger.info(f"Found {len(active_splits)} INTERVAL_ACTIVE splits")
        return active_splits
    
    except Exception as e:
        logger.error(f"Failed to extract INTERVAL_ACTIVE splits: {e}")
        return []


def convert_speed_ms_to_minkm(speed_ms: float) -> str:
    """Convert speed from m/s to min/km format (MM:SS)."""
    if speed_ms == 0:
        return "∞"
    
    # Speed in km/h = speed_m/s * 3.6
    # Pace in min/km = 60 / speed_km/h = 60 / (speed_m/s * 3.6)
    pace_min_per_km = 60 / (speed_ms * 3.6)
    minutes = int(pace_min_per_km)
    seconds = int((pace_min_per_km - minutes) * 60)
    return f"{minutes}:{seconds:02d}"


def format_split_data(split: dict, split_index: int) -> dict:
    """Format a single split for output."""
    if split is None:
        return None
    
    avg_speed_ms = split.get('averageSpeed', 0)
    distance_m = split.get('distance', 0)
    duration_sec = split.get('duration', 0)
    avg_hr = int(split.get('averageHR', 0))
    max_hr = int(split.get('maxHR', 0))
    message_index = split.get('messageIndex', split_index)
    
    return {
        'split_number': message_index,
        'avg_speed_minkm': convert_speed_ms_to_minkm(avg_speed_ms),
        'avg_hr': avg_hr,
        'max_hr': max_hr,
        'distance_m': round(distance_m, 2),
        'duration_sec': round(duration_sec, 2)
    }


def format_all_splits(splits: list) -> list:
    """Format all splits for output."""
    return [format_split_data(split, idx) for idx, split in enumerate(splits)]


def print_table(splits_data: list, metadata: dict):
    """Print splits data as formatted table (CSV-like with one split per row)."""
    if not splits_data:
        print("No data to display")
        return
    
    # Print metadata
    print(f"Activity: {metadata['activity_name']}")
    print(f"Start Time CET: {metadata['start_time_cet']}")
    print(f"End Time CET: {metadata['end_time_cet']}")
    print()
    
    # Print header
    headers = ['split_number', 'avg_speed_minkm', 'avg_hr', 'max_hr', 'distance_m', 'duration_sec']
    print(" | ".join(f"{h:^20}" for h in headers))
    print("-" * (21 * len(headers) - 1))
    
    # Print each split
    for split in splits_data:
        row = [
            str(split['split_number']),
            split['avg_speed_minkm'],
            str(split['avg_hr']),
            str(split['max_hr']),
            str(split['distance_m']),
            str(split['duration_sec'])
        ]
        print(" | ".join(f"{val:^20}" for val in row))


def print_json(splits_data: list, metadata: dict):
    """Print splits data as JSON."""
    if not splits_data:
        print(json.dumps({"error": "No data to display"}))
    else:
        output = {
            "metadata": metadata,
            "splits": splits_data
        }
        print(json.dumps(output, indent=2))


def print_csv(splits_data: list, metadata: dict):
    """Print splits data as CSV."""
    if not splits_data:
        print("error,No data to display")
        return
    
    # Print header
    fieldnames = list(splits_data[0].keys())
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    
    # Print each split row
    for split in splits_data:
        writer.writerow(split)
    
    # Add metadata at the end (with empty first columns to not break Excel)
    print(f",,Activity Name,{metadata['activity_name']}")
    print(f",,Start Time CET,{metadata['start_time_cet']}")
    print(f",,End Time CET,{metadata['end_time_cet']}")


def print_compact(splits_data: list, metadata: dict):
    """Print splits data in compact format suitable for text messages."""
    if not splits_data:
        print("No data to display")
        return
    
    # Print metadata
    print(f"Activity: {metadata['activity_name']}")
    print(f"Start: {metadata['start_time_cet']} CET")
    print(f"End: {metadata['end_time_cet']} CET")
    print()
    
    print("split# / pace / avg_hr / max_hr / distance(m) / duration(s)")
    
    for split in splits_data:
        # Format distance: if whole number, print as int, else float
        distance = split['distance_m']
        if distance == int(distance):
            distance_str = str(int(distance))
        else:
            distance_str = f"{distance:.1f}"
        
        # Duration rounded to 1 decimal
        duration_str = f"{split['duration_sec']:.1f}"
        
        print(f"#{split['split_number']} / {split['avg_speed_minkm']} / {split['avg_hr']} / {split['max_hr']} / {distance_str} / {duration_str}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch last activity's INTERVAL_ACTIVE splits from Garmin Connect"
    )
    parser.add_argument(
        '--output',
        choices=['table', 'json', 'csv', 'compact'],
        default='table',
        help='Output format (default: table)'
    )
    args = parser.parse_args()
    
    try:
        # Load credentials from secrets.yaml
        current_dir = os.path.dirname(os.path.abspath(__file__))
        from garmin_planner.parser import parseYaml
        
        secrets = parseYaml(os.path.join(current_dir, "secrets.yaml"))
        if not secrets or 'email' not in secrets or 'password' not in secrets:
            logger.error("Missing credentials in secrets.yaml")
            sys.exit(1)
        
        # Connect and fetch
        conn = Client(secrets['email'], secrets['password'])
        activity = find_latest_activity(conn)
        
        if not activity:
            logger.error("Failed to fetch activities")
            sys.exit(1)
        
        # Compute metadata
        activity_name = activity.get('activityName', 'Unknown')
        start_time_gmt_str = activity.get('startTimeGMT')
        duration_sec = activity.get('duration', 0)
        
        if start_time_gmt_str:
            start_time_gmt = datetime.fromisoformat(start_time_gmt_str.replace('Z', '+00:00'))
            end_time_gmt = start_time_gmt + timedelta(seconds=duration_sec)
            # CET is UTC+2 for April 30, 2026 (DST)
            cet_offset = timedelta(hours=2)
            start_time_cet = start_time_gmt + cet_offset
            end_time_cet = end_time_gmt + cet_offset
            metadata = {
                'activity_name': activity_name,
                'start_time_cet': start_time_cet.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time_cet': end_time_cet.strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            metadata = {
                'activity_name': activity_name,
                'start_time_cet': 'Unknown',
                'end_time_cet': 'Unknown'
            }
        
        activity_id = activity.get('activityId')
        splits_response = conn.getActivitySplits(activity_id)
        active_splits = extract_interval_active_splits(splits_response)
        
        if not active_splits:
            logger.error("No INTERVAL_ACTIVE splits found")
            sys.exit(1)
        
        splits_data = format_all_splits(active_splits)
        
        # Output in requested format
        if args.output == 'json':
            print_json(splits_data, metadata)
        elif args.output == 'csv':
            print_csv(splits_data, metadata)
        elif args.output == 'compact':
            print_compact(splits_data, metadata)
        else:  # table
            print_table(splits_data, metadata)
        
        logger.info("Successfully fetched all activity splits")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
