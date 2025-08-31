# Archived: Streamlit UI Components

**Status**: Archived - Replaced by Next.js frontend

This directory contains the legacy Streamlit UI components that were replaced by the professional Next.js + shadcn/ui frontend.

## Why Archived?

- **Modern Alternative**: Next.js frontend provides superior UX
- **Professional Design**: shadcn/ui components vs basic Streamlit
- **Real-time Features**: SSE integration for workflow progress
- **Docker Optimization**: Reduced container complexity
- **Maintenance**: Single frontend to maintain

## What Was Here?

- `src/ui/app.py` - Main Streamlit application
- `src/ui/components/` - Various Streamlit components
- `src/ui/utils/` - Utility functions

## Migration Path

All functionality has been reimplemented in:
- `frontend/` - Next.js application with professional UI
- Modern workflows with HITL sidebar
- Document management with drag & drop
- Real-time progress tracking

The legacy endpoints in the FastAPI backend remain functional for backward compatibility.