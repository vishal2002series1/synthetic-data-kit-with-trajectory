cat > README.md << 'EOF'
# 🎯 Trajectory Synthetic Data Generator

**Research toolkit for generating high-quality synthetic training data for Small Language Model (SLM) fine-tuning.**

## Overview

This system generates synthetic training data in the format `{Q, COT, Tool Set, Decision}` using:
- Multi-modal PDF ingestion (text + vision)
- RAG-based Q&A generation from documents
- Query transformations (30× expansion per seed)
- Multi-iteration reasoning trajectories
- Quality filtering and deduplication

## Key Features

✅ **Multi-Modal PDF Processing** - Extract text and analyze images/charts  
✅ **Q&A Generation** - Automatically generate questions from documents  
✅ **Query Transformations** - 5 personas × 3 complexity levels × 2 tool variants = 30× expansion  
✅ **Multi-Iteration Trajectories** - CALL → CALL → ANSWER reasoning chains  
✅ **Quality Control** - Automated filtering and deduplication  
✅ **CLI Interface** - Simple commands for entire pipeline  

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Ingest PDFs
python main.py ingest-batch data/pdfs/

# Generate Q&A from documents
python main.py generate-qa --limit 100

# Run full pipeline
python main.py pipeline data/seed/queries.json
```

## Architecture
```
synthetic-data-kit-with-trajectory/
├── config/           # Configuration files
├── src/              # Source code
│   ├── core/         # Core components (Bedrock, ChromaDB, PDF parsing)
│   ├── transformations/  # Query transformations
│   ├── generators/   # Trajectory generation
│   └── cli/          # CLI commands
├── data/             # Data directory
├── tests/            # Test suite
└── docs/             # Documentation
```

## Documentation

- [Quickstart Guide](docs/QUICKSTART.md)
- [Architecture](docs/ARCHITECTURE.md)
- [CLI Reference](docs/CLI_GUIDE.md)
- [Evaluation Guide](docs/EVALUATION_GUIDE.md)

## Requirements

- Python 3.9+
- AWS Account with Bedrock access (Claude Sonnet 4 + Titan embeddings)
- 5GB+ disk space

## License

MIT License - See LICENSE file for details

## Status

🚧 **Active Development** - Clean rebuild in progress
EOF
## 🔮 Future Enhancements

### Vision Analysis (Planned)

Currently captures text references to figures/charts (42% of chunks). Full vision enhancement will add:
- Image extraction from PDFs
- Claude vision API analysis of charts/graphs/diagrams
- Embedded visual descriptions in training data

See [`docs/VISION_ENHANCEMENT.md`](docs/VISION_ENHANCEMENT.md) for implementation guide.

**Status:** Placeholder - system is fully functional without this  
**Priority:** Low - optional quality improvement
