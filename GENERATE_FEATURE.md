# Generate Command - Synthetic Dataset Generation

## Overview

The `generate` command allows you to create synthetic datasets from scratch without needing source documents. This is useful for creating training data for specific tasks like OCR-to-JSON conversion, following structured patterns, or expanding existing datasets.

## Usage

```bash
# Generate from taxonomy structure
synthetic-data-kit generate --taxonomy outline.md -n 50

# Generate from seed examples  
synthetic-data-kit generate --seed-examples examples.json -n 100
```

## Two Generation Approaches

### 1. Taxonomy-Based Generation (`--taxonomy`)

Use this approach when you have a structured outline or specification of what kind of data you want to generate.

**Input**: Markdown or text file describing the taxonomy/structure
**Example**: `examples/ocr_taxonomy.md`

```bash
synthetic-data-kit generate --taxonomy examples/ocr_taxonomy.md --num-examples 25
```

### 2. Seed Examples-Based Generation (`--seed-examples`)

Use this approach when you have a few examples of the desired output format and want to generate more similar data.

**Input**: JSON file containing example data points
**Example**: `examples/ocr_seed_examples.json`

```bash
synthetic-data-kit generate --seed-examples examples/ocr_seed_examples.json --num-examples 50
```

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--taxonomy` | Path to taxonomy file (.md or .txt) | None |
| `--seed-examples` | Path to seed examples file (.json) | None |
| `--output-dir, -o` | Output directory | `data/generated` |
| `--api-base` | LLM API base URL | From config |
| `--model, -m` | Model to use | From config |
| `--num-examples, -n` | Number of examples to generate | 25 |
| `--verbose, -v` | Show detailed output | False |

## Output Format

The command generates a JSON file with the following structure:

```json
{
  "metadata": {
    "source_type": "taxonomy" | "seed_examples",
    "source_file": "path/to/input/file",
    "num_examples": 25,
    "generation_config": {...}
  },
  "examples": [
    {
      "instruction": "Task instruction",
      "input": "Input data (if applicable)",
      "output": "Expected output"
    }
  ]
}
```

## Use Cases

### OCR-to-JSON Training Data
Perfect for your use case! Generate training data for converting messy OCR text to structured JSON.

### Domain-Specific Datasets
Create datasets for specific domains like legal documents, medical records, or financial data.

### Few-Shot Learning
Generate additional examples when you only have a few seed examples.

### Data Augmentation
Expand existing small datasets with synthetic variations.

## Integration with Existing Pipeline

The generated data can be used with other SDK commands:

```bash
# Generate synthetic data
synthetic-data-kit generate --taxonomy my_taxonomy.md -n 100

# Curate the generated examples
synthetic-data-kit curate data/generated/my_taxonomy_taxonomy_generated.json -t 7.5

# Convert to fine-tuning format
synthetic-data-kit save-as data/cleaned/my_taxonomy_cleaned.json -f ft
```

## Configuration

The command uses the same LLM configuration as other SDK commands. You can use Groq API by setting:

```yaml
llm:
  provider: "api-endpoint"

api-endpoint:
  api_base: "https://api.groq.com/openai/v1"
  api_key: "your-groq-key"  # Or use API_ENDPOINT_KEY env var
  model: "mixtral-8x7b-32768"
```

## Tips for Best Results

1. **Taxonomy Files**: Be specific about the desired output format and include examples
2. **Seed Examples**: Provide diverse, high-quality examples that represent the full range of desired outputs
3. **Number of Examples**: Start with smaller numbers to test, then scale up
4. **Model Selection**: Use capable models like Mixtral or GPT-4 for complex generation tasks
