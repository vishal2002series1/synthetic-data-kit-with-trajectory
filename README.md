# Trajectory Synthetic Data Generator

A production-ready system for generating high-quality training data for Small Language Models (SLMs) using trajectory-based synthetic data generation with multi-iteration reasoning patterns.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 What This Does

Generates **thousands of training examples** from a small set of seed queries through:
- **Multi-iteration reasoning trajectories** (CALL → CALL → ANSWER patterns)
- **30× query expansion** via persona/complexity/tool transformations
- **Document-based Q&A generation** from PDF knowledge bases
- **Stateless iterative reasoning** teaching when to use tools, ask questions, or answer

**Input:** 10 seed queries  
**Output:** 300-900 training examples in `{Q, COT, Tool Set, Decision}` format

---

## ⚡ Quick Start
```bash
# 1. Clone and setup
git clone https://github.com/vishal2002series1/synthetic-data-kit-with-trajectory.git
cd synthetic-data-kit-with-trajectory
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure AWS credentials
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 3. Add PDFs and run complete pipeline
mkdir -p data/pdfs
cp your_pdfs/*.pdf data/pdfs/
./scripts/complete_pipeline_with_ingest.sh 20

# Output: samples/pipeline_TIMESTAMP/04_trajectories.jsonl
```

See [QUICKSTART.md](docs/QUICKSTART.md) for detailed setup.

---

## 📊 Key Features

### 🎓 Training Data Generation
- **Multi-iteration trajectories**: 1-3 reasoning steps per query
- **Decision patterns**: CALL (use tools), ASK (clarify), ANSWER (respond)
- **Chain-of-thought reasoning**: High-quality COT for each iteration
- **Tool orchestration**: Teaches SLMs when/how to use tools

### 🔄 30× Query Expansion
- **5 Personas**: First-time investor, Professional, Technical analyst, Anxious investor, Executive
- **3 Complexity levels**: Simplified (Q-), Original (Q), Complex (Q+)
- **2 Tool variants**: Correct data, Incorrect data (error handling)
- **Total**: 5 × 3 × 2 = **30× expansion per seed**

### 📚 Document Processing
- **PDF ingestion**: Multi-modal parsing with text + vision
- **ChromaDB vector storage**: Persistent embeddings
- **Smart chunking**: 4000 tokens with 200 overlap
- **Q&A generation**: Extract questions from documents

### 🛠️ Production Ready
- **Complete CLI**: 7 commands for full workflow
- **Quality validation**: Format, diversity, quality checks
- **Progress tracking**: Real-time progress bars
- **Error handling**: Robust error recovery

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                   INPUT SOURCES                              │
├─────────────────────────────────────────────────────────────┤
│  PDFs (data/pdfs/)          Seed Queries (data/seed/)       │
│       │                              │                       │
│       ▼                              ▼                       │
│  ┌─────────┐                   ┌──────────┐                │
│  │ Ingest  │                   │ Manual   │                │
│  │ PDFs    │                   │ Seeds    │                │
│  └────┬────┘                   └────┬─────┘                │
│       │                              │                       │
│       ▼                              │                       │
│  ┌─────────────────┐                │                       │
│  │   VectorDB      │                │                       │
│  │  (ChromaDB)     │                │                       │
│  │  291 documents  │                │                       │
│  └────┬────────────┘                │                       │
│       │                              │                       │
│       ▼                              │                       │
│  ┌─────────────────┐                │                       │
│  │ Q&A Generator   │                │                       │
│  └────┬────────────┘                │                       │
│       │                              │                       │
│       ├──────────────────────────────┘                       │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────┐                   │
│  │     TRANSFORMATION PIPELINE          │                   │
│  │  (30× Expansion)                     │                   │
│  │                                      │                   │
│  │  ┌──────────────────────────────┐  │                   │
│  │  │  Persona Transformer (5×)    │  │                   │
│  │  │  P1-P5 variants              │  │                   │
│  │  └────────────┬─────────────────┘  │                   │
│  │               ▼                     │                   │
│  │  ┌──────────────────────────────┐  │                   │
│  │  │  Query Modifier (3×)         │  │                   │
│  │  │  Q-, Q, Q+ complexity        │  │                   │
│  │  └────────────┬─────────────────┘  │                   │
│  │               ▼                     │                   │
│  │  ┌──────────────────────────────┐  │                   │
│  │  │  Tool Data Transformer (2×)  │  │                   │
│  │  │  correct/incorrect variants  │  │                   │
│  │  └────────────┬─────────────────┘  │                   │
│  └───────────────┼─────────────────────┘                   │
│                  │                                          │
│                  ▼                                          │
│  ┌─────────────────────────────────────┐                   │
│  │   TRAJECTORY GENERATOR               │                   │
│  │   (Multi-iteration)                  │                   │
│  │                                      │                   │
│  │  Iteration 0: CALL → gather info    │                   │
│  │  Iteration 1: CALL → more analysis  │                   │
│  │  Iteration 2: ANSWER → final result │                   │
│  └────────────┬────────────────────────┘                   │
│               │                                             │
│               ▼                                             │
│  ┌─────────────────────────────────────┐                   │
│  │      TRAINING EXAMPLES               │                   │
│  │  {Q, COT, Tool Set, Decision}       │                   │
│  │                                      │                   │
│  │  • 300-900 examples from 10 seeds   │                   │
│  │  • Multi-iteration reasoning         │                   │
│  │  • Tool usage patterns              │                   │
│  │  • Decision making logic            │                   │
│  └─────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design.

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](docs/QUICKSTART.md) | 5-minute setup guide |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design & components |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | CLI commands & usage |
| [EXAMPLES.md](docs/EXAMPLES.md) | Real-world examples |
| [FAQ.md](docs/FAQ.md) | Troubleshooting & tips |
| [VISION_ENHANCEMENT.md](docs/VISION_ENHANCEMENT.md) | Future vision roadmap |

---

## 🎯 Training Data Format

Each training example teaches SLMs **when to take action**:
```json
{
  "Q": "How should I optimize my portfolio for retirement?",
  "COT": "The user needs portfolio optimization guidance. I should first analyze their current risk profile, then suggest allocation strategies...",
  "Tool Set": [
    {
      "name": "analyze_portfolio_risk",
      "description": "Analyze portfolio risk metrics",
      "parameters": {"client_id": "...", "lookback_period": "3Y"}
    }
  ],
  "Decision": "CALL",
  "metadata": {"iteration": 0, "decision_type": "CALL"}
}
```

**Decision Types:**
- `CALL`: Execute tools to gather information
- `ASK: <question>`: Request user clarification
- `ANSWER: <response>`: Provide final answer

---

## 🚀 Usage

### Complete Pipeline (Recommended)
```bash
# Generate everything: Q&A → Transformations → Trajectories
./scripts/complete_pipeline_with_ingest.sh data/pdfs 20

# Output: 20 Q&A → 600 transformations → 600-1800 training examples
```

### Individual Commands
```bash
# 1. Ingest PDFs
python main.py ingest-batch data/pdfs/

# 2. Generate Q&A from documents
python main.py generate-qa --limit 50 --output samples/qa.jsonl

# 3. Transform queries (30× expansion)
python main.py transform queries.json --output samples/transformed.jsonl

# 4. Generate trajectories
python main.py generate queries.json --output samples/trajectories.jsonl

# 5. View statistics
python main.py stats
```

See [API_REFERENCE.md](docs/API_REFERENCE.md) for all commands.

---

## 📊 Results

**From 3 seed queries:**
- ✅ 90 transformed queries (30× expansion)
- ✅ 150+ training examples (multi-iteration)
- ✅ CALL → CALL → ANSWER patterns
- ✅ High-quality chain-of-thought reasoning

**From 20 Q&A pairs:**
- ✅ 600 transformed queries
- ✅ 600-1,800 training examples
- ✅ Ready for SLM fine-tuning

---

## 🔧 Configuration

Edit `config/config.yaml`:
```yaml
bedrock:
  model_id: "anthropic.claude-sonnet-4-20250514-v1:0"
  region: "us-east-1"
  max_tokens: 64000

pdf_processing:
  chunk_size: 4000
  chunk_overlap: 200
  use_vision_for_images: true

output:
  format: "jsonl"
  fields:
    query: "Q"
    cot: "COT"
    tools: "Tool Set"
    decision: "Decision"
```

---

## 🧪 Quality Validation
```bash
# Validate format
python scripts/validate_format.py samples/trajectories.jsonl

# Analyze quality
python scripts/analyze_quality.py samples/trajectories.jsonl

# Check diversity
python scripts/check_diversity.py samples/transformed.jsonl

# Overall summary
python scripts/summarize_dataset.py
```

---

## 🎓 Use Cases

### 1. Fine-tuning Small Language Models
Train models to:
- Decide when to use tools vs. answer directly
- Chain multiple tool calls for complex tasks
- Ask clarifying questions when needed
- Generate reasoning before acting

### 2. Conversational AI Training
- Multi-turn dialogue patterns
- Context accumulation across turns
- Tool-augmented responses

### 3. Research & Experimentation
- Test different reasoning patterns
- Evaluate decision-making strategies
- Benchmark SLM performance

---

## 📈 Expansion Capabilities

**Current:**
- 30× per seed query (5 personas × 3 complexity × 2 tool variants)
- 1-3 training examples per transformed query
- **Total: 30-90× effective expansion**

**Future (with Q- reduction):**
- 432× per seed query (Q- iterative simplification)
- Policy knowledge base integration
- Enhanced vision analysis

---

## 🔮 Roadmap

- [x] Multi-iteration trajectory generation
- [x] 30× query transformation
- [x] PDF ingestion with ChromaDB
- [x] Complete CLI interface
- [x] Quality validation tools
- [ ] Enhanced vision analysis (see [VISION_ENHANCEMENT.md](docs/VISION_ENHANCEMENT.md))
- [ ] Q- reduction system (432× expansion)
- [ ] Policy knowledge base integration
- [ ] Distributed processing for scale

---

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Vision analysis enhancement
- Additional transformation strategies
- Quality metrics & evaluation
- SLM fine-tuning examples

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- Built with AWS Bedrock (Claude Sonnet 4)
- ChromaDB for vector storage
- Inspired by trajectory-based reasoning research

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/vishal2002series1/synthetic-data-kit-with-trajectory/issues)
- **Documentation**: [docs/](docs/)
- **Examples**: [EXAMPLES.md](docs/EXAMPLES.md)

---

## 📊 Project Status

**Phase 8/8 Complete** ✅

- ✅ Phase 1: Repository setup
- ✅ Phase 2: Core components
- ✅ Phase 3: Q&A generation
- ✅ Phase 4: Multi-iteration trajectories
- ✅ Phase 5: Transformations (30× expansion)
- ✅ Phase 6: CLI integration
- ✅ Phase 7: Evaluation & samples
- ✅ Phase 8: Documentation

**Status:** Production Ready 🚀

---

*Built for generating high-quality training data for Small Language Models*
