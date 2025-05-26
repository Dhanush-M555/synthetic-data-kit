#!/usr/bin/env python3
"""
Debug script for seed curation functionality
"""

import json
import os
import sys

# Add the project to the path
sys.path.insert(0, '/home/lash_fire/Documents/Projects/synthetic-data-kit1')

def test_api_rating():
    """Test if API can rate a simple example"""
    try:
        from synthetic_data_kit.models.llm_client import LLMClient
        from synthetic_data_kit.utils.config import get_prompt
        
        print("Testing API rating functionality...")
        
        # Initialize LLM client
        client = LLMClient(
            config_path='/home/lash_fire/Documents/Projects/synthetic-data-kit1/configs/config.yaml',
            provider='api-endpoint'
        )
        
        # Get the seed rating prompt
        seed_rating_prompt = get_prompt(client.config, 'seed_rating')
        print(f"Prompt loaded successfully. Length: {len(seed_rating_prompt)} chars")
        
        # Create a simple test example
        test_example = {
            "OCR text": "MFD: 01-07-23 EXP 01.01.25 M.R.P Rs129/- Net wt : 200g",
            "Structured Output": {
                "manufacturing_date": "01/07/2023",
                "expiry_date": "01/01/2025", 
                "mrp": "129",
                "net_weight": "200g"
            }
        }
        
        # Format the prompt
        examples_json = json.dumps([test_example], indent=2)
        rating_prompt = seed_rating_prompt.format(examples=examples_json)
        
        print("Sending test example to API...")
        
        # Make API call
        response = client.chat_completion(
            [{"role": "system", "content": rating_prompt}],
            temperature=0.1
        )
        
        print(f"API Response: {response}")
        
        # Try to parse the response
        try:
            parsed_response = json.loads(response.strip())
            print(f"Parsed response: {parsed_response}")
            
            if isinstance(parsed_response, list) and len(parsed_response) > 0:
                first_item = parsed_response[0]
                if "rating" in first_item:
                    rating = first_item["rating"]
                    print(f"✅ Rating extracted successfully: {rating}")
                    return True
                else:
                    print("❌ No 'rating' key found in response")
                    return False
            else:
                print("❌ Response is not a list or is empty")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ API rating test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Debug Seed Curation ===\n")
    
    if test_api_rating():
        print("\n✅ API rating test passed!")
    else:
        print("\n❌ API rating test failed!")
