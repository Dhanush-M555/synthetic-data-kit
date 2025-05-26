#!/usr/bin/env python3
"""
Test script for seed curation functionality
"""

import json
import os
from pathlib import Path
import sys

# Add the project to the path
sys.path.insert(0, '/home/lash_fire/Documents/Projects/synthetic-data-kit1')

def test_config_loading():
    """Test if configuration loads correctly and has seed_curate settings"""
    try:
        from synthetic_data_kit.utils.config import load_config, get_seed_curate_config, get_prompt
        
        print("Testing configuration loading...")
        config = load_config('/home/lash_fire/Documents/Projects/synthetic-data-kit1/configs/config.yaml')
        
        # Test seed_curate config
        seed_curate_config = get_seed_curate_config(config)
        print(f"Seed curate config: {seed_curate_config}")
        
        # Test seed_rating prompt
        seed_rating_prompt = get_prompt(config, 'seed_rating')
        print(f"Seed rating prompt length: {len(seed_rating_prompt)} chars")
        print("Configuration test: PASSED")
        return True
        
    except Exception as e:
        print(f"Configuration test: FAILED - {e}")
        return False

def test_data_structure():
    """Test if we can parse the seed-generated data correctly"""
    try:
        print("\nTesting data structure parsing...")
        
        input_file = '/home/lash_fire/Documents/Projects/synthetic-data-kit1/data/generated/ocr_seed_examples_seed_generated.json'
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Data keys: {list(data.keys())}")
        
        # Extract examples based on our logic
        if isinstance(data, dict):
            if "examples" in data:
                examples = data["examples"]
                print(f"Found {len(examples)} examples")
            else:
                print("No 'examples' key found")
                return False
        else:
            print("Data is not a dictionary")
            return False
            
        # Check structure of first example
        if examples:
            first_example = examples[0]
            print(f"First example keys: {list(first_example.keys())}")
            print("Data structure test: PASSED")
            return True
        else:
            print("No examples found")
            return False
            
    except Exception as e:
        print(f"Data structure test: FAILED - {e}")
        return False

def test_imports():
    """Test if all required imports work"""
    try:
        print("\nTesting imports...")
        from synthetic_data_kit.core.curate import curate_seed_examples, parse_seed_ratings
        from synthetic_data_kit.utils.config import get_seed_curate_config
        print("All imports: PASSED")
        return True
    except Exception as e:
        print(f"Import test: FAILED - {e}")
        return False

def run_tests():
    """Run all tests"""
    print("=== Seed Curation Test Suite ===\n")
    
    tests = [
        test_imports,
        test_config_loading,
        test_data_structure,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Seed curation implementation is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
