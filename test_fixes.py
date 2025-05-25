#!/usr/bin/env python3
"""
Test script to verify our fixes for JSON parsing and Unicode handling
"""

import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthetic_data_kit.generators.synthetic_data_generator import clean_unicode_characters, parse_synthetic_examples

def test_unicode_cleaning():
    """Test Unicode character cleaning"""
    print("=== Testing Unicode Character Cleaning ===")
    
    test_cases = [
        ("MRP \u20b9 150/- Net weight 200g", "MRP Rs. 150/- Net weight 200g"),
        ("Price: \u20ac50 or \u00a330", "Price: EUR50 or GBP30"),
        ("It\u2019s a \u201cgood\u201d product", "It's a \"good\" product"),
    ]
    
    for original, expected in test_cases:
        cleaned = clean_unicode_characters(original)
        print(f"Original: {repr(original)}")
        print(f"Expected: {repr(expected)}")
        print(f"Cleaned:  {repr(cleaned)}")
        print(f"✓ Pass" if cleaned == expected else f"✗ Fail")
        print()

def test_json_parsing():
    """Test robust JSON parsing"""
    print("=== Testing JSON Parsing ===")
    
    # Test case 1: Well-formatted JSON
    test1 = '''[
  {
    "OCR text": "MFD: 01-07-23 EXP 01.01.25 M.R.P Rs129/- Net wt : 200g",
    "Structured Output": {
      "manufacturing_date": "01/07/2023",
      "expiry_date": "01/01/2025",
      "mrp": "129",
      "net_weight": "200g"
    }
  }
]'''
    
    # Test case 2: JSON with trailing commas (common LLM error)
    test2 = '''[
  {
    "OCR text": "MFD: 01-07-23 EXP 01.01.25 M.R.P Rs129/- Net wt : 200g",
    "Structured Output": {
      "manufacturing_date": "01/07/2023",
      "expiry_date": "01/01/2025",
      "mrp": "129",
      "net_weight": "200g",
    },
  }
]'''
    
    # Test case 3: JSON in markdown code block
    test3 = '''Here are the examples:
```json
[
  {
    "OCR text": "MFD: 01-07-23 EXP 01.01.25 M.R.P Rs129/- Net wt : 200g",
    "Structured Output": {
      "manufacturing_date": "01/07/2023",
      "expiry_date": "01/01/2025",
      "mrp": "129",
      "net_weight": "200g"
    }
  }
]
```'''
    
    # Test case 4: JSON with Unicode characters
    test4 = '''[
  {
    "OCR text": "NetWt 500 gm | Packd on 03-02-2024 | MRP \\u20b9 150/- | use by 02/26",
    "Structured Output": {
      "net_weight": "500g",
      "packed_date": "03/02/2024",
      "mrp": "150",
      "expiry_date": "02/02/2026"
    }
  }
]'''
    
    test_cases = [
        ("Well-formatted JSON", test1),
        ("JSON with trailing commas", test2),
        ("JSON in markdown code block", test3),
        ("JSON with Unicode characters", test4),
    ]
    
    for name, test_json in test_cases:
        print(f"Testing: {name}")
        try:
            examples = parse_synthetic_examples(test_json, verbose=True)
            print(f"✓ Successfully parsed {len(examples)} examples")
            print(f"First example: {examples[0] if examples else 'None'}")
        except Exception as e:
            print(f"✗ Failed to parse: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_unicode_cleaning()
    test_json_parsing()
    print("=== All tests completed ===")
