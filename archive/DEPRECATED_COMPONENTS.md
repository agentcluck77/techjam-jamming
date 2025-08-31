# Deprecated Components Archive

This directory contains deprecated components that have been replaced or superseded by newer implementations.

## JSON Refactorer (Deprecated: 2025-08-29)

### File: `json_refactorer.py`

**Original Purpose**: TikTok terminology expansion and feature context enrichment for legal analysis

**Why Deprecated**:
- New lawyer agent workflows process structured documents, not sparse feature descriptions
- Terminology expansion moved to user-editable Knowledge Base system
- Direct document processing is more efficient than feature enrichment pipeline
- Knowledge Base provides more flexible and maintainable terminology management

**Functionality Migrated To**:
- **Knowledge Base**: `LawyerKnowledgeBase.expand_terminology()`
- **Direct Processing**: Lawyer agent processes documents directly
- **User Management**: UI-based terminology editing and management

**Migration Notes**:
- Extract terminology data from `data/terminology.json` → Knowledge Base initial content
- TikTok jargon mappings → User-editable knowledge base
- Geographic inference logic → Direct legal analysis in lawyer agent
- Risk identification patterns → Legal compliance assessment framework

**Data Migration Required**:
```python
# Extract terminology from json_refactorer.py for Knowledge Base
terminology_data = {
    "tiktok_terminology": {
        "ASL": "American Sign Language",
        "jellybean": "feature component", 
        "Creator Fund": "monetization program",
        "LIVE": "live streaming"
    },
    "geographic_mappings": {
        "US": ["United States", "America"],
        "EU": ["Europe", "European Union"]
    },
    "feature_categories": {
        "social_features": ["messaging", "following", "sharing"]
    },
    "risk_indicators": {
        "high_risk": ["data collection", "minors", "payment processing"]
    }
}
```

**Archive Date**: 2025-08-29  
**Archived By**: System Architecture Team  
**Safe to Delete**: After Knowledge Base migration is complete and tested

---

## Archive Guidelines

1. **Before Archiving**: Ensure all functionality is migrated to new systems
2. **Data Migration**: Extract any useful data/configuration before archiving
3. **Documentation**: Document why component was deprecated and what replaced it
4. **Testing**: Verify replacement systems work before removing from active codebase
5. **Cleanup**: Remove imports and references from active code after archiving