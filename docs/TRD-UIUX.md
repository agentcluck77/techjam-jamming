# Technical Requirements Document: UI/UX Design for TRD Compliance Workflows

**Version**: 3.1  
**Date**: 2025-08-29  
**Author**: System Architecture Team  
**Status**: Implementation Ready - Mock MCPs + All Workflows

---

## 1. Overview

This TRD defines the UI/UX design requirements for the TRD Lawyer Agent Compliance Workflows, implementing a **professional Next.js + shadcn/ui frontend** that replaces Streamlit with a streamlined compliance analysis platform optimized for the primary use case: **requirements PDF compliance checking**.

### 1.1 Design Principles

- **Primary Use Case First**: 80% of users just need to drop a requirements PDF and get compliance results
- **Progressive Complexity**: Simple interfaces that reveal advanced features when needed
- **Non-Intrusive HITL**: Cursor-style sidebar for human-in-the-loop interactions without overlay disruption
- **Separated Concerns**: Legal workflows and document management are separate from simple compliance checking
- **Desktop-First**: Next.js responsive design optimized for professional compliance workflows
- **Modern Tech Stack**: shadcn/ui components for professional appearance and developer experience

### 1.2 User Flow Priority

**Primary (80%)**: Requirements PDF → Drag & Drop → HITL Sidebar → Results  
**Secondary (20%)**: Legal document management, batch processing, advanced workflows

---

## 2. Technical Architecture

### 2.1 Frontend Stack

**Framework**: Next.js 14+ with App Router  
**UI Library**: shadcn/ui (built on Radix UI + Tailwind CSS)  
**State Management**: Zustand for client state  
**Real-time**: Server-Sent Events (SSE) for workflow progress  
**File Upload**: react-dropzone for drag & drop functionality  
**HTTP Client**: Fetch API with custom hooks  
**Deployment**: Docker multi-container (frontend + backend + services)  

### 2.2 Backend Integration

**Existing FastAPI Backend**: Minimal changes required  
**MCP Services**: Direct integration with Legal MCP (port 8010) and Requirements MCP (port 8011)  
**New Endpoints**: HITL management and workflow orchestration  
**Real-time Updates**: SSE streaming for progress and HITL prompts  

### 2.3 Project Structure

```
techjam-jamming/
├── frontend/                    # Next.js application
│   ├── app/                    # App Router pages
│   │   ├── page.tsx                   # "/" - Requirements Check
│   │   ├── legal-documents/           
│   │   │   └── page.tsx              # "/legal-documents"
│   │   ├── document-library/          
│   │   │   └── page.tsx              # "/document-library"
│   │   ├── knowledge-base/            
│   │   │   └── page.tsx              # "/knowledge-base"
│   │   ├── results/                   
│   │   │   └── page.tsx              # "/results"
│   │   ├── layout.tsx                # Root layout with navigation
│   │   └── globals.css               # Tailwind styles
│   ├── components/ui/          # shadcn/ui components
│   │   ├── button.tsx                # shadcn Button
│   │   ├── dialog.tsx                # shadcn Dialog
│   │   ├── table.tsx                 # shadcn Table
│   │   ├── progress.tsx              # shadcn Progress
│   │   └── [other shadcn components]
│   ├── components/            # Custom application components
│   │   ├── HITLSidebar.tsx          # Cursor-style sidebar
│   │   ├── DocumentUpload.tsx        # Drag & drop upload
│   │   ├── DocumentTable.tsx         # Document library table
│   │   ├── ComplianceResults.tsx     # Results display
│   │   ├── WorkflowProgress.tsx      # Progress indicators
│   │   └── Navigation.tsx            # App navigation
│   ├── lib/                   # Utilities and configuration
│   │   ├── api.ts                   # FastAPI client functions
│   │   ├── stores.ts                # Zustand stores
│   │   ├── utils.ts                 # shadcn utilities
│   │   └── types.ts                 # TypeScript types
│   ├── hooks/                 # Custom React hooks
│   │   ├── use-workflow.ts          # Workflow state management
│   │   ├── use-hitl.ts              # HITL interactions
│   │   └── use-sse.ts               # Server-Sent Events
│   ├── package.json
│   ├── tailwind.config.js     # Tailwind + shadcn configuration
│   ├── next.config.js
│   └── Dockerfile             # Frontend container
├── backend/                   # Existing FastAPI (minimal changes)
│   └── src/                   # (mostly unchanged)
├── docker-compose.yml         # Updated: frontend + backend + services
└── README.md
```

### 2.6 Docker Configuration

**Updated docker-compose.yml**:
```yaml
services:
  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:          # Existing service (unchanged)
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  postgres:         # Existing service (unchanged)
  redis:            # Existing service (unchanged)
  
  # MCP services will be added by teammates
  legal-mcp:        # Port 8010 (Lucas & Vivian)
  requirements-mcp: # Port 8011 (Tingli & JunHao)
```

### 2.7 State Management Architecture

**Zustand Stores**:
```typescript
// Workflow state across the application
interface WorkflowStore {
  currentWorkflow: Workflow | null
  progress: WorkflowProgress
  sidebarOpen: boolean
  hitlPrompt: HITLPrompt | null
}

// Document management state  
interface DocumentStore {
  documents: Document[]
  selectedDocuments: string[]
  filters: DocumentFilters
  uploadProgress: UploadProgress[]
}

// UI state for complex interactions
interface UIStore {
  activeTab: string
  searchQuery: string
  notifications: Notification[]
}
```

### 2.8 Real-time Communication

**Server-Sent Events (SSE)**:
```typescript
// Progress updates from backend workflows
const useWorkflowProgress = (workflowId: string) => {
  useEffect(() => {
    const eventSource = new EventSource(`/api/workflow/${workflowId}/progress`)
    
    eventSource.onmessage = (event) => {
      const progress = JSON.parse(event.data)
      updateWorkflowStore(progress)
    }
    
    return () => eventSource.close()
  }, [workflowId])
}
```

**HITL Integration**:
```typescript
// Handle human-in-the-loop prompts
const handleHITLPrompt = async (workflowId: string, response: string) => {
  await fetch(`/api/workflow/${workflowId}/hitl/respond`, {
    method: 'POST',
    body: JSON.stringify({ response })
  })
}
```

---

## 3. Application Architecture

### 3.1 Navigation Structure

```
🏛️ TikTok Geo-Regulation AI System
├── 📋 Requirements Check (Primary - Simple drag & drop)
├── 🏛️ Legal Documents (Secondary - Full legal workflows)  
├── 📚 Document Library (Advanced - Unified document management)
├── 🧠 Knowledge Base (Configuration - Agent customization)
├── 📊 Results History (Reference - Past compliance checks)
└── 🔧 System Info (System - Health and settings)
```

**Implementation**: **5 Separate Pages** optimized for user workflows
- **Requirements Check**: Streamlined for primary use case (80% of usage)
- **Legal Documents**: Complete workflow for legal team power users (20%)
- **Document Library**: Unified management when users need organization
- **Knowledge Base**: Domain expertise customization for better analysis
- **Results History**: Quick access to previous compliance analysis

### 3.2 Layout Framework

```
┌─ Global Navigation ─┬─ Main Content Area ─────────────┬─ HITL Sidebar ─┐
│ 📋 Requirements     │                                 │                │
│ 🏛️ Legal Docs       │                                 │ ┌─ Workflow ─┐ │
│ 📚 Document Library │     Page-Specific Content       │ │ Step 2 of 5 │ │
│ 🧠 Knowledge Base   │                                 │ │ ████░░░ 40% │ │
│ 📊 Results History  │                                 │ └─────────────┘ │
│ 🔧 System           │                                 │                │
└─────────────────────┴─────────────────────────────────┴────────────────┘
```

**Key Features**:
- **Fixed sidebar navigation** (left, 200px width)
- **Main content area** (flexible width, optimized for primary use case)
- **HITL sidebar** (right, 300px width, appears during workflows)
- **Clean separation** between simple and advanced functionality

---

## 3. Page Specifications

### 3.1 Requirements Check (Primary Page)

**Route**: `/` (Landing page)  
**Purpose**: Streamlined requirements PDF compliance checking  
**Target Users**: Product managers, engineers, compliance officers (80% of usage)

#### 3.1.1 Page Layout
```
┌─ Page Header ──────────────────────────────────────────────────────────┐
│ 📋 Requirements Compliance Check                   [Recent] [Help] [⚙️] │
└────────────────────────────────────────────────────────────────────────┘

┌─ Main Drop Zone ───────────────────────────────────────────────────────┐
│                                                                        │
│                         📄 Drop Requirements PDF Here                  │
│                                                                        │
│                    (PRDs, Technical Specs, User Stories)               │
│                                                                        │
│                         or click to select files                       │
│                                                                        │
│     ✨ We'll extract your requirements and check them automatically     │
│        against all legal regulations across jurisdictions              │
│                                                                        │
│ Supported: PDF, DOCX, TXT | Max: 50MB | Processing: ~30 seconds        │
└────────────────────────────────────────────────────────────────────────┘

┌─ Recent Checks ────────────────────────────────────────────────────────┐
│ 🕒 Recent Compliance Checks                                            │
│ • Live Shopping Platform v2.1 - 3 issues found (2 hours ago)          │
│ • Content Safety Technical Spec - All compliant (1 day ago)           │
│ • Payment Flow User Stories - 1 needs review (3 days ago)             │
│                                                           [View All →] │
└────────────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 Upload Flow with Library Prompt

**Step 1: File Upload**
```
User drops/selects PDF → Upload progress → Processing indicator
```

**Step 2: Library Prompt** (Immediate after upload)
```
┌─ Document Uploaded ─────────────────────────────────┐
│ ✅ "Live Shopping Requirements v2.1.pdf" uploaded   │
│                                                     │
│ Add this document to your library for future       │
│ reference and organization?                         │
│                                                     │
│ [Add to Library] [Skip - Just Run Analysis]        │
│                                                     │
│ Note: You can manage documents later in the         │
│ Document Library page                               │
└─────────────────────────────────────────────────────┘
```

**Step 3: Requirements Extraction**
```
Processing... Extracting requirements from document
Found 15 requirements to check for legal compliance
```

**Step 4: HITL Sidebar Appears**
- Sidebar slides in from right
- Shows Workflow 3 progress and lawyer agent prompts
- User guided through compliance decisions

**Step 5: Results**
- Automatic redirect to Results History page
- Show compliance report with actionable issues

#### 3.1.3 Functional Requirements

**Upload Interface**:
- **Large drop zone**: Center of screen, visually prominent
- **Drag & drop**: Visual feedback, multi-file support
- **Progress indication**: File upload and processing status
- **File validation**: Type, size, format checking

**Library Integration**:
- **Immediate prompt**: After successful upload
- **Clear options**: Add or skip with explanations
- **No interruption**: Analysis continues regardless of choice

**Recent Checks**:
- **Quick access**: Last 3-5 compliance checks
- **Status summary**: Issue count and time stamps
- **One-click access**: Direct link to results

### 3.2 Legal Documents (Secondary Page)

**Route**: `/legal-documents`  
**Purpose**: Full legal document workflow for legal team  
**Target Users**: Legal team, compliance specialists (20% of usage)

#### 3.2.1 Page Layout
```
┌─ Page Header ──────────────────────────────────────────────────────────┐
│ 🏛️ Legal Documents Workflow                [Search] [Filter] [Batch ▼] │
└────────────────────────────────────────────────────────────────────────┘

┌─ Upload & Process ─────────────────────────────────────────────────────┐
│ 📤 Upload Legal Documents                                              │
│ ┌─ Drop Zone ─────────────┐  Document Type: [Regulation ▼]            │
│ │ Drag legal docs here    │  Jurisdiction: [Utah ▼]                   │
│ │ (Acts, Regulations,     │  Effective Date: [2025-01-15]             │
│ │  Amendments, Notices)   │                                            │
│ └─────────────────────────┘  [Upload & Process]                       │
└────────────────────────────────────────────────────────────────────────┘

┌─ Recent Legal Documents ───────────────────────────────────────────────┐
│ 📋 Recent Uploads (5 documents)                          [Manage All →] │
│                                                                        │
│ Utah Social Media Act 2025        🔄 Workflow 2: Past iteration found │
│ EU DSA Amendment 2025             ✅ Stored, ready for compliance      │
│ California COPPA Update 2025      🔄 Processing...                     │
│                                                                        │
│ Selected: 2 documents    [🔍 Run Compliance Check] [🗑️ Delete]        │
└────────────────────────────────────────────────────────────────────────┘

┌─ Workflow Actions ─────────────────────────────────────────────────────┐
│ 🔄 Available Workflows                                                 │
│                                                                        │
│ Workflow 1: Check Requirements Compliance                              │
│ • Select legal documents above                                         │
│ • Analysis checks all existing requirements against these laws         │
│ • [Start Workflow 1] (Requires: 1+ legal docs selected)              │
│                                                                        │
│ Workflow 2: Past Iteration Management                                  │
│ • Automatically triggered during upload                                │
│ • Detects and manages outdated law versions                           │
│ • HITL prompts guide deletion decisions                               │
└────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 Workflow Integration

**Upload Process**:
1. **Legal document upload** with metadata (type, jurisdiction, date)
2. **Automatic Workflow 2** (past iteration detection) via HITL sidebar
3. **Storage** and availability for Workflow 1

**Workflow 1 Trigger**:
1. **User selects legal documents** from recent or library
2. **"Run Compliance Check"** button starts Workflow 1
3. **HITL sidebar** guides through analysis
4. **Results** show which requirements are affected

### 3.3 Document Library (Advanced Page)

**Route**: `/document-library`  
**Purpose**: Unified document management and organization  
**Target Users**: Power users who need document organization

#### 3.3.1 Page Layout
```
┌─ Page Header ──────────────────────────────────────────────────────────┐
│ 📚 Document Library                      [Search] [Filter ▼] [Sort ▼] │
└────────────────────────────────────────────────────────────────────────┘

┌─ Library Stats ────────────────────────────────────────────────────────┐
│ 📊 Library Overview: 47 documents (23 requirements, 24 legal)          │
│ Last upload: 2 hours ago | Storage used: 125MB / 1GB                   │
└────────────────────────────────────────────────────────────────────────┘

┌─ Document Table ───────────────────────────────────────────────────────┐
│ ☑️ │ Document Name                │ Type  │ Date    │ Status   │ Actions │
│────┼─────────────────────────────┼───────┼─────────┼──────────┼─────────│
│ ☑️ │ Live Shopping Platform v2.1  │ Req   │ Jan 15  │ Analyzed │ [View]  │
│ ☑️ │ Utah Social Media Act 2025   │ Legal │ Jan 20  │ Stored   │ [View]  │
│ ☑️ │ Content Safety Tech Spec     │ Req   │ Jan 18  │ Pending  │ [View]  │
│ ☑️ │ EU DSA Amendment 2025        │ Legal │ Jan 22  │ Analyzed │ [View]  │
│────┼─────────────────────────────┼───────┼─────────┼──────────┼─────────│
│                                                                        │
│ Selected: 3 documents                                                  │
│ [🔍 Bulk Compliance Check] [🗂️ Move to Folder] [🗑️ Delete] [📤 Export] │
└────────────────────────────────────────────────────────────────────────┘

┌─ Quick Actions ────────────────────────────────────────────────────────┐
│ 🚀 Bulk Operations                                                     │
│ • Check selected requirements against all legal docs                   │
│ • Check selected legal docs against all requirements                   │
│ • Export compliance reports for selected documents                     │
│ • Move documents to organized folders                                  │
└────────────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Advanced Features

**Search & Organization**:
- **Global search**: Document names, content, metadata
- **Advanced filters**: Type, date range, status, jurisdiction
- **Folder organization**: User-created folders and tags
- **Bulk operations**: Multi-select for batch actions

**Integration Actions**:
- **Quick compliance**: Run analysis on selected documents
- **Cross-reference**: Show related documents and analyses
- **Export options**: Reports, summaries, raw data

### 3.4 Knowledge Base (Configuration Page)

**Route**: `/knowledge-base`  
**Purpose**: Customize lawyer agent domain expertise  
**Target Users**: System administrators, domain experts

#### 3.4.1 Page Layout
```
┌─ Page Header ──────────────────────────────────────────────────────────┐
│ 🧠 Agent Knowledge Base                     [Save] [Revert] [Help] [?] │
└────────────────────────────────────────────────────────────────────────┘

┌─ Knowledge Editor ─────────────────────────────────────────────────────┐
│ 📝 Customize Agent Expertise                                           │
│                                                                        │
│ ┌─ Content Editor (Expandable Text Area) ───────────────────────────┐  │
│ │                                                                    │  │
│ │  # TikTok Terminology                                              │  │
│ │  - "Live Shopping" = e-commerce integration during live streams    │  │
│ │  - "Creator Fund" = monetization program for content creators      │  │
│ │  - "For You Page" = personalized recommendation feed               │  │
│ │                                                                    │  │
│ │  # Legal Precedents                                                │  │
│ │  - Utah Social Media Act requires age verification for minor       │  │
│ │    features and 10:30 PM - 6:30 AM curfews                        │  │
│ │  - EU DSA mandates 24-hour content moderation response times       │  │
│ │  - COPPA applies to any feature accessible by users under 13       │  │
│ │                                                                    │  │
│ │  # Compliance Patterns                                             │  │
│ │  - Payment processing → PCI DSS compliance required                │  │
│ │  - User data collection → Privacy policy updates needed            │  │
│ │  - Minor-accessible features → Parental controls mandatory         │  │
│ │                                                                    │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│ 📊 Word count: 1,247 | Characters: 6,183 | Last saved: 2 minutes ago  │
└────────────────────────────────────────────────────────────────────────┘

┌─ Content Templates ────────────────────────────────────────────────────┐
│ 🔧 Quick Add Sections                                                  │
│ [+ TikTok Terminology] [+ Legal Precedents] [+ Compliance Patterns]    │
│ [+ Jurisdiction Guide] [+ Common Violations] [+ Best Practices]        │
└────────────────────────────────────────────────────────────────────────┘

┌─ Impact Preview ───────────────────────────────────────────────────────┐
│ 🔍 How This Enhances Analysis                                          │
│ Your knowledge base is automatically included in every compliance      │
│ analysis to provide TikTok-specific context and improve accuracy.      │
│                                                                        │
│ [Preview Enhanced Prompt] - See how this content improves AI analysis  │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.5 Results History (Reference Page)

**Route**: `/results`  
**Purpose**: Access past compliance analysis results  
**Target Users**: All users needing to reference previous analyses

#### 3.5.1 Page Layout
```
┌─ Page Header ──────────────────────────────────────────────────────────┐
│ 📊 Compliance Analysis History            [Search] [Filter] [Export ▼] │
└────────────────────────────────────────────────────────────────────────┘

┌─ Results Summary ──────────────────────────────────────────────────────┐
│ 📈 Analysis Overview                                                   │
│ Total analyses: 127 | This month: 23 | Issues resolved: 89/94 (95%)   │
│ Average analysis time: 2m 15s | Most common issue: Data retention      │
└────────────────────────────────────────────────────────────────────────┘

┌─ Recent Results ───────────────────────────────────────────────────────┐
│ 🕒 Recent Compliance Checks                                            │
│                                                                        │
│ ┌─ Analysis Result ──────────────────────────────────────────────────┐ │
│ │ 📋 Live Shopping Platform v2.1 → Legal Compliance                  │ │
│ │ Completed: 2 hours ago | Duration: 1m 45s                          │ │
│ │ ❌ 2 non-compliant | ⚠️ 1 needs review | ✅ 12 compliant          │ │
│ │ Key issues: Data retention period, Content response time SLA       │ │
│ │ [View Details] [Export Report] [Mark Issues Resolved]              │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ ┌─ Analysis Result ──────────────────────────────────────────────────┐ │
│ │ 🏛️ EU DSA Amendment 2025 → Requirements Compliance                 │ │
│ │ Completed: 1 day ago | Duration: 3m 22s                            │ │
│ │ ❌ 1 non-compliant | ⚠️ 3 needs review | ✅ 43 compliant          │ │
│ │ Key issues: Age verification methods, Transparency reporting        │ │
│ │ [View Details] [Export Report] [Schedule Follow-up]                │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│                                                            [Load More] │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. HITL Sidebar Specifications (Unchanged)

### 4.1 Cursor-Style Sidebar Design

**Position**: Fixed right sidebar, 300px width, non-overlay  
**Behavior**: Appears during workflow execution, hidden otherwise  
**Activation**: Automatic when workflows start from any page

#### 4.1.1 Sidebar States by Page

**Requirements Check Page**:
- Appears after upload and extraction
- Guides through Workflow 3 (Requirements → Legal Compliance)
- Shows progress and lawyer agent prompts

**Legal Documents Page**:
- Appears during Workflow 1 (Legal → Requirements) and Workflow 2 (Past Iterations)
- Handles past iteration deletion prompts
- Shows compliance analysis progress

**All Pages**:
- Consistent look and behavior
- Maintains conversation history per workflow
- Clear progress indicators and user choices

---

## 5. Implementation Phases

### 5.1 Phase 1: Next.js Foundation + Core Flow (Week 1)

**Frontend Setup**:
- [ ] **Next.js project initialization**: App Router setup with TypeScript
- [ ] **shadcn/ui installation**: Core components (Button, Dialog, Progress, Table)
- [ ] **Tailwind configuration**: shadcn theme setup + custom styles
- [ ] **Project structure**: Components, hooks, lib, stores organization

**Core Primary Flow**:
- [ ] **Requirements Check page**: react-dropzone + library prompt + recent checks
- [ ] **Basic HITL sidebar**: Slide-out panel with shadcn components
- [ ] **Results History page**: shadcn Table for analysis results display
- [ ] **Navigation**: App Router routing between 5 pages

**Backend Minimal Changes**:
- [ ] **HITL endpoints**: `/api/workflow/{id}/hitl/*` for user interactions
- [ ] **SSE endpoint**: `/api/workflow/{id}/progress` for real-time updates
- [ ] **CORS configuration**: Allow frontend (port 3000) → backend (port 8000)

### 5.2 Phase 2: Full Workflow Integration (Week 2)

**Advanced Components**:
- [ ] **DocumentUpload component**: Advanced drag & drop with progress
- [ ] **ComplianceResults component**: Detailed results with shadcn Cards
- [ ] **WorkflowProgress component**: Real-time progress with SSE
- [ ] **DocumentTable component**: shadcn Table with filtering/sorting

**Full Workflow Support**:
- [ ] **Legal Documents page**: Upload + past iteration detection + Workflow 1
- [ ] **Workflow orchestration**: Start/stop workflows via API
- [ ] **HITL state management**: Zustand stores for workflow state
- [ ] **Real-time updates**: SSE integration for all 3 workflows

**MCP Integration**:
- [ ] **API client functions**: FastAPI → MCP service calls
- [ ] **Error handling**: MCP service failures and retries
- [ ] **Document Library page**: Basic table view and search

### 5.3 Phase 3: Advanced Features + Polish (Week 3)

**Advanced Pages**:
- [ ] **Knowledge Base page**: Rich text editor with shadcn Textarea
- [ ] **Advanced DocumentTable**: Search, filtering, bulk operations
- [ ] **Results visualization**: Charts and graphs for compliance trends

**Production Polish**:
- [ ] **Loading states**: Skeleton components and spinners
- [ ] **Error boundaries**: Graceful error handling and recovery
- [ ] **Performance optimization**: Code splitting and caching
- [ ] **Responsive design**: Mobile-friendly layouts and interactions

**Docker Integration**:
- [ ] **Frontend Dockerfile**: Optimized Next.js container
- [ ] **Docker-compose update**: Frontend service + existing backend/services
- [ ] **Production build**: Optimized static generation where possible

---

## 5.4 Development Environment Setup

**Prerequisites**:
```bash
# Node.js 18+ for Next.js
node --version  # Should be 18+
npm --version   # or yarn/pnpm

# Docker for containerization
docker --version
docker-compose --version
```

**Quick Start Commands**:
```bash
# 1. Initialize Next.js frontend
cd techjam-jamming/
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# 2. Install shadcn/ui
cd frontend/
npx shadcn-ui@latest init

# 3. Add required shadcn components
npx shadcn-ui@latest add button dialog table progress card input textarea

# 4. Install additional dependencies
npm install zustand react-dropzone

# 5. Update docker-compose.yml (add frontend service)
# 6. Start development environment
cd ../
docker-compose up -d postgres redis  # Start backend services
npm run dev --prefix frontend        # Start frontend dev server
python -m src.main                   # Start FastAPI backend
```

---

## 6. Success Criteria

### 6.1 Primary Use Case Success
- [ ] **80% user flow**: Drop PDF → Analysis → Results in under 3 clicks
- [ ] **Library integration**: Clear prompt with non-disruptive workflow
- [ ] **HITL efficiency**: Sidebar prompts don't interrupt main workflow
- [ ] **Results accessibility**: Easy access to past analyses and export options

### 6.2 Secondary Use Case Success  
- [ ] **Legal workflow**: Complete document management with past iteration handling
- [ ] **Power user features**: Document library with search, filter, bulk operations
- [ ] **Knowledge base**: Domain expertise customization improves analysis quality

### 6.3 Technical Success
- [ ] **Performance**: Requirements check completes in under 30 seconds
- [ ] **Real-time updates**: SSE provides smooth progress updates without polling
- [ ] **HITL reliability**: Sidebar maintains state during interruptions and browser refresh
- [ ] **MCP integration**: All workflows connect properly with Legal/Requirements MCP services
- [ ] **Modern UX**: shadcn/ui provides professional, accessible interface
- [ ] **Responsive design**: Works properly on desktop screens 1200px+
- [ ] **Docker deployment**: Frontend + backend containers work together seamlessly

---

*This TRD defines a modern Next.js + shadcn/ui implementation that replaces Streamlit with a professional, scalable frontend. The architecture prioritizes the primary use case (requirements PDF compliance checking) while maintaining full functionality for legal team workflows and document management power users.*

---

## 7. Backend Changes Required

### 7.1 New API Endpoints

**HITL Management**:
```python
# In src/api/endpoints/hitl.py (new file)
@router.post("/workflow/{workflow_id}/start")
async def start_workflow(workflow_id: str, workflow_type: str, document_id: str):
    """Start a TRD workflow with web-friendly HITL integration"""

@router.get("/workflow/{workflow_id}/progress")  
async def workflow_progress_stream(workflow_id: str):
    """SSE stream for real-time progress updates"""

@router.post("/workflow/{workflow_id}/hitl/respond")
async def respond_to_hitl(workflow_id: str, response: HITLResponse):
    """Handle user response from HITL sidebar"""

@router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get current workflow state and any pending HITL prompts"""
```

**Document Management**:
```python  
# In src/api/endpoints/documents.py (enhanced)
@router.post("/documents/upload")
async def upload_document(file: UploadFile, doc_type: str, metadata: Dict):
    """Upload document with immediate library prompt response"""

@router.get("/documents/recent")
async def get_recent_uploads(limit: int = 5):
    """Get recent uploads for landing page display"""
```

### 7.2 Models Updates

**New Pydantic Models**:
```python
# In src/core/models.py (additions)
class WorkflowState(BaseModel):
    workflow_id: str
    workflow_type: str  # "workflow_1", "workflow_2", "workflow_3"
    status: str  # "running", "waiting_hitl", "complete", "error"
    current_step: int
    total_steps: int
    progress_message: str

class HITLPrompt(BaseModel):
    prompt_id: str
    prompt_type: str  # "compliance_clarification", "past_iteration_decision"
    question: str
    options: List[str]
    context: Dict[str, Any]

class HITLResponse(BaseModel):
    prompt_id: str
    response: str
    timestamp: datetime
```

### 7.3 Workflow Integration

**Modified TRD Agent Integration**:
```python
# Enhanced lawyer_trd_agent.py integration
class WebFriendlyLawyerTRDAgent(LawyerTRDAgent):
    """Web-friendly version with SSE and async HITL"""
    
    async def workflow_3_web(
        self, 
        requirements_document_id: str,
        workflow_id: str,
        progress_callback: Callable,
        hitl_callback: Callable
    ) -> RequirementsComplianceReport:
        """Web-optimized Workflow 3 with SSE progress and async HITL"""
        
        # Send progress updates via SSE
        await progress_callback(workflow_id, {
            "step": 1,
            "message": "Extracting requirements from document...",
            "progress": 20
        })
        
        # Async HITL - store prompt and wait for response
        await hitl_callback(workflow_id, {
            "type": "compliance_clarification",
            "question": "This requirement may conflict with EU regulation...",
            "options": ["COMPLIANT", "NON-COMPLIANT", "NEEDS-REVIEW"]
        })
```

This architecture provides a **professional, scalable foundation** for the compliance platform while maintaining compatibility with existing MCP services and backend infrastructure.