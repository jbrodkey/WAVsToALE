#!/usr/bin/env python3
"""
Smoke test for UCS best-guess matching.
Tests the scoring algorithm with sample filenames.
"""

import sys
import os

# Add parent dir to path to import the main script
sys.path.insert(0, os.path.dirname(__file__))

# Import the functions we need to test
import importlib.util
spec = importlib.util.spec_from_file_location("wav_main", "wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py")
wav_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wav_main)

def test_best_guess():
    """Test UCS best-guess scoring with sample filenames"""
    
    # Load UCS data
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'UCS_v8.2.1_Full_List.csv')
    if not os.path.exists(csv_path):
        print(f"Error: UCS CSV not found at {csv_path}")
        return False
    
    wav_main.UCS_MAPPING = wav_main.load_ucs_mapping(csv_path)
    
    if not wav_main.UCS_MAPPING:
        print("Error: Failed to load UCS mapping")
        return False
    
    print(f"Loaded {len(wav_main.UCS_MAPPING)} UCS entries\n")
    
    # Test cases: (filename, expected_category_hint, expected_subcategory_hint)
    test_cases = [
        ("FOOTCnc_Running_Fast.wav", "FOOT", "Concrete - exact prefix match"),
        ("door_close_heavy_wooden.wav", "DOOR", "close"),
        ("footsteps_concrete_running.wav", "FOOT", "foot"),
        ("wind_howling_storm.wav", "wind", "weather"),
        ("glass_break_bottle_smash.wav", "glass", "break"),
    ]
    
    print("=" * 80)
    print("UCS BEST-GUESS SMOKE TEST")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        filename = test[0]
        print(f"\nTest {i}: {filename}")
        print("-" * 80)
        
        result = wav_main.best_guess_ucs(filename, min_confidence_threshold=0.0, low_confidence_threshold=25.0)
        
        if result:
            print(f"  UCS ID:      {result['ucs_id']}")
            print(f"  Category:    {result['category']}")
            print(f"  Subcategory: {result['subcategory']}")
            print(f"  Score:       {result['score']:.1f}")
            print(f"  Low Conf:    {result['low_confidence']}")
            if result.get('alternatives'):
                print(f"  Alternatives: {', '.join(result['alternatives'][:3])}")
            
            # Check if result makes sense
            if len(test) > 2:
                hint_cat = test[1].lower() if isinstance(test[1], str) else ""
                hint_sub = test[2].lower() if isinstance(test[2], str) else ""
                cat_match = hint_cat in result['category'].lower() if hint_cat else True
                sub_match = hint_sub in result['subcategory'].lower() if hint_sub else True
                
                if cat_match or sub_match:
                    print(f"  ✓ Match looks reasonable")
                else:
                    print(f"  ⚠ Expected hints: {test[1]}, {test[2]}")
        else:
            print("  No match found")
            if len(test) > 1:
                print(f"  ⚠ Expected a match")
    
    print("\n" + "=" * 80)
    print("Smoke test complete!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = test_best_guess()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
