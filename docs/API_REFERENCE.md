# API Reference

Complete CLI command reference for the Trajectory Synthetic Data Generator.

## Table of Contents

- [Main CLI](#main-cli)
- [Ingest Commands](#ingest-commands)
- [Generation Commands](#generation-commands)
- [Transformation Commands](#transformation-commands)
- [Pipeline Commands](#pipeline-commands)
- [Utility Scripts](#utility-scripts)

---

## Main CLI
```bash
python main.py <command> [options]
```

### Global Options
```bash
--help, -h          Show help message
```

### Available Commands

| Command | Description |
|---------|-------------|
| `ingest` | Ingest a single PDF file |
| `ingest-batch` | Ingest all PDFs from a directory |
| `generate-qa` | Generate Q&A pairs from documents |
| `generate` | Generate multi-iteration trajectories |
| `transform` | Transform queries (30× expansion) |
| `pipeline` | Run complete generation pipeline |
| `stats` | Show system statistics |

---

## Ingest Commands

### ingest

Ingest a single PDF file into VectorDB.
```bash
python main.py ingest <pdf_file> [options]
```

**Arguments:**
- `pdf_file`: Path to PDF file

**Options:**
- `--no-vision`: Disable vision analysis for images

**Examples:**
```bash
# Basic ingestion
python main.py ingest data/pdfs/document.pdf

# Without vision analysis
python main.py ingest data/pdfs/document.pdf --no-vision
```

**Output:**
```
🔄 Ingesting PDF: document.pdf
✅ Parsed 25 pages into 75 chunks
✅ Ingested 75 chunks from document.pdf
Total documents in vector store: 150
```

---

### ingest-batch

Ingest all PDFs from a directory.
```bash
python main.py ingest-batch <pdf_dir> [options]
```

**Arguments:**
- `pdf_dir`: Directory containing PDF files

**Options:**
- `--no-vision`: Disable vision analysis
- `--skip-errors`: Continue on errors instead of stopping

**Examples:**
```bash
# Ingest all PDFs
python main.py ingest-batch data/pdfs/

# Skip problematic PDFs
python main.py ingest-batch data/pdfs/ --skip-errors

# Without vision
python main.py ingest-batch data/pdfs/ --no-vision
```

**Output:**
```
============================================================
BATCH PDF INGESTION
============================================================
Found 5 PDF files in data/pdfs
============================================================

[1/5] Processing: doc1.pdf
  ✅ 45 chunks added

[2/5] Processing: doc2.pdf
  ✅ 67 chunks added

...

============================================================
BATCH INGESTION SUMMARY
============================================================
Total PDFs found: 5
Successfully processed: 5
Failed: 0
Total chunks added: 245
Total documents in VectorDB: 245
============================================================
```

---

## Generation Commands

### generate-qa

Generate Q&A pairs from ingested documents.
```bash
python main.py generate-qa [options]
```

**Options:**
- `--limit <n>`: Number of Q&A pairs to generate (default: 50)
- `--complexity <level>`: Question complexity (choices: simple, medium, complex, all; default: all)
- `--output <file>`: Output file path (default: samples/generated_qa.jsonl)

**Examples:**
```bash
# Generate 50 Q&A pairs (all complexities)
python main.py generate-qa --limit 50

# Generate only simple questions
python main.py generate-qa --limit 20 --complexity simple --output samples/qa_simple.jsonl

# Generate complex questions
python main.py generate-qa --limit 30 --complexity complex --output samples/qa_complex.jsonl
```

**Output Format:**
```json
{
  "question": "What are the key benefits of portfolio diversification?",
  "answer": "Portfolio diversification provides several benefits...",
  "complexity": "medium",
  "source_chunks": ["chunk_id_1", "chunk_id_2"]
}
```

---

### generate

Generate multi-iteration trajectories from queries.
```bash
python main.py generate <queries_file> [options]
```

**Arguments:**
- `queries_file`: JSON or JSONL file with queries

**Options:**
- `--output <file>`: Output file path (default: samples/trajectories.jsonl)
- `--max-iterations <n>`: Maximum iterations per trajectory (default: 3)

**Input Format (JSON):**
```json
{
  "queries": [
    "How should I allocate my portfolio?",
    "What are the tax implications?"
  ]
}
```

**Input Format (JSONL - from transformations):**
```json
{"transformed_query": "I'm new to investing - how should I split my money?", "persona": "P1", ...}
{"transformed_query": "What's the optimal allocation strategy?", "persona": "P2", ...}
```

**Examples:**
```bash
# Generate from simple queries
python main.py generate data/seed/queries.json --output samples/traj.jsonl

# Generate with max 5 iterations
python main.py generate transformed.jsonl --output samples/traj.jsonl --max-iterations 5

# Generate from transformed queries
python main.py generate samples/transformed.jsonl --output samples/trajectories.jsonl
```

**Output Format:**
```json
{
  "Q": "How should I optimize my portfolio?",
  "COT": "The user needs portfolio optimization...",
  "Tool Set": [{"name": "analyze_portfolio_risk", ...}],
  "Decision": "CALL",
  "metadata": {"iteration": 0, "decision_type": "CALL"}
}
```

---

## Transformation Commands

### transform

Transform queries with 30× expansion.
```bash
python main.py transform <queries_file> [options]
```

**Arguments:**
- `queries_file`: JSON file with seed queries

**Options:**
- `--output <file>`: Output file path (default: samples/transformed_queries.jsonl)
- `--persona <P>`: Specific persona or 'all' (choices: P1, P2, P3, P4, P5, all; default: all)
- `--complexity <C>`: Specific complexity or 'all' (choices: Q-, Q, Q+, all; default: all)

**Examples:**
```bash
# Full 30× transformation
python main.py transform data/seed/queries.json --output samples/transformed.jsonl

# Only P1 persona
python main.py transform queries.json --persona P1 --output samples/p1_only.jsonl

# Only complex queries
python main.py transform queries.json --complexity Q+ --output samples/complex_only.jsonl

# Specific persona + complexity
python main.py transform queries.json --persona P3 --complexity Q+ --output samples/p3_complex.jsonl
```

**Output Format:**
```json
{
  "seed_query": "How should I diversify my portfolio?",
  "seed_id": 1,
  "persona": "P1",
  "persona_name": "First-time Investor",
  "complexity": "Q-",
  "complexity_name": "Simplified",
  "transformed_query": "I'm new to investing - how do I spread my money?",
  "tool_variant": "correct",
  "tool_variant_description": "Normal tool execution with valid data"
}
```

**Expansion:**
- 5 personas × 3 complexity × 2 tool variants = **30× per seed**
- With filters: Subset of 30×

---

## Pipeline Commands

### pipeline

Run complete generation pipeline.
```bash
python main.py pipeline <queries_file> [options]
```

**Arguments:**
- `queries_file`: JSON file with seed queries

**Options:**
- `--output-dir <dir>`: Output directory (default: data/output)
- `--skip-transform`: Skip transformation step (use queries as-is)
- `--max-iterations <n>`: Maximum trajectory iterations (default: 3)

**Examples:**
```bash
# Full pipeline
python main.py pipeline data/seed/queries.json --output-dir samples/pipeline_output/

# Skip transformations (direct trajectory generation)
python main.py pipeline queries.json --skip-transform --output-dir samples/direct/

# Custom iterations
python main.py pipeline queries.json --max-iterations 5 --output-dir samples/iter5/
```

**Output Files:**
```
samples/pipeline_output/
├── transformed_queries.jsonl  # 30× expanded queries
└── trajectories.jsonl         # Final training examples
```

**Pipeline Flow:**
```
queries.json
    ↓
Transform (30×)
    ↓
transformed_queries.jsonl
    ↓
Generate Trajectories
    ↓
trajectories.jsonl
```

---

### stats

Show system statistics.
```bash
python main.py stats
```

**No arguments required.**

**Output:**
```
============================================================
📊 SYSTEM STATISTICS
============================================================

📦 Vector Store:
  Collection: document_chunks
  Documents: 291
  Distance metric: cosine

⚙️  Configuration:
  Model: anthropic.claude-sonnet-4-20250514-v1:0
  Embedding: amazon.titan-embed-text-v2:0
  Region: us-east-1
  Output format: jsonl
  Max tokens: 64000

📄 Output Files (10):
  - trajectories.jsonl (125.3 KB, 150 records)
  - transformed.jsonl (89.2 KB, 300 records)
  ...

============================================================
```

---

## Utility Scripts

### Complete Pipeline Script
```bash
./scripts/complete_pipeline_with_ingest.sh [pdf_dir] [num_qa_pairs]
```

**Arguments:**
- `pdf_dir`: PDF directory (default: data/pdfs)
- `num_qa_pairs`: Number of Q&A pairs (default: 20)

**Example:**
```bash
# Default (data/pdfs, 20 Q&A)
./scripts/complete_pipeline_with_ingest.sh

# Custom
./scripts/complete_pipeline_with_ingest.sh /path/to/pdfs 50
```

**Output:**
```
samples/pipeline_TIMESTAMP/
├── 01_qa.jsonl
├── 02_queries.json
├── 03_transformed.jsonl
└── 04_trajectories.jsonl
```

---

### Validation Scripts

#### validate_format.py
```bash
python scripts/validate_format.py <file.jsonl>
```

Validates training data format.

**Example:**
```bash
python scripts/validate_format.py samples/trajectories.jsonl
```

#### analyze_quality.py
```bash
python scripts/analyze_quality.py <file.jsonl>
```

Analyzes quality metrics.

**Example:**
```bash
python scripts/analyze_quality.py samples/trajectories.jsonl
```

#### check_diversity.py
```bash
python scripts/check_diversity.py <file.jsonl>
```

Checks query diversity.

**Example:**
```bash
python scripts/check_diversity.py samples/transformed.jsonl
```

#### summarize_dataset.py
```bash
python scripts/summarize_dataset.py
```

Generates comprehensive dataset summary.

**Example:**
```bash
python scripts/summarize_dataset.py
```

---

## Configuration Files

### config/config.yaml

Main configuration file.

**Key sections:**
- `bedrock`: AWS Bedrock settings
- `pdf_processing`: PDF parsing configuration
- `chromadb`: Vector database settings
- `output`: Output format configuration

### config/tools.json

Tool definitions for trajectory generation.

**Format:**
```json
{
  "name": "tool_name",
  "description": "Tool description",
  "parameters": {
    "type": "object",
    "properties": {...},
    "required": [...]
  }
}
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid arguments, file not found, etc.) |

---

## Tips & Best Practices

### 1. Start Small
```bash
# Test with small datasets first
python main.py generate-qa --limit 5
python main.py transform small_queries.json
```

### 2. Use Pipeline for Production
```bash
# Pipeline handles everything
./scripts/complete_pipeline_with_ingest.sh data/pdfs 50
```

### 3. Validate Before Using
```bash
# Always validate generated data
python scripts/validate_format.py output.jsonl
python scripts/analyze_quality.py output.jsonl
```

### 4. Monitor Progress
- Progress bars show real-time status
- Check logs in `logs/` for details

### 5. Incremental Processing
```bash
# Process in stages for debugging
python main.py transform queries.json --output step1.jsonl
python main.py generate step1.jsonl --output step2.jsonl
```

---

*For examples, see [EXAMPLES.md](EXAMPLES.md)*
