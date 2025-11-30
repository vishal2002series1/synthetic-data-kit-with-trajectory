# System Architecture

## Overview

The Trajectory Synthetic Data Generator is a multi-stage pipeline that transforms a small set of seed queries into thousands of high-quality training examples for Small Language Models (SLMs).

## High-Level Design
```
┌─────────────────────────────────────────────────────────────┐
│                    COMPONENT LAYERS                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              CLI LAYER (main.py)                   │    │
│  │  Commands: ingest, generate-qa, transform,         │    │
│  │            generate, pipeline, stats               │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────┴─────────────────────────────┐    │
│  │           ORCHESTRATION LAYER                      │    │
│  │  • Pipeline management                             │    │
│  │  • Workflow coordination                           │    │
│  │  • Progress tracking                               │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────┴─────────────────────────────┐    │
│  │            CORE COMPONENTS                         │    │
│  │                                                     │    │
│  │  ┌─────────────────┐  ┌─────────────────┐        │    │
│  │  │  BedrockProvider│  │   VectorStore   │        │    │
│  │  │  (AWS Claude)   │  │   (ChromaDB)    │        │    │
│  │  └─────────────────┘  └─────────────────┘        │    │
│  │                                                     │    │
│  │  ┌─────────────────┐  ┌─────────────────┐        │    │
│  │  │   PDFParser     │  │  QAGenerator    │        │    │
│  │  │  (Multi-modal)  │  │  (Doc-based)    │        │    │
│  │  └─────────────────┘  └─────────────────┘        │    │
│  └─────────────────────────────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────┴─────────────────────────────┐    │
│  │          TRANSFORMATION LAYER                      │    │
│  │                                                     │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  PersonaTransformer (5 personas)            │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  QueryModifier (3 complexity levels)        │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  ToolDataTransformer (2 variants)           │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────┴─────────────────────────────┐    │
│  │          GENERATION LAYER                          │    │
│  │                                                     │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  DecisionEngine (CALL/ASK/ANSWER logic)     │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  TrajectoryGeneratorMultiIter               │  │    │
│  │  │  (Multi-iteration reasoning)                │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  StateManager (Context tracking)            │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. BedrockProvider (`src/core/bedrock_provider.py`)

**Purpose:** Interface to AWS Bedrock for LLM inference

**Key Methods:**
- `generate()`: Generate text completions
- `generate_embedding()`: Create vector embeddings
- Token counting and error handling

**Configuration:**
```yaml
bedrock:
  model_id: "anthropic.claude-sonnet-4-20250514-v1:0"
  embedding_model_id: "amazon.titan-embed-text-v2:0"
  region: "us-east-1"
  max_tokens: 64000
```

**Usage:**
```python
provider = BedrockProvider(model_id, embedding_model_id, region)
response = provider.generate(prompt, max_tokens=1000)
embedding = provider.generate_embedding(text)
```

### 2. VectorStore (`src/core/vector_store.py`)

**Purpose:** Persistent vector storage using ChromaDB

**Key Methods:**
- `add_chunks()`: Store document chunks with embeddings
- `retrieve_relevant_chunks()`: Semantic search
- `count()`: Get document count
- `get_stats()`: Collection statistics

**Features:**
- Automatic embedding generation
- Cosine similarity search
- Persistent storage
- Metadata filtering

**Usage:**
```python
vector_store = VectorStore(config)
vector_store.add_chunks(chunks, source="document.pdf")
results = vector_store.retrieve_relevant_chunks(query, k=5)
```

### 3. PDFParser (`src/core/pdf_parser.py`)

**Purpose:** Multi-modal PDF parsing with text and vision

**Key Methods:**
- `parse_pdf()`: Extract text and images
- `chunk_text()`: Smart text chunking

**Features:**
- Text extraction with pypdf
- Image extraction (vision placeholder)
- Configurable chunk sizes
- Overlap for context preservation

**Chunking Strategy:**
```
Document: [Page 1] [Page 2] [Page 3] ...

Chunk 1: [────────4000 tokens────────]
              [200 overlap]
Chunk 2:           [────────4000 tokens────────]
                        [200 overlap]
Chunk 3:                     [────────4000 tokens────────]
```

### 4. QAGenerator (`src/generators/qa_generator.py`)

**Purpose:** Generate Q&A pairs from documents

**Key Methods:**
- `generate_qa_from_documents()`: Create Q&A pairs
- `save_qa_pairs()`: Export to JSONL

**Process:**
1. Retrieve diverse document chunks
2. Prompt Claude to generate questions
3. Generate answers with context
4. Validate quality
5. Export in standard format

**Complexity Levels:**
- Simple: Basic factual questions
- Medium: Analytical questions
- Complex: Multi-step reasoning

### 5. PersonaTransformer (`src/transformations/persona_transformer.py`)

**Purpose:** Transform queries into 5 different user personas

**Personas:**
1. **P1 - First-time Investor**: Simple language, uncertain, basic questions
2. **P2 - Experienced Professional**: Direct, efficient, industry terms
3. **P3 - Technical Analyst**: Data-driven, quantitative, precise
4. **P4 - Anxious Investor**: Risk-averse, cautious, seeks reassurance
5. **P5 - Directive Executive**: Assertive, time-conscious, action-oriented

**Example Transformation:**
```
Original: "How should I diversify my portfolio?"

P1: "I'm new to investing and wondering how I should split up 
     my money across different investments?"
     
P3: "Can you provide optimal allocation percentages across 
     asset classes for portfolio diversification efficiency?"
     
P5: "Give me the diversification breakdown now."
```

### 6. QueryModifier (`src/transformations/query_modifier.py`)

**Purpose:** Adjust query complexity across 3 levels

**Complexity Levels:**
- **Q-** (Simplified): Beginner-friendly, 1-2 sentences, everyday language
- **Q** (Original): Unchanged, as-is
- **Q+** (Complex): Sophisticated, multi-faceted, 2-3 sentences, technical

**Example:**
```
Q-: "How can I save money for retirement safely?"

Q:  "What's the recommended asset allocation for retirement savings?"

Q+: "What asset allocation framework optimizes risk-adjusted returns 
     for retirement portfolios while accounting for sequence-of-returns 
     risk, tax implications, and dynamic rebalancing strategies?"
```

### 7. TrajectoryGeneratorMultiIter (`src/generators/trajectory_generator_multi_iter.py`)

**Purpose:** Generate multi-iteration reasoning trajectories

**Process:**
```
Iteration 0 (No context):
  ↓
DecisionEngine evaluates → CALL
  ↓
Execute tools → Store results
  ↓
Iteration 1 (With context):
  ↓
DecisionEngine evaluates → CALL again
  ↓
Execute more tools → Accumulate context
  ↓
Iteration 2 (Full context):
  ↓
DecisionEngine evaluates → ANSWER
  ↓
Generate final response
  ↓
Output: 3 training examples
```

**Key Features:**
- Context accumulation across iterations
- Tool result tracking
- Automatic termination logic
- Configurable max iterations

### 8. DecisionEngine (`src/generators/decision_engine.py`)

**Purpose:** Determine when to CALL, ASK, or ANSWER

**Decision Logic:**
```python
if iteration == 0 and no_context:
    → Prefer CALL (gather information)
elif insufficient_information:
    → Prefer CALL or ASK
elif ambiguous_query:
    → ASK for clarification
elif sufficient_context:
    → ANSWER with confidence
```

**Outputs:**
- `CALL`: Execute one or more tools
- `ASK: <question>`: Request user clarification
- `ANSWER: <response>`: Provide final answer

## Data Flow

### Complete Pipeline Flow
```
1. PDF INGESTION
   ├── Read PDF files (pypdf)
   ├── Extract text per page
   ├── Extract images (vision placeholder)
   ├── Chunk text (4000 tokens, 200 overlap)
   ├── Generate embeddings (Titan)
   └── Store in ChromaDB
   
2. Q&A GENERATION
   ├── Retrieve diverse chunks
   ├── Generate questions (Claude)
   ├── Generate answers with context
   └── Export Q&A pairs (JSONL)
   
3. QUERY EXTRACTION
   └── Extract questions from Q&A pairs
   
4. TRANSFORMATION (30× expansion)
   ├── Persona transformation (5×)
   │   ├── P1: First-time investor
   │   ├── P2: Professional
   │   ├── P3: Technical analyst
   │   ├── P4: Anxious investor
   │   └── P5: Executive
   ├── Complexity transformation (3×)
   │   ├── Q-: Simplified
   │   ├── Q:  Original
   │   └── Q+: Complex
   └── Tool data transformation (2×)
       ├── correct: Normal execution
       └── incorrect: Error handling
   
5. TRAJECTORY GENERATION
   ├── For each transformed query:
   │   ├── Iteration 0: Evaluate → CALL/ASK/ANSWER
   │   ├── Execute tools (if CALL)
   │   ├── Accumulate context
   │   ├── Iteration 1: Re-evaluate with context
   │   ├── Continue until ANSWER or max_iterations
   │   └── Generate 1-3 training examples
   └── Export all examples (JSONL)
```

## File Structure
```
synthetic-data-kit-with-trajectory/
├── config/
│   ├── config.yaml           # Main configuration
│   └── tools.json            # Tool definitions
│
├── src/
│   ├── core/                 # Core components
│   │   ├── bedrock_provider.py
│   │   ├── vector_store.py
│   │   ├── pdf_parser.py
│   │   └── __init__.py
│   │
│   ├── generators/           # Generation logic
│   │   ├── qa_generator.py
│   │   ├── trajectory_generator_multi_iter.py
│   │   ├── decision_engine.py
│   │   ├── state_manager.py
│   │   └── __init__.py
│   │
│   ├── transformations/      # Query transformers
│   │   ├── persona_transformer.py
│   │   ├── query_modifier.py
│   │   ├── tool_data_transformer.py
│   │   └── __init__.py
│   │
│   ├── cli/                  # CLI commands
│   │   ├── ingest_commands.py
│   │   ├── generate_commands.py
│   │   ├── transform_commands.py
│   │   ├── pipeline_commands.py
│   │   └── __init__.py
│   │
│   └── utils/                # Utilities
│       ├── config_loader.py
│       ├── logger.py
│       ├── file_utils.py
│       └── __init__.py
│
├── scripts/                  # Utility scripts
│   ├── complete_pipeline_with_ingest.sh
│   ├── validate_format.py
│   ├── analyze_quality.py
│   ├── check_diversity.py
│   └── summarize_dataset.py
│
├── data/
│   ├── pdfs/                 # Input PDFs
│   ├── seed/                 # Seed queries
│   ├── chromadb/            # Vector database (persistent)
│   └── output/              # Generated datasets
│
├── samples/                  # Sample outputs
├── docs/                     # Documentation
├── tests/                    # Test suites
├── logs/                     # Application logs
│
├── main.py                   # CLI entry point
├── requirements.txt
└── README.md
```

## Configuration

### config.yaml Structure
```yaml
# AWS Bedrock
bedrock:
  model_id: "anthropic.claude-sonnet-4-20250514-v1:0"
  embedding_model_id: "amazon.titan-embed-text-v2:0"
  region: "us-east-1"
  max_tokens: 64000
  temperature: 0.7

# PDF Processing
pdf_processing:
  extract_images: true
  chunk_size: 4000
  chunk_overlap: 200
  use_vision_for_images: true

# ChromaDB
chromadb:
  persist_directory: "data/chromadb"
  collection_name: "document_chunks"
  distance_metric: "cosine"

# Output Format
output:
  format: "jsonl"
  output_dir: "data/output"
  fields:
    query: "Q"
    cot: "COT"
    tools: "Tool Set"
    decision: "Decision"
```

## Performance Characteristics

### Throughput

| Operation | Time (avg) | Notes |
|-----------|-----------|-------|
| PDF ingestion (10 pages) | 30-60s | Depends on content density |
| Q&A generation (1 pair) | 5-10s | Bedrock API latency |
| Query transformation (30×) | 60-90s | 30 Claude API calls |
| Trajectory generation (1 query) | 15-30s | 1-3 iterations |
| Complete pipeline (10 seeds) | 10-15 min | Full transformation + generation |

### Scaling

| Seed Queries | Transformed | Training Examples | Time |
|--------------|-------------|-------------------|------|
| 10 | 300 | 300-900 | 10-15 min |
| 50 | 1,500 | 1,500-4,500 | 45-60 min |
| 100 | 3,000 | 3,000-9,000 | 90-120 min |

## Error Handling

### Retry Logic
- **Bedrock API**: 3 retries with exponential backoff
- **PDF parsing**: Skip corrupted files with `--skip-errors`
- **Tool execution**: Mock results on failure

### Validation
- Format validation before saving
- Quality checks for COT length
- Decision type verification
- Metadata completeness

## Security

- **AWS credentials**: Environment variables or AWS CLI config
- **No data persistence**: Bedrock API doesn't store data
- **Local storage**: All data stays on local machine
- **No external APIs**: Only AWS Bedrock

## Future Enhancements

See [VISION_ENHANCEMENT.md](VISION_ENHANCEMENT.md) for:
- Full vision analysis implementation
- Q- reduction system (432× expansion)
- Distributed processing
- Policy knowledge base integration

---

*Architecture designed for scalability, modularity, and production use*
