# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
# Synthetic Data Generator

from typing import Dict, List, Any, Optional
import json
import os
import re
from pathlib import Path

from synthetic_data_kit.models.llm_client import LLMClient
from synthetic_data_kit.utils.config import load_config, get_generation_config, get_prompt

def clean_unicode_characters(text: str) -> str:
    """Clean problematic Unicode characters from text"""
    # Replace common problematic Unicode characters
    replacements = {
        '\u20b9': 'Rs.',  # Indian Rupee symbol
        '\u20ac': 'EUR',  # Euro symbol
        '\u00a3': 'GBP',  # Pound symbol
        '\u00a5': 'YEN',  # Yen symbol
        '\u0024': '$',    # Dollar symbol (if escaped)
        '\u2019': "'",    # Right single quotation mark
        '\u201c': '"',    # Left double quotation mark
        '\u201d': '"',    # Right double quotation mark
        '\u2013': '-',    # En dash
        '\u2014': '--',   # Em dash
        '\u00a0': ' ',    # Non-breaking space
    }
    
    cleaned_text = text
    for unicode_char, replacement in replacements.items():
        cleaned_text = cleaned_text.replace(unicode_char, replacement)
    
    return cleaned_text

def parse_synthetic_examples(text: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """Parse synthetic examples from LLM output with robust error handling
    
    Uses multiple parsing methods to handle malformed JSON responses from LLMs.
    This is based on the proven approach used in parse_ratings.
    
    Args:
        text: LLM response text to parse
        verbose: Whether to print debug information
    
    Returns:
        List of synthetic examples
        
    Raises:
        ValueError: If the response cannot be parsed as valid JSON
    """
    if verbose:
        print(f"Parsing synthetic examples response of length {len(text)}")
        print(f"Raw response (first 500 chars): {repr(text[:500])}")
    
    # Clean Unicode characters first
    text = clean_unicode_characters(text)
    
    if verbose:
        print(f"Cleaned text (first 500 chars): {repr(text[:500])}")
    
    # Method 1: Handle pretty-printed JSON with newlines
    try:
        # Remove any markdown or text before/after the JSON
        json_content = text.strip()
        
        # Normalize escape sequences
        json_content = json_content.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
        
        # Check if we have a JSON array (which is what we expect for examples)
        if '[' in json_content and ']' in json_content:
            start_idx = json_content.find('[')
            end_idx = json_content.rfind(']') + 1
            json_text = json_content[start_idx:end_idx]
            
            # Clean up the JSON string to handle common issues
            # Convert newlines to spaces in JSON values
            json_text = re.sub(r'\s*\n\s*', ' ', json_text)
            # Remove trailing commas
            json_text = re.sub(r',(\s*\}|\s*\])', r'\1', json_text)
            
            try:
                parsed = json.loads(json_text)
                if isinstance(parsed, list):
                    if verbose:
                        print(f"Successfully parsed {len(parsed)} examples using method 1")
                    return parsed
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"Method 1 JSON parse error: {str(e)}")
        
        # Also try if we have a single JSON object instead of array
        if '{' in json_content and '}' in json_content:
            start_idx = json_content.find('{')
            end_idx = json_content.rfind('}') + 1
            json_text = json_content[start_idx:end_idx]
            
            json_text = re.sub(r'\s*\n\s*', ' ', json_text)
            json_text = re.sub(r',(\s*\}|\s*\])', r'\1', json_text)
            
            try:
                parsed = json.loads(json_text)
                if isinstance(parsed, dict):
                    if verbose:
                        print("Successfully parsed single object using method 1, wrapping in list")
                    return [parsed]
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"Method 1 single object parse error: {str(e)}")
    
    except Exception as e:
        if verbose:
            print(f"Error in method 1: {str(e)}")
    
    # Method 2: Code block extraction from markdown
    try:
        code_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)```', text)
        if code_blocks:
            for block in code_blocks:
                try:
                    # Clean up newlines in the code block
                    clean_block = re.sub(r'\s*\n\s*', ' ', block.strip())
                    # Remove trailing commas
                    clean_block = re.sub(r',(\s*\}|\s*\])', r'\1', clean_block)
                    
                    parsed = json.loads(clean_block)
                    if isinstance(parsed, list):
                        if verbose:
                            print(f"Successfully parsed {len(parsed)} examples from code block")
                        return parsed
                    elif isinstance(parsed, dict):
                        if verbose:
                            print("Successfully parsed single object from code block, wrapping in list")
                        return [parsed]
                except json.JSONDecodeError:
                    if verbose:
                        print(f"Failed to parse code block: {block[:100]}...")
                    pass
    except Exception as e:
        if verbose:
            print(f"Error in method 2 (code block extraction): {str(e)}")
    
    # Method 3: Regex-based pattern matching for common JSON structures
    try:
        # Look for array patterns with common fields
        array_pattern = r'(\[\s*\{.*?\}\s*\])'
        matches = re.findall(array_pattern, text, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    # Clean up the match
                    clean_match = re.sub(r'\s*\n\s*', ' ', match)
                    clean_match = re.sub(r',(\s*\}|\s*\])', r'\1', clean_match)
                    
                    parsed = json.loads(clean_match)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        if verbose:
                            print(f"Successfully parsed {len(parsed)} examples using regex method 3")
                        return parsed
                except json.JSONDecodeError:
                    if verbose:
                        print(f"Failed to parse regex match: {match[:100]}...")
                    pass
    except Exception as e:
        if verbose:
            print(f"Error in method 3 (regex): {str(e)}")
    
    # Method 4: Try json5 if available (more lenient parser)
    try:
        import json5
        try:
            parsed = json5.loads(text)
            if isinstance(parsed, list):
                if verbose:
                    print(f"Successfully parsed {len(parsed)} examples using json5")
                return parsed
            elif isinstance(parsed, dict):
                if verbose:
                    print("Successfully parsed single object using json5, wrapping in list")
                return [parsed]
        except Exception:
            if verbose:
                print("json5 parsing failed")
            pass
    except ImportError:
        if verbose:
            print("json5 not available")
    
    # Method 5: Last resort - try to extract JSON-like objects manually
    try:
        # Look for individual JSON objects in the text
        object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(object_pattern, text)
        
        parsed_objects = []
        for match in matches:
            try:
                # Clean up the match
                clean_match = re.sub(r'\s*\n\s*', ' ', match.strip())
                clean_match = re.sub(r',(\s*\})', r'\1', clean_match)
                
                obj = json.loads(clean_match)
                if isinstance(obj, dict) and obj:  # Non-empty dict
                    parsed_objects.append(obj)
            except json.JSONDecodeError:
                pass
        
        if parsed_objects:
            if verbose:
                print(f"Successfully parsed {len(parsed_objects)} examples using method 5 (object extraction)")
            return parsed_objects
    
    except Exception as e:
        if verbose:
            print(f"Error in method 5 (object extraction): {str(e)}")
    
    # If we reach here, we couldn't extract valid JSON
    if verbose:
        print("All parsing methods failed")
    
    # Include part of the response in the error message for debugging
    error_snippet = text[:200] if len(text) > 200 else text
    raise ValueError(f"Failed to parse JSON response from LLM. Response snippet: {error_snippet}")

class SyntheticDataGenerator:
    def __init__(self, 
                 client: LLMClient,
                 config_path: Optional[Path] = None):
        """Initialize the Synthetic Data Generator with an LLM client and optional config"""
        self.client = client
        
        # Load config
        self.config = load_config(config_path)
        
        # Get specific configurations
        self.generation_config = get_generation_config(self.config)
    
    def generate_from_taxonomy(self, taxonomy_content: str, num_examples: int = 25, verbose: bool = False) -> List[Dict[str, Any]]:
        """Generate synthetic data from a taxonomy structure"""
        if verbose:
            print(f"Generating {num_examples} examples from taxonomy...")
        
        # Get taxonomy generation prompt from config
        prompt_template = get_prompt(self.config, "taxonomy_generation")
        prompt = prompt_template.format(
            num_examples=num_examples,
            taxonomy=taxonomy_content
        )
        
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        response = self.client.chat_completion(
            messages, 
            temperature=self.generation_config.get("temperature", 0.7)
        )
        
        # Parse the JSON response using robust parsing
        try:
            examples = parse_synthetic_examples(response, verbose=verbose)
            
            if verbose:
                print(f"Successfully generated {len(examples)} examples")
            
            return examples
        except ValueError as e:
            if verbose:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw response: {response}")
            raise
    
    def generate_from_seed_examples(self, seed_examples: List[Dict[str, Any]], num_examples: int = 25, verbose: bool = False) -> List[Dict[str, Any]]:
        """Generate synthetic data from seed examples"""
        if verbose:
            print(f"Generating {num_examples} examples from {len(seed_examples)} seed examples...")
        
        # Convert seed examples to JSON string
        seed_examples_json = json.dumps(seed_examples, indent=2)
        
        # Get seed examples generation prompt from config
        prompt_template = get_prompt(self.config, "seed_examples_generation")
        prompt = prompt_template.format(
            num_examples=num_examples,
            seed_examples=seed_examples_json
        )
        
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        response = self.client.chat_completion(
            messages, 
            temperature=self.generation_config.get("temperature", 0.7)
        )
        
        # Parse the JSON response using robust parsing
        try:
            examples = parse_synthetic_examples(response, verbose=verbose)
            
            if verbose:
                print(f"Successfully generated {len(examples)} examples")
            
            return examples
        except ValueError as e:
            if verbose:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw response: {response}")
            raise
    
    def process_taxonomy_file(self, taxonomy_file: str, num_examples: int = 25, verbose: bool = False) -> Dict[str, Any]:
        """Process a taxonomy file and generate synthetic data"""
        # Read taxonomy file
        try:
            with open(taxonomy_file, 'r', encoding='utf-8') as f:
                taxonomy_content = f.read()
        except Exception as e:
            raise ValueError(f"Error reading taxonomy file: {e}")
        
        # Generate examples
        examples = self.generate_from_taxonomy(taxonomy_content, num_examples, verbose)
        
        # Create result structure
        result = {
            "metadata": {
                "source_type": "taxonomy",
                "source_file": taxonomy_file,
                "num_examples": len(examples),
                "generation_config": self.generation_config
            },
            "examples": examples
        }
        
        return result
    
    def process_seed_examples_file(self, seed_file: str, num_examples: int = 25, verbose: bool = False, include_seed_examples: bool = True) -> Dict[str, Any]:
        """Process a seed examples file and generate synthetic data
        
        Args:
            seed_file: Path to the seed examples file
            num_examples: Number of examples to generate
            verbose: Whether to print verbose output
            include_seed_examples: Whether to include seed examples in the output (default: True)
        
        Returns:
            Dictionary containing metadata and examples (with or without seed examples)
        """
        # Read seed examples file
        try:
            with open(seed_file, 'r', encoding='utf-8') as f:
                seed_data = json.load(f)
        except Exception as e:
            raise ValueError(f"Error reading seed examples file: {e}")
        
        # Extract examples from different possible formats
        if isinstance(seed_data, list):
            seed_examples = seed_data
        elif isinstance(seed_data, dict):
            # Try different common keys
            if "examples" in seed_data:
                seed_examples = seed_data["examples"]
            elif "data" in seed_data:
                seed_examples = seed_data["data"]
            elif "conversations" in seed_data:
                seed_examples = seed_data["conversations"]
            else:
                raise ValueError("Could not find examples in seed file. Expected 'examples', 'data', or 'conversations' key.")
        else:
            raise ValueError("Seed file must contain a list or dictionary with examples")
        
        if not isinstance(seed_examples, list) or len(seed_examples) == 0:
            raise ValueError("No valid seed examples found in file")
        
        # Generate examples
        examples = self.generate_from_seed_examples(seed_examples, num_examples, verbose)
        
        # Create result structure based on include_seed_examples flag
        if include_seed_examples:
            result = {
                "metadata": {
                    "source_type": "seed_examples",
                    "source_file": seed_file,
                    "num_seed_examples": len(seed_examples),
                    "num_generated_examples": len(examples),
                    "generation_config": self.generation_config
                },
                "seed_examples": seed_examples,
                "examples": examples
            }
        else:
            result = {
                "metadata": {
                    "source_type": "seed_examples_generated_only",
                    "source_file": seed_file,
                    "num_seed_examples": len(seed_examples),
                    "num_generated_examples": len(examples),
                    "generation_config": self.generation_config
                },
                "examples": examples
            }
        
        return result
    
    def get_generated_examples_only(self, seed_file: str, num_examples: int = 25, verbose: bool = False) -> List[Dict[str, Any]]:
        """Get only the generated examples without seed examples or metadata
        
        Args:
            seed_file: Path to the seed examples file
            num_examples: Number of examples to generate
            verbose: Whether to print verbose output
        
        Returns:
            List of generated examples only
        """
        result = self.process_seed_examples_file(seed_file, num_examples, verbose, include_seed_examples=False)
        return result["examples"]
