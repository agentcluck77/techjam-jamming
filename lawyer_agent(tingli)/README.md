# Lawyer Agent - TikTok Compliance System

**Team Member**: Tingli  
**Competition**: TikTok TechJam - Automated Compliance Detection

## Overview

The Lawyer Agent is a specialized component of an automated compliance detection system that uses Large Language Models (LLMs) to identify features requiring geo-specific compliance logic. This system addresses TikTok's challenge of managing dozens of geographic regulations across global markets.

## Problem Statement

TikTok operates globally and must satisfy various geographic regulations (GDPR, state privacy laws, etc.). The Lawyer Agent helps answer:
- "Does this feature require dedicated logic to comply with region-specific legal obligations?"
- "How many features have we rolled out to ensure compliance with this regulation?"

## System Architecture

```
Document Agent → Standardized Document → Lawyer Agent → Compliance Assessment
                                          ↓
                            Vector Database (MiniLM-L6-v2)
                                          ↓
                               Legal Requirements Database
```

## Target Regulations

The system focuses on these 5 key regulations:
1. **EU Digital Service Act (DSA)** - Content moderation and platform obligations
2. **California Protecting Our Kids from Social Media Addiction Act** - Minor protection
3. **Florida Online Protections for Minors** - Age verification and parental consent
4. **Utah Social Media Regulation Act** - Youth safety measures
5. **US NCMEC Reporting Requirements** - Child safety content reporting

## Features

### Core Functionality
- **Semantic Legal Matching**: Uses MiniLM-L6-v2 embeddings to match features against legal requirements
- **Compliance Reasoning**: Explainable AI decisions with confidence scores
- **Multi-format Input**: Supports structured documents and raw text
- **Batch Processing**: Handle multiple features simultaneously
- **REST API**: Easy integration with document processing pipeline

### Key Components
- **Vector Database**: FAISS-based similarity search with 384-dimensional embeddings
- **Feature Analyzer**: Extracts compliance indicators (geographic, age-related, data processing)
- **Compliance Engine**: Makes final compliance decisions with reasoning
- **Test Processor**: Generates competition-format CSV outputs

## Installation

```bash
# Clone repository
git clone <repository-url>
cd lawyer_agent\(tingli\)

# Install dependencies
pip install -r requirements.txt

# Initialize the system (builds vector database)
python -c "from src.core.compliance_engine import ComplianceEngine; ComplianceEngine()"
```

## Usage

### API Server
```bash
# Start the Flask API server
cd src/api
python main.py
```

The API runs on `http://localhost:5000` with endpoints:
- `POST /analyze` - Analyze single feature
- `POST /batch-analyze` - Analyze multiple features  
- `POST /parse-feature` - Parse document structure
- `GET /regulations` - List available regulations
- `GET /system-status` - System health check

### Direct Usage
```python
from src.core.compliance_engine import ComplianceEngine

# Initialize engine
engine = ComplianceEngine()

# Analyze a feature
feature_text = """
Title: Location-based Content Blocking
Description: Feature reads user location to enforce France's copyright rules
Geographic Scope: EU, France  
Data Processing: location tracking, geolocation
"""

assessment = engine.assess_feature_compliance(feature_text)
print(f"Requires Compliance: {assessment.requires_compliance}")
print(f"Confidence: {assessment.confidence:.2f}")
print(f"Reasoning: {assessment.reasoning}")
```

### Test Dataset Processing
```python
from src.utils.test_processor import TestDatasetProcessor

# Process competition dataset
processor = TestDatasetProcessor()
output_path = processor.process_csv_dataset("test_dataset.csv")
print(f"Results saved to: {output_path}")
```

## Technical Details

### Model Architecture
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Vector Store**: FAISS with cosine similarity
- **No Training Required**: Uses pre-trained models with RAG approach

### Compliance Decision Logic
1. **Semantic Similarity**: Match feature text to legal provisions
2. **Indicator Analysis**: Extract compliance-relevant patterns
3. **Confidence Scoring**: Multi-factor confidence calculation
4. **Reasoning Generation**: Explainable decision rationale

### Performance Considerations
- **Embedding Caching**: Cached embeddings for faster processing
- **Batch Processing**: Efficient handling of multiple features
- **Similarity Thresholds**: Configurable precision/recall balance

## Output Format

The system generates CSV files with these columns:
- `test_case_id`: Unique identifier
- `feature_title`: Feature name
- `requires_compliance`: Boolean compliance flag
- `confidence`: Confidence score (0.0-1.0)
- `reasoning`: Human-readable explanation
- `matched_regulations`: Relevant legal frameworks
- `assessment_timestamp`: Processing timestamp

## Development Tools

- **Python 3.8+**: Core language
- **sentence-transformers**: Embedding generation
- **FAISS**: Vector similarity search
- **Flask**: REST API framework
- **pandas**: Data processing
- **loguru**: Structured logging

## Project Structure

```
lawyer_agent(tingli)/
├── src/
│   ├── core/               # Core compliance logic
│   │   ├── embeddings.py   # MiniLM-L6-v2 integration
│   │   ├── feature_analyzer.py  # Document parsing
│   │   └── compliance_engine.py # Main reasoning engine
│   ├── database/           # Data management
│   │   ├── law_loader.py   # Legal database loader
│   │   └── vector_store.py # FAISS vector database
│   ├── api/               # REST API
│   │   └── main.py        # Flask application
│   └── utils/             # Utilities
│       └── test_processor.py # Test dataset processing
├── data/                  # Data storage
│   ├── regulations.json   # Legal requirements database
│   └── vector_store/      # FAISS indices
├── config/               # Configuration
│   └── config.py         # System settings
├── output/               # Generated results
├── tests/                # Unit tests
└── requirements.txt      # Dependencies
```

## Competition Deliverables

✅ **Working Solution**: Complete compliance detection system  
✅ **Public Repository**: Available on GitHub with setup instructions  
✅ **Documentation**: Comprehensive README and API documentation  
✅ **Local Demo**: Runnable Flask API with test endpoints  
✅ **CSV Output**: Competition-format result files  

## Demonstration

The system can be demonstrated via:
1. **REST API**: Interactive compliance analysis
2. **Batch Processing**: Test dataset evaluation  
3. **Sample Cases**: Pre-built test scenarios
4. **Real-time Analysis**: Live feature assessment

## Future Enhancements

- **Domain Fine-tuning**: Legal-specific model training
- **Multi-language Support**: International regulation compliance
- **Real-time Integration**: Live feature pipeline processing
- **Advanced Reasoning**: Chain-of-thought compliance logic

---

**Contact**: Tingli  
**Competition**: TikTok TechJam 2024  
**Focus**: Defensive security and compliance automation