# Frequently Asked Questions

## Table of Contents

- [Setup & Installation](#setup--installation)
- [Usage & Operations](#usage--operations)
- [Troubleshooting](#troubleshooting)
- [Performance & Scaling](#performance--scaling)
- [Data Quality](#data-quality)
- [Advanced Topics](#advanced-topics)

---

## Setup & Installation

### Q: What are the system requirements?

**A:** Minimum requirements:
- Python 3.9 or higher
- 2GB RAM
- 500MB disk space (more for large document sets)
- Internet connection for AWS Bedrock API
- macOS, Linux, or Windows with WSL

**Recommended:**
- Python 3.10+
- 8GB RAM
- 5GB disk space
- Fast internet connection

---

### Q: How do I get AWS Bedrock access?

**A:** 
1. Create AWS account
2. Request Bedrock access in your region
3. Enable Claude Sonnet 4 and Titan embeddings models
4. Create IAM user with Bedrock permissions
5. Configure credentials:
```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_REGION=us-east-1
```

See: https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html

---

### Q: Installation fails with "cryptography" error

**A:** Install the cryptography package:
```bash
pip install cryptography
```

If that fails, you may need system dependencies:
```bash
# macOS
brew install openssl

# Ubuntu/Debian
sudo apt-get install libssl-dev

# Then retry
pip install cryptography
```

---

### Q: Can I use this without AWS?

**A:** Currently, the system requires AWS Bedrock for:
- Text generation (Claude Sonnet 4)
- Embeddings (Titan)

Alternative LLM providers (OpenAI, local models) are not currently supported but could be added.

---

## Usage & Operations

### Q: How many training examples can I generate from N seed queries?

**A:** Expansion formula:
- **Transformations**: N × 30 (5 personas × 3 complexity × 2 tool variants)
- **Trajectories**: Transformed × 1-3 (depending on iterations)
- **Total**: N × 30-90 training examples

Examples:
- 10 seeds → 300-900 examples
- 50 seeds → 1,500-4,500 examples
- 100 seeds → 3,000-9,000 examples

---

### Q: What's the difference between Q&A generation and seed queries?

**A:** 
- **Q&A Generation**: Extracts questions from ingested PDFs automatically
- **Seed Queries**: Manually created questions you provide

Both work the same way once you have queries. Q&A generation is useful when you have documents but no queries.

---

### Q: How long does it take to generate training data?

**A:** Approximate times:
- PDF ingestion (10 pages): 30-60 seconds
- Q&A generation (1 pair): 5-10 seconds
- Query transformation (30×): 60-90 seconds
- Trajectory generation (1 query): 15-30 seconds

**Complete pipeline (10 seed queries)**: 10-15 minutes

---

### Q: Can I stop and resume a pipeline?

**A:** The pipeline runs in stages. You can:
1. Run stages individually (ingest → generate-qa → transform → generate)
2. Stop between stages and resume later
3. Use intermediate outputs (transformed.jsonl) as input to next stage

ChromaDB data persists, so you don't need to re-ingest documents.

---

### Q: How do I use only specific personas or complexity levels?

**A:** Use CLI filters:
```bash
# Only P3 persona
python main.py transform queries.json --persona P3

# Only Q+ complexity
python main.py transform queries.json --complexity Q+

# Specific combination
python main.py transform queries.json --persona P1 --complexity Q-
```

---

## Troubleshooting

### Q: "VectorDB is empty" error when generating Q&A

**A:** You need to ingest documents first:
```bash
# Check current count
python main.py stats

# If Documents: 0, ingest PDFs
python main.py ingest-batch data/pdfs/
```

---

### Q: Q&A generation produces empty files

**A:** This happens when:
1. VectorDB has too few chunks (< 50)
2. Documents don't contain relevant content

**Solutions:**
```bash
# Check document count
python main.py stats  # Should show Documents: 100+

# If low, add more PDFs
cp more_pdfs/*.pdf data/pdfs/
python main.py ingest-batch data/pdfs/

# Try smaller Q&A limit
python main.py generate-qa --limit 5
```

---

### Q: "wrong pointing object" warnings during PDF ingestion

**A:** These warnings are harmless. They indicate minor PDF metadata issues but don't affect ingestion.

If you want to suppress them:
```bash
python main.py ingest-batch data/pdfs/ 2>/dev/null
```

---

### Q: Bedrock API rate limit errors

**A:** Bedrock has default quotas:
- **Invocations**: 100/minute (varies by region)
- **Tokens**: Varies by model

**Solutions:**
1. Process smaller batches
2. Add delays between API calls (modify code)
3. Request quota increases from AWS

---

### Q: ChromaDB "Collection already exists" error

**A:** This is normal - ChromaDB reuses existing collections. To start fresh:
```bash
# Delete ChromaDB data
rm -rf data/chromadb/

# Re-ingest
python main.py ingest-batch data/pdfs/
```

---

### Q: Training examples have incorrect format

**A:** Validate format:
```bash
python scripts/validate_format.py output.jsonl
```

Common issues:
- Missing required fields (Q, COT, Tool Set, Decision)
- Invalid JSON syntax

Check `config.yaml` field mapping:
```yaml
output:
  fields:
    query: "Q"      # Must match
    cot: "COT"
    tools: "Tool Set"
    decision: "Decision"
```

---

## Performance & Scaling

### Q: How much does it cost to run?

**A:** AWS Bedrock costs (approximate):
- **Claude Sonnet 4**: $0.003 per 1K input tokens, $0.015 per 1K output tokens
- **Titan Embeddings**: $0.0001 per 1K tokens

**Example costs:**
- 100 Q&A pairs: ~$2-3
- 1,000 transformations: ~$3-5
- 1,000 trajectory generations: ~$8-12
- **Total for 100 seeds → 3,000 examples**: ~$15-20

---

### Q: Can I run this on multiple machines?

**A:** Not currently. The system uses:
- Local ChromaDB (not distributed)
- Sequential processing

For distributed processing, you'd need to:
1. Use shared ChromaDB instance (or separate per machine)
2. Split seed queries across machines
3. Merge results

Future enhancement planned.

---

### Q: How do I speed up generation?

**A:** Optimization tips:
1. **Reduce transformations**: Use specific persona/complexity filters
2. **Limit iterations**: `--max-iterations 2` instead of 3
3. **Batch processing**: Run multiple pipelines in parallel on different query sets
4. **Skip Q&A**: Use manual seed queries instead of document Q&A

---

### Q: What's the maximum number of PDFs I can ingest?

**A:** Practical limits:
- **ChromaDB**: No hard limit, tested with 1,000+ documents
- **Disk space**: ~1MB per 50 pages of PDF (embeddings + text)
- **Memory**: Minimal (ChromaDB uses disk storage)

For very large corpora (10,000+ PDFs), consider:
- Processing in batches
- Using external vector DB (Pinecone, Weaviate)

---

## Data Quality

### Q: How do I ensure high-quality training data?

**A:** Use validation tools:
```bash
# 1. Format validation
python scripts/validate_format.py output.jsonl

# 2. Quality analysis
python scripts/analyze_quality.py output.jsonl

# 3. Diversity check
python scripts/check_diversity.py output.jsonl
```

**Quality indicators:**
- COT mean length: 200+ characters
- Decision distribution: Mix of CALL/ASK/ANSWER
- Multi-iteration examples: >30% of total
- Unique queries: >80%

---

### Q: What makes a good seed query?

**A:** Good seed queries:
- **Specific**: "How should I allocate a retirement portfolio?" (good) vs. "Tell me about investing" (too broad)
- **Action-oriented**: Require decision-making or tool usage
- **Domain-relevant**: Match your target use case
- **Diverse**: Cover different aspects of your domain

**Examples:**
```json
{
  "queries": [
    "How can I reduce portfolio risk while maintaining growth?",
    "What are the tax implications of rebalancing my 401k?",
    "Should I invest in individual stocks or index funds?",
    "How do I evaluate whether a fund is performing well?"
  ]
}
```

---

### Q: Why are some examples only 1 iteration?

**A:** This is correct behavior! The DecisionEngine decides:
- **ANSWER immediately** (1 iteration): Query can be answered from general knowledge
- **CALL → ANSWER** (2 iterations): Needs one tool call
- **CALL → CALL → ANSWER** (3 iterations): Complex, multi-step reasoning

This diversity teaches models when to act vs. when to answer directly.

---

### Q: How do I filter out low-quality examples?

**A:** Manual or automated filtering:

**Automated:**
```python
import json

# Filter by COT length
with open('input.jsonl') as f_in, open('filtered.jsonl', 'w') as f_out:
    for line in f_in:
        example = json.loads(line)
        if len(example.get('COT', '')) >= 100:  # Min 100 chars
            f_out.write(line)
```

**Manual:**
- Review `analyze_quality.py` output
- Identify problem examples
- Remove or regenerate

---

## Advanced Topics

### Q: How does vision analysis work?

**A:** Currently, vision is a **placeholder**. The system:
- ✅ Captures text references to figures ("Figure 1.1 shows...")
- ⏳ Full vision analysis (extracting and describing images) is planned

See [VISION_ENHANCEMENT.md](VISION_ENHANCEMENT.md) for implementation roadmap.

---

### Q: Can I customize the decision logic?

**A:** Yes! Edit `src/generators/decision_engine.py`:
```python
def decide(self, query, context, iteration):
    # Add custom logic
    if "urgent" in query.lower():
        return "ANSWER", "Provide immediate response"
    
    # Default logic
    return super().decide(query, context, iteration)
```

---

### Q: Can I add custom tools?

**A:** Yes! Edit `config/tools.json`:
```json
{
  "name": "my_custom_tool",
  "description": "What the tool does",
  "parameters": {
    "type": "object",
    "properties": {
      "param1": {"type": "string", "description": "..."}
    },
    "required": ["param1"]
  }
}
```

The system will include it in trajectory generation.

---

### Q: How do I export data for fine-tuning?

**A:** Training data is already in JSONL format. For specific frameworks:

**Hugging Face:**
```python
from datasets import load_dataset

dataset = load_dataset('json', data_files='samples/train.jsonl')
# Use with transformers Trainer
```

**OpenAI Fine-tuning:**
```bash
# Convert to OpenAI format
python scripts/convert_to_openai_format.py input.jsonl output.jsonl
```

See [EXAMPLES.md](EXAMPLES.md#integration-examples) for more.

---

### Q: Can I use this for languages other than English?

**A:** Currently optimized for English. For other languages:
1. Modify prompts in transformation classes
2. Use multilingual embeddings
3. Test with non-English PDFs

Claude Sonnet 4 supports many languages, but transformations are English-focused.

---

### Q: What's the roadmap for future features?

**A:** Planned enhancements:
- [ ] Full vision analysis (extract and describe images)
- [ ] Q- reduction system (432× expansion)
- [ ] Policy knowledge base integration
- [ ] Distributed processing
- [ ] Additional LLM providers
- [ ] Web UI

See GitHub issues for tracking.

---

## Still Have Questions?

- **Documentation**: Check [docs/](.)
- **Examples**: See [EXAMPLES.md](EXAMPLES.md)
- **Issues**: [GitHub Issues](https://github.com/vishal2002series1/synthetic-data-kit-with-trajectory/issues)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)

---

*Last updated: 2024-11-30*
