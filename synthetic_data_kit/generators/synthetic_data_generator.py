# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
# Synthetic Data Generator

from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path

from synthetic_data_kit.models.llm_client import LLMClient
from synthetic_data_kit.utils.config import load_config, get_generation_config, get_prompt

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
        
        # Parse the JSON response
        try:
            examples = json.loads(response)
            if not isinstance(examples, list):
                raise ValueError("Response is not a list")
            
            if verbose:
                print(f"Successfully generated {len(examples)} examples")
            
            return examples
        except json.JSONDecodeError as e:
            if verbose:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw response: {response}")
            raise ValueError(f"Failed to parse JSON response: {e}")
    
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
        
        # Parse the JSON response
        try:
            examples = json.loads(response)
            if not isinstance(examples, list):
                raise ValueError("Response is not a list")
            
            if verbose:
                print(f"Successfully generated {len(examples)} examples")
            
            return examples
        except json.JSONDecodeError as e:
            if verbose:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw response: {response}")
            raise ValueError(f"Failed to parse JSON response: {e}")
    
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
    
    def process_seed_examples_file(self, seed_file: str, num_examples: int = 25, verbose: bool = False) -> Dict[str, Any]:
        """Process a seed examples file and generate synthetic data"""
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
        
        # Create result structure
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
        
        return result
