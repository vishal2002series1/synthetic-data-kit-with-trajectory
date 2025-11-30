# Quick Start Guide

Get up and running in 5 minutes! ⚡

## Prerequisites

- Python 3.9+
- AWS account with Bedrock access
- 500MB disk space
- Git

## Step 1: Clone & Setup (2 minutes)
```bash
# Clone repository
git clone https://github.com/vishal2002series1/synthetic-data-kit-with-trajectory.git
cd synthetic-data-kit-with-trajectory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure AWS (1 minute)
```bash
# Set environment variables
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Or use AWS CLI configure
aws configure
```

**Verify Bedrock access:**
```bash
aws bedrock list-foundation-models --region us-east-1
```

## Step 3: Add Documents (30 seconds)
```bash
# Create PDF directory
mkdir -p data/pdfs

# Add your PDFs
cp /path/to/your/documents/*.pdf data/pdfs/

# OR use sample queries instead (skip PDF ingestion)
cat > data/seed/my_queries.json << 'JSON'
{
  "queries": [
    "How should I allocate my investment portfolio?",
    "What are the tax implications of retirement savings?",
    "How can I reduce investment risk?"
  ]
}
JSON
```

## Step 4: Run Pipeline (90 seconds)

### Option A: With PDFs (Full Pipeline)
```bash
# Run complete pipeline: PDFs → Q&A → Transform → Trajectories
./scripts/complete_pipeline_with_ingest.sh data/pdfs 10

# Output: samples/pipeline_TIMESTAMP/04_trajectories.jsonl
```

### Option B: With Seed Queries (Faster)
```bash
# Transform → Trajectories only
python main.py transform data/seed/my_queries.json \
  --output samples/transformed.jsonl

python main.py generate samples/transformed.jsonl \
  --output samples/trajectories.jsonl
```

## Step 5: Verify Results (30 seconds)
```bash
# Check output
wc -l samples/pipeline_*/04_trajectories.jsonl

# View sample
head -1 samples/pipeline_*/04_trajectories.jsonl | python3 -m json.tool

# Validate quality
python scripts/analyze_quality.py samples/pipeline_*/04_trajectories.jsonl
```

## ✅ Success!

You should now have:
- ✅ Training examples in `{Q, COT, Tool Set, Decision}` format
- ✅ Multi-iteration reasoning patterns
- ✅ 30× query expansion

## Next Steps

1. **Explore examples**: `cat docs/EXAMPLES.md`
2. **Learn CLI commands**: `cat docs/API_REFERENCE.md`
3. **Understand architecture**: `cat docs/ARCHITECTURE.md`
4. **Fine-tune your SLM**: Use generated training data

## Common Issues

### "VectorDB is empty"
```bash
# Re-ingest PDFs
python main.py ingest-batch data/pdfs/
```

### "cryptography module not found"
```bash
pip install cryptography
```

### "AWS credentials not configured"
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

See [FAQ.md](FAQ.md) for more troubleshooting.

---

**Need help?** Check [EXAMPLES.md](EXAMPLES.md) for real-world usage patterns!
