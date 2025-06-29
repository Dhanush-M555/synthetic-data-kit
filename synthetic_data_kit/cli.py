# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
# CLI Logic for synthetic-data-kit

import os
import json
import typer
from pathlib import Path
from typing import Optional
import requests
from rich.console import Console
from rich.table import Table

from synthetic_data_kit.utils.config import load_config, get_vllm_config, get_openai_config, get_llm_provider, get_path_config
from synthetic_data_kit.core.context import AppContext
from synthetic_data_kit.server.app import run_server

# Initialize Typer app
app = typer.Typer(
    name="synthetic-data-kit",
    help="A toolkit for preparing synthetic datasets for fine-tuning LLMs",
    add_completion=True,
)
console = Console()

# Create app context
ctx = AppContext()

# Define global options
@app.callback()
def callback(
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
):
    """
    Global options for the Synthetic Data Kit CLI
    """
    if config:
        ctx.config_path = config
    ctx.config = load_config(ctx.config_path)


@app.command("system-check")
def system_check(
    api_base: Optional[str] = typer.Option(
        None, "--api-base", help="API base URL to check"
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", help="Provider to check ('vllm' or 'api-endpoint')"
    )
):
    """
    Check if the selected LLM provider's server is running.
    """
    # Check for API_ENDPOINT_KEY directly from environment
    console.print("Environment variable check:", style="bold blue")
    llama_key = os.environ.get('API_ENDPOINT_KEY')
    console.print(f"API_ENDPOINT_KEY: {'Present' if llama_key else 'Not found'}")
    # Debugging sanity test:
    # if llama_key:
        # console.print(f"  Value starts with: {llama_key[:10]}...")
    
    # To check the rename bug:
    #console.print("Available environment variables:", style="bold blue")
    #env_vars = [key for key in os.environ.keys() if 'API' in key or 'KEY' in key or 'TOKEN' in key]
    #for var in env_vars:
    #    console.print(f"  {var}")
    #console.print("")
    # Get provider from args or config
    selected_provider = provider or get_llm_provider(ctx.config)
    
    if selected_provider == "api-endpoint":
        # Get API endpoint config
        api_endpoint_config = get_openai_config(ctx.config)
        api_base = api_base or api_endpoint_config.get("api_base")
        
        # Check for environment variables
        api_endpoint_key = os.environ.get('API_ENDPOINT_KEY')
        console.print(f"API_ENDPOINT_KEY environment variable: {'Found' if api_endpoint_key else 'Not found'}")
        
        # Set API key with priority: env var > config
        api_key = api_endpoint_key or api_endpoint_config.get("api_key")
        if api_key:
            console.print(f"API key source: {'Environment variable' if api_endpoint_key else 'Config file'}")
        
        model = api_endpoint_config.get("model")
        
        # Check API endpoint access
        with console.status(f"Checking API endpoint access..."):
            try:
                # Try to import OpenAI
                try:
                    from openai import OpenAI
                except ImportError:
                    console.print("L API endpoint package not installed", style="red")
                    console.print("Install with: pip install openai>=1.0.0", style="yellow")
                    return 1
                
                # Create client
                client_kwargs = {}
                if api_key:
                    client_kwargs['api_key'] = api_key
                if api_base:
                    client_kwargs['base_url'] = api_base
                
                # Check API access
                try:
                    client = OpenAI(**client_kwargs)
                    # Try a simple models list request to check connectivity
                    models = client.models.list()
                    console.print(f" API endpoint access confirmed", style="green")
                    if api_base:
                        console.print(f"Using custom API base: {api_base}", style="green")
                    console.print(f"Default model: {model}", style="green")
                    return 0
                except Exception as e:
                    console.print(f"L Error connecting to API endpoint: {str(e)}", style="red")
                    if api_base:
                        console.print(f"Using custom API base: {api_base}", style="yellow")
                    if not api_key and not api_base:
                        console.print("API key is required. Set in config.yaml or as API_ENDPOINT_KEY env var", style="yellow")
                    return 1
            except Exception as e:
                console.print(f"L Error: {str(e)}", style="red")
                return 1
    else:
        # Default to vLLM
        # Get vLLM server details
        vllm_config = get_vllm_config(ctx.config)
        api_base = api_base or vllm_config.get("api_base")
        model = vllm_config.get("model")
        port = vllm_config.get("port", 8000)
        
        with console.status(f"Checking vLLM server at {api_base}..."):
            try:
                response = requests.get(f"{api_base}/models", timeout=2)
                if response.status_code == 200:
                    console.print(f" vLLM server is running at {api_base}", style="green")
                    console.print(f"Available models: {response.json()}")
                    return 0
                else:
                    console.print(f"L vLLM server is not available at {api_base}", style="red")
                    console.print(f"Error: Server returned status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                console.print(f"L vLLM server is not available at {api_base}", style="red")
                console.print(f"Error: {str(e)}")
                
            # Show instruction to start the server
            console.print("\nTo start the server, run:", style="yellow")
            console.print(f"vllm serve {model} --port {port}", style="bold blue")
            return 1


@app.command()
def ingest(
    input: str = typer.Argument(..., help="File or URL to parse"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-o", help="Where to save the output"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Custom output filename"
    ),
):
    """
    Parse documents (PDF, HTML, YouTube, DOCX, PPT, TXT) into clean text.
    """
    from synthetic_data_kit.core.ingest import process_file
    
    # Get output directory from args, then config, then default
    if output_dir is None:
        output_dir = get_path_config(ctx.config, "output", "parsed")
    
    try:
        with console.status(f"Processing {input}..."):
            output_path = process_file(input, output_dir, name, ctx.config)
        console.print(f" Text successfully extracted to [bold]{output_path}[/bold]", style="green")
        return 0
    except Exception as e:
        console.print(f"L Error: {e}", style="red")
        return 1


@app.command()
def create(
    input: str = typer.Argument(..., help="File to process"),
    content_type: str = typer.Option(
        "qa", "--type", help="Type of content to generate [qa|summary|cot|cot-enhance]"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-o", help="Where to save the output"
    ),
    api_base: Optional[str] = typer.Option(
        None, "--api-base", help="VLLM API base URL"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use"
    ),
    num_pairs: Optional[int] = typer.Option(
        None, "--num-pairs", "-n", help="Target number of QA pairs to generate"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"
    ),
):
    """
    Generate content from text using local LLM inference.
    
    Content types:
    - qa: Generate question-answer pairs from text
    - summary: Generate a summary of the text
    - cot: Generate Chain of Thought reasoning examples from text
    - cot-enhance: Enhance existing tool-use conversations with Chain of Thought reasoning
      (for cot-enhance, the input must be a JSON file with either:
       - A single conversation in 'conversations' field
       - An array of conversation objects, each with a 'conversations' field
       - A direct array of conversation messages)
    """
    from synthetic_data_kit.core.create import process_file
    
    # Check the LLM provider from config
    provider = get_llm_provider(ctx.config)
    console.print(f"L Using {provider} provider", style="green")
    if provider == "api-endpoint":
        # Use API endpoint config
        api_endpoint_config = get_openai_config(ctx.config)
        api_base = api_base or api_endpoint_config.get("api_base")
        model = model or api_endpoint_config.get("model")
        # No server check needed for API endpoint
    else:
        # Use vLLM config
        vllm_config = get_vllm_config(ctx.config)
        api_base = api_base or vllm_config.get("api_base")
        model = model or vllm_config.get("model")
        
        # Check vLLM server availability
        try:
            response = requests.get(f"{api_base}/models", timeout=2)
            if response.status_code != 200:
                console.print(f"L Error: VLLM server not available at {api_base}", style="red")
                console.print("Please start the VLLM server with:", style="yellow")
                console.print(f"vllm serve {model}", style="bold blue")
                return 1
        except requests.exceptions.RequestException:
            console.print(f"L Error: VLLM server not available at {api_base}", style="red")
            console.print("Please start the VLLM server with:", style="yellow")
            console.print(f"vllm serve {model}", style="bold blue")
            return 1
    
    # Get output directory from args, then config, then default
    if output_dir is None:
        output_dir = get_path_config(ctx.config, "output", "generated")
    
    try:
        with console.status(f"Generating {content_type} content from {input}..."):
            output_path = process_file(
                input,
                output_dir,
                ctx.config_path,
                api_base,
                model,
                content_type,
                num_pairs,
                verbose,
                provider=provider  # Pass the provider parameter
            )
        if output_path:
            console.print(f" Content saved to [bold]{output_path}[/bold]", style="green")
        return 0
    except Exception as e:
        console.print(f"L Error: {e}", style="red")
        return 1


@app.command("curate")
def curate(
    input: str = typer.Argument(..., help="Input file to clean"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
    threshold: Optional[float] = typer.Option(
        None, "--threshold", "-t", help="Quality threshold (1-10)"
    ),
    api_base: Optional[str] = typer.Option(
        None, "--api-base", help="VLLM API base URL"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"
    ),
):
    """
    Clean and filter content based on quality.
    """
    from synthetic_data_kit.core.curate import curate_qa_pairs
    
    # Check the LLM provider from config
    provider = get_llm_provider(ctx.config)
    
    if provider == "api-endpoint":
        # Use API endpoint config
        api_endpoint_config = get_openai_config(ctx.config)
        api_base = api_base or api_endpoint_config.get("api_base")
        model = model or api_endpoint_config.get("model")
        # No server check needed for API endpoint
    else:
        # Use vLLM config
        vllm_config = get_vllm_config(ctx.config)
        api_base = api_base or vllm_config.get("api_base")
        model = model or vllm_config.get("model")
        
        # Check vLLM server availability
        try:
            response = requests.get(f"{api_base}/models", timeout=2)
            if response.status_code != 200:
                console.print(f"L Error: VLLM server not available at {api_base}", style="red")
                console.print("Please start the VLLM server with:", style="yellow")
                console.print(f"vllm serve {model}", style="bold blue")
                return 1
        except requests.exceptions.RequestException:
            console.print(f"L Error: VLLM server not available at {api_base}", style="red")
            console.print("Please start the VLLM server with:", style="yellow")
            console.print(f"vllm serve {model}", style="bold blue")
            return 1
    
    # Get default output path from config if not provided
    if not output:
        cleaned_dir = get_path_config(ctx.config, "output", "cleaned")
        os.makedirs(cleaned_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input))[0]
        output = os.path.join(cleaned_dir, f"{base_name}_cleaned.json")
    
    try:
        with console.status(f"Cleaning content from {input}..."):
            result_path = curate_qa_pairs(
                input,
                output,
                threshold,
                api_base,
                model,
                ctx.config_path,
                verbose,
                provider=provider  # Pass the provider parameter
            )
        console.print(f" Cleaned content saved to [bold]{result_path}[/bold]", style="green")
        return 0
    except Exception as e:
        console.print(f"L Error: {e}", style="red")
        return 1


@app.command("save-as")
def save_as(
    input: str = typer.Argument(..., help="Input file to convert"),
    format: Optional[str] = typer.Option(
        None, "--format", "-f", help="Output format [jsonl|alpaca|ft|chatml]"
    ),
    storage: str = typer.Option(
        "json", "--storage", help="Storage format [json|hf]",
        show_default=True
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """
    Convert to different formats for fine-tuning.
    
    The --format option controls the content format (how the data is structured).
    The --storage option controls how the data is stored (JSON file or HF dataset).
    
    When using --storage hf, the output will be a directory containing a Hugging Face 
    dataset in Arrow format, which is optimized for machine learning workflows.
    """
    from synthetic_data_kit.core.save_as import convert_format
    
    # Get format from args or config
    if not format:
        format_config = ctx.config.get("format", {})
        format = format_config.get("default", "jsonl")
    
    # Set default output path if not provided
    if not output:
        final_dir = get_path_config(ctx.config, "output", "final")
        os.makedirs(final_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input))[0]
        
        if storage == "hf":
            # For HF datasets, use a directory name
            output = os.path.join(final_dir, f"{base_name}_{format}_hf")
        else:
            # For JSON files, use appropriate extension
            if format == "jsonl":
                output = os.path.join(final_dir, f"{base_name}.jsonl")
            else:
                output = os.path.join(final_dir, f"{base_name}_{format}.json")
    
    try:
        with console.status(f"Converting {input} to {format} format with {storage} storage..."):
            output_path = convert_format(
                input,
                output,
                format,
                ctx.config,
                storage_format=storage
            )
        
        if storage == "hf":
            console.print(f" Converted to {format} format and saved as HF dataset to [bold]{output_path}[/bold]", style="green")
        else:
            console.print(f" Converted to {format} format and saved to [bold]{output_path}[/bold]", style="green")
        return 0
    except Exception as e:
        console.print(f"L Error: {e}", style="red")
        return 1


@app.command("server")
def server(
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host address to bind the server to"
    ),
    port: int = typer.Option(
        5000, "--port", "-p", help="Port to run the server on"
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Run the server in debug mode"
    ),
):
    """
    Start a web interface for the Synthetic Data Kit.
    
    This launches a web server that provides a UI for all SDK functionality,
    including generating and curating QA pairs, as well as viewing
    and managing generated files.
    """
    provider = get_llm_provider(ctx.config)
    console.print(f"Starting web server with {provider} provider...", style="green")
    console.print(f"Web interface available at: http://{host}:{port}", style="bold green")
    console.print("Press CTRL+C to stop the server.", style="italic")
    
    # Run the Flask server
    run_server(host=host, port=port, debug=debug)


@app.command()
def generate(
    taxonomy: Optional[str] = typer.Option(
        None, "--taxonomy", help="Path to taxonomy file (.md or .txt) for taxonomy-based generation"
    ),
    seed_examples: Optional[str] = typer.Option(
        None, "--seed-examples", help="Path to seed examples file (.json) for example-based generation"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-o", help="Where to save the output"
    ),
    api_base: Optional[str] = typer.Option(
        None, "--api-base", help="LLM API base URL"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use"
    ),
    num_examples: Optional[int] = typer.Option(
        None, "--num-examples", "-n", help="Number of examples to generate"
    ),
    examples_only: bool = typer.Option(
        False, "--examples-only", help="Save only generated examples without seed examples or full metadata (seed-examples mode only)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"
    ),
):
    """
    Generate synthetic datasets from scratch using taxonomies or seed examples.
    
    This command allows you to create datasets without needing source documents.
    You can use either:
    
    1. Taxonomy-based generation: Provide a taxonomy structure in markdown/text format
    2. Seed examples-based generation: Provide a few example data points in JSON format
    
    Examples:
    
    # Generate from taxonomy
    synthetic-data-kit generate --taxonomy outline.md -n 50
    
    # Generate from seed examples  
    synthetic-data-kit generate --seed-examples examples.json -n 100
    
    # Generate only the examples without seed data or metadata
    synthetic-data-kit generate --seed-examples examples.json -n 50 --examples-only
    """
    from synthetic_data_kit.core.generate import process_generate_request
    
    # Validate that exactly one input type is provided
    if not taxonomy and not seed_examples:
        console.print("L Error: You must specify either --taxonomy or --seed-examples", style="red")
        console.print("Use --help for more information", style="yellow")
        return 1
    
    if taxonomy and seed_examples:
        console.print("L Error: You cannot specify both --taxonomy and --seed-examples", style="red")
        console.print("Use --help for more information", style="yellow")
        return 1
    
    # Determine generation type and input file
    if taxonomy:
        generation_type = "taxonomy"
        input_file = taxonomy
    else:
        generation_type = "seed-examples"
        input_file = seed_examples
    
    # Check the LLM provider from config
    provider = get_llm_provider(ctx.config)
    console.print(f"L Using {provider} provider", style="green")
    
    if provider == "api-endpoint":
        # Use API endpoint config
        api_endpoint_config = get_openai_config(ctx.config)
        api_base = api_base or api_endpoint_config.get("api_base")
        model = model or api_endpoint_config.get("model")
        # No server check needed for API endpoint
    else:
        # Use vLLM config
        vllm_config = get_vllm_config(ctx.config)
        api_base = api_base or vllm_config.get("api_base")
        model = model or vllm_config.get("model")
        
        # Check vLLM server availability
        try:
            response = requests.get(f"{api_base}/models", timeout=2)
            if response.status_code != 200:
                console.print(f"L Error: VLLM server not available at {api_base}", style="red")
                console.print("Please start the VLLM server with:", style="yellow")
                console.print(f"vllm serve {model}", style="bold blue")
                return 1
        except requests.exceptions.RequestException:
            console.print(f"L Error: VLLM server not available at {api_base}", style="red")
            console.print("Please start the VLLM server with:", style="yellow")
            console.print(f"vllm serve {model}", style="bold blue")
            return 1
    
    # Get output directory from args, then config, then default
    if output_dir is None:
        output_dir = get_path_config(ctx.config, "output", "generated")
    
    try:
        generation_desc = "taxonomy structure" if generation_type == "taxonomy" else "seed examples"
        with console.status(f"Generating synthetic data from {generation_desc}..."):
            output_path = process_generate_request(
                input_file,
                output_dir,
                ctx.config_path,
                api_base,
                model,
                generation_type,
                num_examples,
                verbose,
                provider=provider,
                examples_only=examples_only
            )
        console.print(f" Synthetic data saved to [bold]{output_path}[/bold]", style="green")
        return 0
    except Exception as e:
        console.print(f"L Error: {e}", style="red")
        return 1


@app.command("curate-seed")
def curate_seed(
    input: str = typer.Argument(..., help="Input file with seed-generated examples to clean"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
    threshold: Optional[float] = typer.Option(
        None, "--threshold", "-t", help="Quality threshold (1-10)"
    ),
    api_base: Optional[str] = typer.Option(
        None, "--api-base", help="VLLM API base URL"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"
    ),
):
    """
    Clean and filter seed-generated examples based on quality.
    """
    from synthetic_data_kit.core.curate import curate_seed_examples
    
    # Check the LLM provider from config
    provider = get_llm_provider(ctx.config)
    
    if provider == "api-endpoint":
        # Use API endpoint config
        api_endpoint_config = get_openai_config(ctx.config)
        api_base = api_base or api_endpoint_config.get("api_base")
        model = model or api_endpoint_config.get("model")
        # No server check needed for API endpoint
    else:
        # Use vLLM config
        vllm_config = get_vllm_config(ctx.config)
        api_base = api_base or vllm_config.get("api_base")
        model = model or vllm_config.get("model")
        
        # Check vLLM server availability
        try:
            response = requests.get(f"{api_base}/models", timeout=2)
            if response.status_code != 200:
                console.print(f"L Error: VLLM server not available at {api_base}", style="red")
                console.print("Please start the VLLM server with:", style="yellow")
                console.print(f"vllm serve {model}", style="bold blue")
                return 1
        except requests.exceptions.RequestException:
            console.print(f"L Error: VLLM server not available at {api_base}", style="red")
            console.print("Please start the VLLM server with:", style="yellow")
            console.print(f"vllm serve {model}", style="bold blue")
            return 1
    
    # Get default output path from config if not provided
    if not output:
        cleaned_dir = get_path_config(ctx.config, "output", "cleaned")
        os.makedirs(cleaned_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input))[0]
        output = os.path.join(cleaned_dir, f"{base_name}_cleaned.json")
    
    try:
        with console.status(f"Cleaning seed examples from {input}..."):
            result_path = curate_seed_examples(
                input,
                output,
                threshold,
                api_base,
                model,
                ctx.config_path,
                verbose,
                provider=provider  # Pass the provider parameter
            )
        console.print(f" Cleaned seed examples saved to [bold]{result_path}[/bold]", style="green")
        return 0
    except Exception as e:
        console.print(f"L Error: {e}", style="red")
        return 1


def main():
    """Entry point for the synthetic-data-kit CLI."""
    app()


if __name__ == "__main__":
    app()
