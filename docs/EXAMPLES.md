# Usage Examples

Real-world examples for common use cases.

## Table of Contents

- [Quick Examples](#quick-examples)
- [Complete Workflows](#complete-workflows)
- [Advanced Usage](#advanced-usage)
- [Integration Examples](#integration-examples)

---

## Quick Examples

### Example 1: Generate Training Data from PDFs
```bash
# 1. Add your PDFs
mkdir -p data/pdfs
cp ~/Documents/financial_reports/*.pdf data/pdfs/

# 2. Run complete pipeline
./scripts/complete_pipeline_with_ingest.sh data/pdfs 20

# Result: 20 Q&A → 600 transformed → 600-1800 training examples
```

**Output:**
```
samples/pipeline_20241130_143052/
├── 01_qa.jsonl              (20 Q&A pairs)
├── 02_queries.json          (20 queries extracted)
├── 03_transformed.jsonl     (600 variants, 30× expansion)
└── 04_trajectories.jsonl    (1,245 training examples)
```

---

### Example 2: Generate from Seed Queries Only
```bash
# 1. Create seed queries
cat > data/seed/investment_queries.json << 'JSON'
{
  "queries": [
    "How should I allocate my retirement portfolio?",
    "What are the tax implications of rebalancing?",
    "How can I reduce investment risk?",
    "What's the difference between active and passive investing?",
    "How do I evaluate fund performance?"
  ]
}
JSON

# 2. Transform (5 → 150)
python main.py transform data/seed/investment_queries.json \
  --output samples/investment_transformed.jsonl

# 3. Generate trajectories (150 → 150-450 examples)
python main.py generate samples/investment_transformed.jsonl \
  --output samples/investment_trajectories.jsonl

# Result: 5 seeds → 150 variants → ~300 training examples
```

---

### Example 3: Generate Specific Persona Only
```bash
# Only generate P3 (Technical Analyst) variants
python main.py transform data/seed/queries.json \
  --persona P3 \
  --output samples/p3_technical.jsonl

# Result: 5 seeds → 30 P3 variants (5 × 3 complexity × 2 tool)
```

---

### Example 4: Generate Complex Queries Only
```bash
# Only generate Q+ (Complex) variants
python main.py transform data/seed/queries.json \
  --complexity Q+ \
  --output samples/complex_queries.jsonl

# Result: 5 seeds → 50 complex variants (5 × 5 personas × 2 tool)
```

---

## Complete Workflows

### Workflow 1: Research Paper Training Data

**Goal:** Generate training data for financial research assistant SLM
```bash
# Step 1: Ingest research papers
mkdir -p data/pdfs/research
cp ~/research_papers/*.pdf data/pdfs/research/
python main.py ingest-batch data/pdfs/research/

# Step 2: Generate Q&A focused on complex questions
python main.py generate-qa \
  --limit 50 \
  --complexity complex \
  --output samples/research_qa.jsonl

# Step 3: Extract queries
python scripts/extract_queries.py \
  samples/research_qa.jsonl \
  samples/research_queries.json

# Step 4: Transform with focus on technical personas
python main.py transform samples/research_queries.json \
  --persona P3 \
  --output samples/research_transformed.jsonl

# Step 5: Generate trajectories with more iterations
python main.py generate samples/research_transformed.jsonl \
  --max-iterations 5 \
  --output samples/research_trajectories.jsonl

# Step 6: Validate
python scripts/analyze_quality.py samples/research_trajectories.jsonl
```

**Expected Output:**
- 50 Q&A pairs
- 300 P3 technical variants
- 900-1,500 training examples with deep reasoning

---

### Workflow 2: Customer Support Training

**Goal:** Train chatbot for investment advisory
```bash
# Step 1: Create customer-like queries
cat > data/seed/customer_queries.json << 'JSON'
{
  "queries": [
    "I'm worried about losing money in the stock market",
    "How much should I save for retirement?",
    "I don't understand what a mutual fund is",
    "Should I invest in bonds or stocks?",
    "I need help understanding my 401k options"
  ]
}
JSON

# Step 2: Transform with customer personas (P1, P4)
python main.py transform data/seed/customer_queries.json \
  --persona P1 \
  --output samples/beginner_transformed.jsonl

python main.py transform data/seed/customer_queries.json \
  --persona P4 \
  --output samples/anxious_transformed.jsonl

# Step 3: Combine and generate
cat samples/beginner_transformed.jsonl samples/anxious_transformed.jsonl > samples/customer_combined.jsonl

python main.py generate samples/customer_combined.jsonl \
  --output samples/customer_support_trajectories.jsonl

# Step 4: Check diversity
python scripts/check_diversity.py samples/customer_support_trajectories.jsonl
```

**Expected Output:**
- Customer-focused training data
- Emphasis on clarification (ASK decisions)
- Reassuring, educational responses

---

### Workflow 3: Batch Processing Multiple Documents

**Goal:** Process large document corpus
```bash
# Step 1: Organize documents by category
mkdir -p data/pdfs/{stocks,bonds,retirement,tax}
# ... copy PDFs to respective folders

# Step 2: Process each category
for category in stocks bonds retirement tax; do
  echo "Processing $category..."
  
  # Ingest
  python main.py ingest-batch data/pdfs/$category/ --skip-errors
  
  # Generate Q&A
  python main.py generate-qa \
    --limit 25 \
    --output samples/${category}_qa.jsonl
  
  # Extract queries
  python scripts/extract_queries.py \
    samples/${category}_qa.jsonl \
    samples/${category}_queries.json
done

# Step 3: Combine all queries
cat > data/seed/all_queries.json << 'JSON'
{
  "queries": []
}
JSON

# Merge queries from all categories
python -c "
import json
from pathlib import Path

all_queries = []
for file in Path('samples').glob('*_queries.json'):
    with open(file) as f:
        data = json.load(f)
        all_queries.extend(data.get('queries', []))

with open('data/seed/all_queries.json', 'w') as f:
    json.dump({'queries': all_queries}, f, indent=2)
"

# Step 4: Run full transformation pipeline
python main.py pipeline data/seed/all_queries.json \
  --output-dir samples/complete_corpus/

# Step 5: Generate summary
python scripts/summarize_dataset.py
```

**Expected Output:**
- 100 Q&A pairs across categories
- 3,000 transformed variants
- 3,000-9,000 training examples
- Comprehensive coverage

---

## Advanced Usage

### Example 5: Custom Transformation Filtering
```bash
# Generate only specific combinations
# P1 (beginner) + Q- (simple) queries

python main.py transform data/seed/queries.json \
  --persona P1 \
  --complexity Q- \
  --output samples/p1_simple.jsonl

# Result: 5 seeds → 10 variants (5 × 1 persona × 1 complexity × 2 tool)
```

---

### Example 6: Incremental Data Generation
```bash
# Week 1: Generate initial dataset
python main.py pipeline data/seed/week1_queries.json \
  --output-dir samples/week1/

# Week 2: Add more data
python main.py pipeline data/seed/week2_queries.json \
  --output-dir samples/week2/

# Week 3: Combine datasets
cat samples/week1/trajectories.jsonl \
    samples/week2/trajectories.jsonl \
    > samples/combined_trajectories.jsonl

# Validate combined dataset
python scripts/validate_format.py samples/combined_trajectories.jsonl
python scripts/analyze_quality.py samples/combined_trajectories.jsonl
```

---

### Example 7: Quality-Filtered Dataset
```bash
# Generate large dataset
python main.py pipeline data/seed/queries.json \
  --output-dir samples/raw/

# Analyze quality
python scripts/analyze_quality.py samples/raw/trajectories.jsonl > quality_report.txt

# Manual review and filtering
# (Remove low-quality examples based on COT length, decision distribution, etc.)

# Validate final dataset
python scripts/validate_format.py samples/filtered/trajectories.jsonl
```

---

### Example 8: Multi-Model Comparison
```bash
# Generate with different max iterations
for iterations in 2 3 5; do
  python main.py generate samples/transformed.jsonl \
    --max-iterations $iterations \
    --output samples/trajectories_iter${iterations}.jsonl
  
  echo "Iteration $iterations stats:"
  python scripts/analyze_quality.py samples/trajectories_iter${iterations}.jsonl
done

# Compare results
echo "Comparison:"
wc -l samples/trajectories_iter*.jsonl
```

---

## Integration Examples

### Example 9: Fine-tuning Preparation
```bash
# 1. Generate training data
./scripts/complete_pipeline_with_ingest.sh data/pdfs 100

# 2. Split into train/val/test
python << 'PYTHON'
import json
import random
from pathlib import Path

# Load data
with open('samples/pipeline_latest/04_trajectories.jsonl') as f:
    data = [json.loads(line) for line in f]

# Shuffle
random.shuffle(data)

# Split: 80% train, 10% val, 10% test
n = len(data)
train = data[:int(0.8*n)]
val = data[int(0.8*n):int(0.9*n)]
test = data[int(0.9*n):]

# Save splits
for split_name, split_data in [('train', train), ('val', val), ('test', test)]:
    with open(f'samples/{split_name}.jsonl', 'w') as f:
        for example in split_data:
            f.write(json.dumps(example) + '\n')

print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
PYTHON

# 3. Validate splits
for split in train val test; do
  echo "Validating $split..."
  python scripts/validate_format.py samples/${split}.jsonl
done
```

---

### Example 10: Export to Different Format
```bash
# Convert JSONL to CSV for analysis
python << 'PYTHON'
import json
import csv

# Read JSONL
with open('samples/trajectories.jsonl') as f:
    data = [json.loads(line) for line in f]

# Write CSV
with open('samples/trajectories.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Query', 'Decision', 'Iteration', 'COT_Length'])
    
    for item in data:
        writer.writerow([
            item.get('Q', ''),
            item.get('Decision', ''),
            item.get('metadata', {}).get('iteration', 0),
            len(item.get('COT', ''))
        ])

print("Exported to samples/trajectories.csv")
PYTHON
```

---

### Example 11: Integration with Training Framework
```python
# example_training_integration.py
"""
Example: Load training data for SLM fine-tuning
"""

import jsonlines
from transformers import AutoTokenizer

# Load training data
training_examples = []
with jsonlines.open('samples/train.jsonl') as reader:
    for example in reader:
        training_examples.append(example)

print(f"Loaded {len(training_examples)} training examples")

# Format for your training framework
def format_for_training(example):
    """
    Convert trajectory format to training format.
    
    Input: {Q, COT, Tool Set, Decision}
    Output: Training format for your framework
    """
    
    # Example formatting for instruction fine-tuning
    instruction = example['Q']
    reasoning = example['COT']
    tools = example['Tool Set']
    decision = example['Decision']
    
    # Format as instruction-following example
    formatted = {
        'instruction': instruction,
        'input': json.dumps(tools),
        'output': f"{reasoning}\n\nDecision: {decision}"
    }
    
    return formatted

# Convert all examples
formatted_data = [format_for_training(ex) for ex in training_examples]

# Use with your training pipeline
# model.train(formatted_data)
```

---

### Example 12: Monitoring Data Quality Over Time
```bash
# Track quality metrics over multiple generations
mkdir -p quality_tracking

for batch in batch1 batch2 batch3; do
  # Generate
  python main.py pipeline data/seed/${batch}_queries.json \
    --output-dir samples/${batch}/
  
  # Analyze and save report
  python scripts/analyze_quality.py samples/${batch}/trajectories.jsonl \
    > quality_tracking/${batch}_report.txt
  
  # Extract key metrics
  echo "$batch:" >> quality_tracking/summary.txt
  grep "Mean length" quality_tracking/${batch}_report.txt >> quality_tracking/summary.txt
  grep "CALL:" quality_tracking/${batch}_report.txt >> quality_tracking/summary.txt
  echo "" >> quality_tracking/summary.txt
done

# View summary
cat quality_tracking/summary.txt
```

---

## Tips for Production Use

### 1. Start Small, Scale Gradually
```bash
# Day 1: Test with 5 queries
python main.py pipeline data/seed/test_5.json --output-dir samples/test/

# Day 2: Expand to 20 queries
python main.py pipeline data/seed/test_20.json --output-dir samples/small/

# Week 1: Full production (100+ queries)
python main.py pipeline data/seed/production.json --output-dir samples/production/
```

### 2. Version Your Training Data
```bash
# Use timestamps in output directories
VERSION=$(date +%Y%m%d_%H%M%S)
python main.py pipeline queries.json --output-dir samples/v_${VERSION}/

# Track in git (optional)
git add samples/v_${VERSION}/
git commit -m "Training data version ${VERSION}"
```

### 3. Monitor Resource Usage
```bash
# Check disk space before large runs
df -h data/chromadb

# Monitor during execution
watch -n 5 'ls -lh samples/pipeline_*/04_trajectories.jsonl'
```

### 4. Backup ChromaDB
```bash
# Backup vector database
tar -czf backups/chromadb_$(date +%Y%m%d).tar.gz data/chromadb/

# Restore if needed
tar -xzf backups/chromadb_YYYYMMDD.tar.gz -C data/
```

---

*For more details, see [API_REFERENCE.md](API_REFERENCE.md) and [FAQ.md](FAQ.md)*
