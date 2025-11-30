# Vision Enhancement Guide

## Current Status

**Text Extraction:** ✅ Working  
**Figure References:** ✅ Captured (42% of chunks reference figures/charts)  
**Vision API Analysis:** ⚠️ Placeholder for future implementation

## What's Currently Captured

The system currently captures:
- Text references to figures: "Figure 1.1 shows...", "as illustrated in Figure 2..."
- Chart/graph mentions in surrounding text
- Context around visual elements

**Example from current data:**
```
"...framework shown in Figure 1.1, we expect outcomes for households to be..."
"...Figure 2.2 lays out four suggested budgeting strategies..."
```

## What Vision Enhancement Will Add

Full vision analysis using AWS Bedrock Claude with vision will:
1. **Extract actual images** from PDFs (charts, graphs, diagrams)
2. **Analyze visual content** using Claude's vision API
3. **Generate descriptions** of what's shown in images
4. **Embed vision analysis** into chunks

**Example of enhanced content:**
```
"Figure 1.1 [Vision Analysis: A bar chart showing three portfolio 
allocation strategies: Conservative (70% bonds, 30% stocks), 
Balanced (50% bonds, 50% stocks), and Aggressive (30% bonds, 
70% stocks). The chart uses blue for bonds and green for stocks.]"
```

## Implementation Approach (Future)

### Phase 1: Image Extraction
Location: `src/core/pdf_parser.py`
```python
def extract_images_from_pdf(self, pdf_path: str) -> List[dict]:
    """
    Extract images from PDF pages.
    
    Returns list of:
    {
        'page_number': int,
        'image': PIL.Image,
        'bbox': tuple,  # bounding box
        'image_index': int
    }
    """
    # Use pypdf or pdfplumber to extract images
    # Convert to PIL Image format
    pass
```

### Phase 2: Vision Analysis
Location: `src/core/bedrock_provider.py`
```python
def analyze_image_with_vision(self, image: bytes, context: str = "") -> str:
    """
    Analyze image using Claude with vision.
    
    Args:
        image: Image bytes (base64 encoded)
        context: Surrounding text for context
    
    Returns:
        Vision analysis description
    """
    # Call Bedrock with vision model
    # Prompt: "Describe this financial chart/diagram in detail"
    pass
```

### Phase 3: Integration
Location: `src/core/pdf_parser.py`
```python
def parse_pdf_with_vision(self, pdf_path: str) -> dict:
    """
    Parse PDF with vision analysis.
    
    1. Extract text and images per page
    2. For each image, call vision API
    3. Embed vision descriptions near related text
    4. Mark chunks with has_vision_content=True
    """
    pass
```

## Configuration

Add to `config/config.yaml`:
```yaml
pdf_processing:
  chunk_size: 4000
  chunk_overlap: 200
  use_vision_for_images: true
  
  # Vision-specific settings (future)
  vision:
    enabled: true
    min_image_size: 100  # pixels, ignore tiny images
    max_images_per_page: 5
    vision_model: "anthropic.claude-sonnet-4-20250514-v1:0"
    vision_prompt: |
      You are analyzing financial charts and diagrams.
      Describe this image in detail, focusing on:
      - Type of visualization (bar chart, line graph, table, etc.)
      - Key data points and trends
      - Labels, legends, and axes
      - Financial insights or patterns shown
```

## Testing Vision Enhancement

When implementing:
```bash
# 1. Test image extraction
python scripts/test_image_extraction.py data/pdfs/sample.pdf

# 2. Test vision API
python scripts/test_vision_api.py --image test_image.png

# 3. Test full integration
python scripts/test_vision_integration.py data/pdfs/sample.pdf

# 4. Verify in VectorDB
python scripts/check_vision_simple.py
```

## Migration Path

### Option 1: Re-ingest with Vision
```bash
# When vision is ready, re-ingest all PDFs
python main.py ingest-batch data/pdfs/ --force-reingest
```

### Option 2: Incremental Enhancement
```bash
# Add vision to new PDFs only
python main.py ingest data/pdfs/new_document.pdf --use-vision
```

### Option 3: Batch Vision Update
```bash
# Update existing chunks with vision analysis
python scripts/enhance_existing_chunks_with_vision.py
```

## Dependencies

Vision enhancement will require:
```txt
# Add to requirements.txt when implementing
Pillow>=10.0.0           # Image processing
pdf2image>=1.16.0        # PDF to images (requires poppler)
pdfplumber>=0.9.0        # Better PDF parsing
```

System dependencies (install via brew/apt):
```bash
# macOS
brew install poppler

# Ubuntu
sudo apt-get install poppler-utils
```

## Cost Considerations

**Vision API calls are more expensive than text-only:**
- Text-only: ~$0.003 per 1K input tokens
- Vision: ~$0.015 per image + text tokens

**Example cost for 100-page PDF:**
- Text-only: ~$0.50
- With vision (50 images): ~$1.25

Budget accordingly for large document sets.

## Quality Metrics

After implementing vision, verify:
- `has_vision_content` metadata: Should be >0%
- Vision description quality: Manual review
- Chunk coherence: Text + vision integrated well
- Search relevance: Vision content improves retrieval

## Resources

- AWS Bedrock Vision docs: https://docs.aws.amazon.com/bedrock/
- Claude vision examples: https://docs.anthropic.com/claude/docs/vision
- pypdf image extraction: https://pypdf.readthedocs.io/

## Status

- [x] Document current state (42% figure references)
- [ ] Implement image extraction
- [ ] Implement vision API integration  
- [ ] Add vision-specific configuration
- [ ] Test with sample PDFs
- [ ] Re-ingest document corpus
- [ ] Validate quality improvements

**Priority:** Low (system is functional without it)  
**Impact:** Medium (improved training data quality)  
**Effort:** Medium (~8-16 hours development + testing)

---

*Last updated: 2024-11-30*  
*Status: Placeholder for future enhancement*
