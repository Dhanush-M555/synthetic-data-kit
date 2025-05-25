# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
# Logic for generating synthetic datasets

import os
import json
from pathlib import Path
from typing import Optional

from synthetic_data_kit.models.llm_client import LLMClient
from synthetic_data_kit.generators.synthetic_data_generator import SyntheticDataGenerator
from synthetic_data_kit.utils.config import get_generation_config

def process_generate_request(
    input_file: str,
    output_dir: str,
    config_path: Optional[Path] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
    generation_type: str = "taxonomy",  # "taxonomy" or "seed-examples"
    num_examples: Optional[int] = None,
    verbose: bool = False,
    provider: Optional[str] = None,
    examples_only: bool = False,  # New parameter to save only generated examples
) -> str:
    """
    Generate synthetic dataset from taxonomy or seed examples
    
    Args:
        input_file: Path to taxonomy file (.md) or seed examples file (.json)
        output_dir: Directory to save generated data
        config_path: Path to configuration file
        api_base: API base URL for LLM client
        model: Model name to use
        generation_type: Type of generation ("taxonomy" or "seed-examples")
        num_examples: Number of examples to generate
        verbose: Enable verbose output
        provider: LLM provider to use
        examples_only: If True, save only generated examples without seed examples or metadata (only applies to seed-examples)
        
    Returns:
        Path to the generated output file
    """
    # Validate input file exists
    if not os.path.exists(input_file):
        raise ValueError(f"Input file not found: {input_file}")
    
    # Validate generation type
    if generation_type not in ["taxonomy", "seed-examples"]:
        raise ValueError(f"Invalid generation type: {generation_type}. Must be 'taxonomy' or 'seed-examples'")
    
    # Validate file extension based on generation type
    input_path = Path(input_file)
    if generation_type == "taxonomy" and input_path.suffix.lower() not in ['.md', '.txt']:
        raise ValueError(f"Taxonomy files must be .md or .txt files, got: {input_path.suffix}")
    elif generation_type == "seed-examples" and input_path.suffix.lower() != '.json':
        raise ValueError(f"Seed examples files must be .json files, got: {input_path.suffix}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize LLM client
    client = LLMClient(
        config_path=config_path,
        provider=provider,
        api_base=api_base,
        model_name=model
    )
    
    # Get default num_examples if not provided
    if num_examples is None:
        config = client.config
        generation_config = get_generation_config(config)
        num_examples = generation_config.get("num_pairs", 25)  # Reuse num_pairs config
    
    # Initialize synthetic data generator
    generator = SyntheticDataGenerator(client, config_path)
    
    # Generate data based on type
    if generation_type == "taxonomy":
        result = generator.process_taxonomy_file(input_file, num_examples, verbose)
        output_suffix = "taxonomy_generated"
    else:  # seed-examples
        if examples_only:
            # Get only the generated examples
            examples = generator.get_generated_examples_only(input_file, num_examples, verbose)
            result = examples  # Just the list of examples
            output_suffix = "generated_only"
        else:
            # Get full result with seed examples and metadata
            result = generator.process_seed_examples_file(input_file, num_examples, verbose, include_seed_examples=True)
            output_suffix = "seed_generated"
    
    # Create output filename
    base_name = input_path.stem
    output_filename = f"{base_name}_{output_suffix}.json"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save result
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)  # ensure_ascii=False to handle Unicode properly
    
    if verbose:
        if isinstance(result, list):
            print(f"Generated {len(result)} examples (examples only)")
        else:
            print(f"Generated {len(result['examples'])} examples")
        print(f"Output saved to: {output_path}")
    
    return output_path
