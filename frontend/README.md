# TikTok Geo-Regulation AI System - Frontend

A professional Next.js + shadcn/ui frontend for the TRD Compliance Workflows, implementing a streamlined compliance analysis platform.

## Features

- **Professional UI**: Built with Next.js 14+ and shadcn/ui components
- **5 Core Pages**: Requirements Check, Legal Documents, Document Library, Knowledge Base, Results History
- **Real-time Updates**: Server-Sent Events (SSE) for workflow progress
- **HITL Integration**: Cursor-style sidebar for human-in-the-loop interactions
- **Document Management**: Drag & drop upload with progress tracking
- **Responsive Design**: Desktop-optimized professional interface

## Tech Stack

- **Framework**: Next.js 14+ with App Router
- **UI Library**: shadcn/ui (Radix UI + Tailwind CSS)
- **State Management**: Zustand
- **File Upload**: react-dropzone
- **TypeScript**: Full type safety
- **Containerization**: Docker for deployment

## Quick Start

### Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

### Production Build

```bash
npm run build
npm start
```

### Docker

```bash
docker build -t tiktok-compliance-frontend .
docker run -p 3000:3000 tiktok-compliance-frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx                   # "/" - Requirements Check
│   │   ├── legal-documents/           # "/legal-documents"
│   │   ├── document-library/          # "/document-library"
│   │   ├── knowledge-base/            # "/knowledge-base"
│   │   └── results/                   # "/results"
│   ├── components/
│   │   ├── ui/                        # shadcn/ui components
│   │   ├── HITLSidebar.tsx           # Cursor-style sidebar
│   │   ├── DocumentUpload.tsx         # Drag & drop upload
│   │   └── Navigation.tsx             # App navigation
│   ├── lib/
│   │   ├── api.ts                     # FastAPI client functions
│   │   ├── stores.ts                  # Zustand stores
│   │   ├── types.ts                   # TypeScript types
│   │   └── utils.ts                   # shadcn utilities
│   └── hooks/
│       ├── use-workflow.ts            # Workflow state management
│       ├── use-hitl.ts                # HITL interactions
│       └── use-sse.ts                 # Server-Sent Events
```

## Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API URL
```

## API Integration

The frontend connects to the FastAPI backend via:

- **Document Management**: `/api/documents/*`
- **Workflow Control**: `/api/workflow/*`
- **Results**: `/api/results/*`
- **Mock MCPs**: `/api/v1/legal/*` and `/api/v1/requirements/*`

## Key Features

### 1. Requirements Check (Primary Flow)
- Large drag & drop area for PDF upload
- Automatic requirements extraction
- HITL sidebar for compliance decisions
- Library integration prompt

### 2. Legal Documents
- Legal document upload with metadata
- Workflow 1 & 2 integration
- Past iteration detection

### 3. Document Library
- Unified document management
- Advanced filtering and search
- Bulk operations

### 4. Knowledge Base
- Rich text editor for agent customization
- Template insertion
- Real-time content preview

### 5. Results History
- Compliance analysis history
- Detailed issue tracking
- Export capabilities

## Development Notes

- Built with TypeScript for type safety
- Uses ESLint with relaxed rules for development
- Implements proper error handling and loading states
- Optimized for desktop professional use
- Ready for Docker deployment

## Production Deployment

The application is configured for production deployment with:

- Docker multi-stage build
- Standalone output for minimal container size
- Health checks and proper error handling
- Environment-based configuration

## Next Steps

1. Replace mock MCP endpoints with real MCP services
2. Add comprehensive error boundaries
3. Implement offline support
4. Add comprehensive testing suite
5. Performance optimization for large document sets
