# Technical Requirements Document: Lawyer Agent Compliance Workflows

**Version**: 1.0  
**Date**: 2025-08-29  
**Author**: System Architecture Team  
**Status**: Draft

---

## 1. Overview

This TRD defines three core compliance workflows for the Lawyer Agent, transforming it from a feature analysis tool into a comprehensive compliance management system for legal documents and requirements.

### 1.1 Scope

- **Workflow 1**: Legal Document Upload � Requirements Compliance Check
- **Workflow 2**: Past Law Iteration Detection & Management  
- **Workflow 3**: Requirements Document Upload � Legal Compliance Check
- **Knowledge Base**: Enhanced lawyer agent knowledge system

---

## 2. System Architecture Assessment

### 2.1 Current State
- Lawyer agent handles feature analysis requests
- Mock MCP system with 2-MCP architecture (Legal + Requirements)
- Basic LLM-based parsing and synthesis

### 2.2 Target State (Overhaul Required)
- Document upload and processing workflows
- Bidirectional compliance checking (legal � requirements)
- Past iteration detection and management
- Enhanced knowledge base system
- Human-in-the-loop decision making

### 2.3 Impact Assessment
**=� MAJOR OVERHAUL**: This represents a fundamental shift from reactive analysis to proactive compliance management.

**Components Affected**:
- Lawyer Agent (core logic overhaul)
- Workflow Orchestrator (new workflow types)
- Both MCPs (new operations: delete, metadata search)
- UI Layer (new upload interfaces, user prompts)
- Knowledge Base (new system required)

---

## 3. Workflow Specifications

### 3.1 Workflow 1: Legal Document Compliance Check

**Trigger**: Upload of new legal document  
**Purpose**: Validate all existing requirements against new legal regulations

#### 3.1.1 Flow Specification
```
1. Legal Document Upload → Legal MCP
2. Legal MCP processes and stores document
3. For NEW legal document:
   a. Extract key regulatory topics/requirements from legal doc (1 LLM call)
   b. For each extracted topic: search Requirements MCP for matching requirements (semantic search)
   c. LLM compliance assessment for matched requirements only
4. Generate focused compliance report with actionable issues
```

#### 3.1.2 Technical Requirements
- **Input**: Legal document (PDF)
- **Processing**: Targeted compliance checking via semantic search (not bulk retrieval)
- **Output**: Brief compliance report showing ONLY non-compliant/needs-review items
- **Efficiency**: ~10-20 LLM calls instead of 5,000+ (requirements only checked if relevant)

#### 3.1.3 API Specification
```python
async def check_requirements_compliance(legal_document_id: str) -> ComplianceReport:
    """
    Check all existing requirements against newly uploaded legal document
    Returns brief report containing ONLY non-compliant/needs-review items
    """
    # TODO: Implement full compliance checking workflow

@dataclass
class ComplianceReport:
    legal_document: str
    total_requirements_checked: int
    issues_found: List[ComplianceIssue]
    
@dataclass  
class ComplianceIssue:
    requirement_id: str
    requirement_summary: str
    status: str  # "NON-COMPLIANT" or "NEEDS-REVIEW"
    reason: str
    relevant_regulation: str
    action_needed: str
```

#### 3.1.4 Sample Compliance Report
```
📋 COMPLIANCE CHECK RESULTS
Legal Document: "EU Digital Services Act Amendment 2025"
Requirements Checked: 47 | Issues Found: 3

❌ NON-COMPLIANT (2 items):
• REQ-2023-001: User data retention policy
  Issue: Conflicts with new 90-day retention requirement
  Action: Update retention period from 180 to 90 days

• REQ-2023-015: Content moderation response time  
  Issue: Current 48-hour SLA exceeds new 24-hour requirement
  Action: Reduce response time SLA

⚠️ NEEDS REVIEW (1 item):
• REQ-2023-008: Age verification methodology
  Issue: New regulation allows alternative verification methods
  Action: Legal review recommended for expanded options
```

---

### 3.2 Workflow 2: Past Law Iteration Detection & Management

**Trigger**: Legal document upload  
**Purpose**: Detect and manage outdated law iterations

#### 3.2.1 Flow Specification
```
1. New legal document uploaded
2. Legal MCP semantic search for similar documents
3. LLM assessment of top XX chunks to identify same law/older iterations
4. If past iteration detected:
   a. MANDATORY user prompt: "Past iteration of {law} detected. Delete old version?"
   b. User decision required to proceed
   c. If YES: Delete past iteration from Legal MCP database
   d. If NO: Keep both versions (mark relationship)
5. Continue with document processing
```

#### 3.2.2 Technical Requirements
- **Similarity Detection**: Semantic similarity via vector search
- **LLM Validation**: Assess top XX chunks for same law identification
- **User Interaction**: Mandatory blocking prompt
- **Database Operations**: Delete capability in Legal MCP

#### 3.2.3 API Specification
```python
async def detect_past_iterations(legal_document: LegalDocument) -> List[PastIterationMatch]:
    """
    Detect potential past iterations of the same law
    """
    # TODO: Implement semantic similarity detection
    
async def delete_past_iteration(document_id: str) -> bool:
    """
    Delete past law iteration from Legal MCP database
    """
    # TODO: MCP Team - Implement delete operation in Legal MCP
```

---

### 3.3 Workflow 3: Requirements Document Compliance Check

**Trigger**: Upload of new requirements document (PDF)  
**Purpose**: Validate new requirements against all existing legal regulations

#### 3.3.1 Flow Specification
```
Prerequisites (Requirements MCP Team Scope):
1. Requirements Document (PDF) Upload → Requirements MCP
2. Requirements MCP processes and stores with metadata

Lawyer Agent Scope (Steps 3-6):
3. Lawyer Agent searches new document only (metadata-based ChromaDB filtering)
4. Extract requirements from new document
5. For each extracted requirement:
   a. Search Legal MCP for applicable regulations (all jurisdictions)
   b. LLM compliance assessment with human-in-the-loop
   c. If unclear: Prompt user for clarification/decision
6. Generate compliance status for new requirements
```

#### 3.3.2 Technical Requirements (Lawyer Agent Scope)
- **Input**: Requirements document ID (PDF processing handled by Requirements MCP)
- **Metadata Filtering**: ChromaDB search limited to new document via metadata queries
- **Human-in-the-Loop**: Interactive prompts for unclear compliance cases
- **Output**: Compliance assessment report for extracted requirements
- **Dependencies**: Requirements MCP must complete PDF processing before lawyer agent starts

#### 3.3.3 API Specification
```python
async def check_new_requirements_compliance(
    requirements_document_id: str,
    user_interaction_callback: Callable
) -> RequirementsComplianceReport:
    """
    Check new requirements document against all legal regulations
    """
    # TODO: Implement requirements compliance workflow with HITL
```

---

## 4. Knowledge Base Requirements

### 4.1 Current Gap
Lawyer agent lacks specialized knowledge base for legal compliance analysis, TikTok-specific terminology, and user-customizable domain knowledge.

### 4.2 Knowledge Base Specification

#### 4.2.1 Content Requirements (Legal + Domain Knowledge)
- **Regulatory Precedents**: Past legal compliance decisions and interpretations
- **Compliance Patterns**: Common requirement-regulation mappings and conflicts
- **Jurisdictional Nuances**: Regional legal interpretation differences
- **Legal Analysis Methods**: Standard compliance assessment frameworks
- **TikTok Terminology**: Platform-specific jargon, feature names, technical terms
- **User-Defined Knowledge**: Custom terminology, company-specific interpretations, domain expertise
- **Context Mappings**: Terminology expansions and contextual definitions

#### 4.2.2 Technical Architecture
```python
class LawyerKnowledgeBase:
    """
    Enhanced knowledge system combining legal compliance and domain expertise
    User-editable knowledge base with UI management interface
    """
    
    # Legal Compliance Knowledge (from Legal MCP)
    async def get_compliance_precedents(self, regulation: str) -> List[Precedent]:
        """Get past legal compliance decisions for similar regulations"""  
        # TODO: Implement precedent knowledge retrieval from Legal MCP
        
    async def get_regulatory_patterns(self, requirement_type: str) -> CompliancePattern:
        """Get common legal compliance patterns for requirement types"""
        # TODO: Implement pattern knowledge retrieval from Legal MCP
        
    async def get_jurisdictional_context(self, jurisdiction: str, regulation_type: str) -> JurisdictionalContext:
        """Get jurisdiction-specific legal interpretation patterns"""
        # TODO: Implement jurisdictional knowledge retrieval from Legal MCP
        
    # Domain Knowledge Management (Simple Text-Based)
    async def get_knowledge_base_content(self) -> str:
        """Get the full knowledge base content as text"""
        # TODO: Retrieve knowledge base text from database
        
    async def update_knowledge_base_content(self, content: str, user_id: str) -> bool:
        """Update the knowledge base with new content"""
        # TODO: Save knowledge base text to database
        
    async def enhance_prompt_with_knowledge(self, base_prompt: str) -> str:
        """Enhance LLM prompts with knowledge base context"""
        knowledge_content = await self.get_knowledge_base_content()
        return f"{base_prompt}\n\nAdditional Context:\n{knowledge_content}"
```

#### 4.2.3 Integration Points
- **Legal MCP**: Primary source for legal precedents, regulatory history, and compliance patterns
- **LLM Service**: Enhanced prompts with legal + domain knowledge context for better analysis
- **User Interface**: Knowledge base management UI for terminology editing and customization
- **Database**: Persistent storage for user-defined terminology and custom knowledge

#### 4.2.4 Knowledge Base Management UI (Your Implementation)
```
📚 SIMPLE KNOWLEDGE BASE EDITOR

┌─ Knowledge Base Content ─────────────────────────────────────┐
│                                                              │
│  [Large Text Area - Users type everything here]             │
│                                                              │
│  TikTok terminology, legal notes, compliance patterns,      │
│  custom definitions, jurisdictional context - all in        │
│  free-form text that users can organize however they want   │
│                                                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘

                    [Save]  [Clear]
```

**UI Features to Implement:**
- **Big Text Area**: Large textarea for all knowledge base content
- **Save/Load**: Persist knowledge base content to database
- **Simple Interface**: Just text editing - no complex structure required
- **User-Friendly**: Users organize content however makes sense to them

---

## 5. User Interaction Specifications

### 5.1 User Roles
- **Legal Team**: Upload legal documents, make compliance decisions
- **Product Managers**: Upload requirements, review compliance reports  
- **Developers**: Access compliance status for implementation planning

### 5.2 User Prompts

#### 5.2.1 Past Iteration Detection Prompt
```
�  PAST LAW ITERATION DETECTED
Law: {law_name}
Past Version: {old_version_info}
New Version: {new_version_info}

Would you like to delete the past iteration or keep both versions?
[DELETE PAST] [KEEP BOTH] [VIEW DETAILS]
```

#### 5.2.2 Compliance Clarification Prompt  
```
> COMPLIANCE ASSESSMENT NEEDS CLARIFICATION
Requirement: {requirement_summary}  
Relevant Regulation: {regulation_summary}
Uncertainty: {compliance_question}

How should this be handled?
[COMPLIANT] [NON-COMPLIANT] [NEEDS LEGAL REVIEW] [MORE INFO]
```

---

## 6. Implementation Roadmap

### 6.1 Phase 1: Core Infrastructure
- [ ] Enhanced workflow orchestrator for new workflow types
- [ ] User interaction framework (blocking prompts, callbacks)
- [ ] Knowledge base system architecture
- [ ] MCP delete operations (Legal MCP Team)

### 6.2 Phase 2: Workflow Implementation
- [ ] Workflow 1: Legal document compliance checking
- [ ] Workflow 2: Past iteration detection and management
- [ ] Workflow 3: Requirements compliance checking
- [ ] Knowledge base content population

### 6.3 Phase 3: UI and Integration
- [ ] Document upload interfaces
- [ ] Compliance dashboards and reporting
- [ ] Integration with existing feature analysis workflows
- [ ] Testing and validation

---

## 7. Technical Dependencies

### 7.1 MCP Team Dependencies
- **Legal MCP**: 
  - DELETE endpoint: `DELETE /api/v1/documents/{doc_id}` (hard delete from ChromaDB)
  - SIMILARITY_SEARCH endpoint: `POST /api/v1/similarity_search` (for past iteration detection)
  - Bulk retrieval operations for compliance checking
- **Requirements MCP**: PDF processing, metadata filtering, document management

### 7.2 UI Enhancement Dependencies  
- **Document Upload**: PDF upload interfaces for both legal and requirements docs
- **Interactive Prompts**: Blocking user decision workflows
- **Compliance Dashboards**: Report visualization and management

### 7.3 Core System Dependencies
- **Workflow Orchestrator**: New workflow types and user interaction support
- **LLM Service**: Enhanced compliance assessment prompts
- **Database**: 
  - Audit logs for compliance decisions and document management
  - Workflow state persistence for resumable long-running processes
  - User decision tracking for human-in-the-loop workflows
- **MCP Fallback**: Graceful handling of MCP service failures with partial results

---

## 8. Success Criteria

### 8.1 Functional Requirements
- [ ] Successfully detect non-compliant requirements when legal docs are uploaded
- [ ] Accurately identify past law iterations with <5% false positives
- [ ] Complete requirements compliance checks with human-in-the-loop support
- [ ] Knowledge base provides relevant context for 90% of compliance assessments

### 8.2 Performance Requirements
- [ ] Compliance checks complete within 30 seconds for documents <50 pages
- [ ] Past iteration detection processes within 10 seconds  
- [ ] Knowledge base queries respond within 2 seconds
- [ ] Support ~10 documents per day volume
- [ ] Bulk operations handle multiple documents efficiently
- [ ] Workflow state persistence enables resumable processes

### 8.3 User Experience Requirements
- [ ] Clear, actionable compliance reports
- [ ] Intuitive user prompts with sufficient context for decisions
- [ ] Resumable workflows (save progress and return later)
- [ ] Automatic workflow triggers with clear UI progress indication
- [ ] Single user class (no complex permission management)

---

## 9. Architecture Changes

### 9.1 JSON Refactorer Deprecation
**Status**: ✅ **DEPRECATED** - Functionality moved to Knowledge Base

**Rationale**:
- New workflows process structured documents, not sparse feature descriptions
- Terminology expansion now handled by user-editable Knowledge Base
- Direct document processing is more efficient than feature enrichment pipeline
- Knowledge Base provides more flexible and maintainable terminology management

**Migration Path**:
- JSON Refactorer terminology data → Knowledge Base initial content
- Existing feature analysis workflow → Direct lawyer agent processing
- TikTok jargon expansion → Knowledge Base terminology expansion
- Archive JSON Refactorer code for reference

---

## 10. Risk Assessment

### 9.1 High Risk Items
- **=4 Major Architecture Change**: Complete overhaul of lawyer agent functionality
- **=4 MCP Dependencies**: New operations required from both MCP teams
- **=4 User Interaction Complexity**: Blocking prompts and decision workflows

### 9.2 Medium Risk Items  
- **=� Knowledge Base Content**: Quality and completeness of TikTok-specific knowledge
- **=� Performance**: Large document processing and bulk compliance checking
- **=� Integration**: Maintaining existing feature analysis functionality

### 9.3 Mitigation Strategies
- **Phased Implementation**: Roll out workflows incrementally
- **Backwards Compatibility**: Maintain existing lawyer agent functionality
- **Extensive Testing**: Validate compliance accuracy with legal team

---

## 10. Questions for Stakeholders

1. **Knowledge Base Content**: What specific TikTok policies and precedents should be included?
2. **Compliance Thresholds**: What confidence level should trigger "NEEDS REVIEW" vs automated decisions?
3. **Document Versioning**: How should we handle multiple versions of the same legal document?
4. **Audit Requirements**: What compliance decision audit trails are required?
5. **User Permissions**: Should different user roles have different capabilities (e.g., only legal team can delete past iterations)?

---

*This TRD represents a significant evolution of the lawyer agent into a comprehensive compliance management system. Implementation should be carefully planned with all stakeholder teams.*