"""
Test script to verify fetcher logic with example splits.txt data.
"""

import json
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from garmin_planner.fetcher_main import (
    extract_interval_active_splits,
    format_all_splits,
    convert_speed_ms_to_minkm
)

# Load example splits from activities_example/splits.txt
example_splits_path = os.path.join(
    os.path.dirname(__file__),
    'garmin_planner', 'activities_example', 'splits.txt'
)

try:
    # Parse the response from the example file
    with open(example_splits_path, 'r') as f:
        content = f.read()
        # Extract JSON from the file (it's after "response:")
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        json_str = content[json_start:json_end]
        splits_response = json.loads(json_str)
    
    print("✓ Loaded example splits data")
    print(f"  Total splits: {len(splits_response['splits'])}")
    
    # Test extraction
    active_splits = extract_interval_active_splits(splits_response)
    if active_splits:
        print(f"✓ Found {len(active_splits)} INTERVAL_ACTIVE splits")
        
        # Test formatting
        splits_data = format_all_splits(active_splits)
        print("✓ Formatted all splits:")
        for idx, split_data in enumerate(splits_data):
            print(f"  Split {idx+1}:")
            for key, value in split_data.items():
                print(f"    {key}: {value}")
        
        print("\n✓ All tests passed!")
    else:
        print("✗ Failed to find INTERVAL_ACTIVE splits")
        sys.exit(1)

except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
