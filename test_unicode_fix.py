#!/usr/bin/env python3
"""
Test script to verify the Unicode character cleaning and robust JSON parsing fixes
"""

import json
import sys
import os

# Add the project path to Python path
sys.path.insert(0, '/home/lash_fire/Documents/Projects/synthetic-data-kit1')

from synthetic_data_kit.generators.synthetic_data_generator import clean_unicode_characters, parse_synthetic_examples

def test_unicode_cleaning():
    """Test the Unicode character cleaning function"""
    print("Testing Unicode character cleaning...")
    
    # Test text with problematic Unicode characters
    test_text = """
    {
        "OCR text": "NetWt 500 gm | Packd on 03-02-2024 | MRP \u20b9 150/- | use by 02/26",
        "Structured Output": {
            "net_weight": "500g",
            "packed_date": "03/02/2024",
            "mrp": "150",
            "expiry_date": "01/02/2026"
        }
    }
    """
    
    cleaned = clean_unicode_characters(test_text)
    print(f"Original: {repr(test_text[:100])}")
    print(f"Cleaned:  {repr(cleaned[:100])}")
    
    # Check if the rupee symbol was replaced
    if '\u20b9' not in cleaned and 'Rs.' in cleaned:
        print("✅ Unicode cleaning works correctly")
        return True
    else:
        print("❌ Unicode cleaning failed")
        return False

def test_json_parsing():
    """Test the robust JSON parsing function"""
    print("\nTesting robust JSON parsing...")
    
    # Test case 1: Malformed JSON with extra commas and newlines
    malformed_json = '''
    [
        {
            "OCR text": "MFD: 01-07-23 EXP 01.01.25 M.R.P Rs.129/- Net wt : 200g",
            "Structured Output": {
                "manufacturing_date": "01/07/2023",
                "expiry_date": "01/01/2025",
                "mrp": "129",
                "net_weight": "200g",
            }
        },
        {
            "OCR text": "B.No:XYZ12K3 Mfg Dt: 12/05/22 Best before 18mnths MRP Rs. 75/- wt 75 g",
            "Structured Output": {
                "batch_number": "XYZ12K3",
                "manufacturing_date": "12/05/2022",
                "expiry_duration": "18 months",
                "mrp": "75",
                "net_weight": "75g",
            }
        },
    ]
    '''
    
    try:
        result = parse_synthetic_examples(malformed_json, verbose=True)
        if isinstance(result, list) and len(result) == 2:
            print("✅ Robust JSON parsing works correctly")
            print(f"   Parsed {len(result)} examples successfully")
            return True
        else:
            print("❌ Robust JSON parsing failed - wrong result type or length")
            return False
    except Exception as e:
        print(f"❌ Robust JSON parsing failed with error: {e}")
        return False

def test_combined():
    """Test Unicode cleaning + JSON parsing together"""
    print("\nTesting combined Unicode cleaning + JSON parsing...")
    
    # Test with Unicode characters in malformed JSON
    test_json = '''
    [
        {
            "OCR text": "NetWt 500 gm | MRP \u20b9 150/- | use by 02/26",
            "Structured Output": {
                "net_weight": "500g",
                "mrp": "150",
                "expiry_date": "01/02/2026",
            }
        },
    ]
    '''
    
    try:
        result = parse_synthetic_examples(test_json, verbose=True)
        if isinstance(result, list) and len(result) == 1:
            # Check if Unicode was cleaned in the result
            ocr_text = result[0].get("OCR text", "")
            if '\u20b9' not in ocr_text and 'Rs.' in ocr_text:
                print("✅ Combined Unicode cleaning + JSON parsing works correctly")
                return True
            else:
                print("❌ Unicode cleaning didn't work in JSON parsing")
                return False
        else:
            print("❌ Combined test failed - wrong result")
            return False
    except Exception as e:
        print(f"❌ Combined test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Unicode and JSON parsing fixes...")
    print("=" * 50)
    
    # Run all tests
    test1 = test_unicode_cleaning()
    test2 = test_json_parsing()
    test3 = test_combined()
    
    print("\n" + "=" * 50)
    if all([test1, test2, test3]):
        print("🎉 All tests passed! The fixes are working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
