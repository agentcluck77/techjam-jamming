-- Requirements MCP Database Schema
-- Tables for document storage and processing logs

CREATE TABLE IF NOT EXISTS pdfs (
    id VARCHAR(255) PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) DEFAULT 'prd',
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending',
    content TEXT,
    processing_details JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processing_log (
    id SERIAL PRIMARY KEY,
    pdf_id VARCHAR(255) REFERENCES pdfs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_content TEXT NOT NULL,
    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_pdfs_upload_date ON pdfs(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_pdfs_status ON pdfs(processing_status);
CREATE INDEX IF NOT EXISTS idx_pdfs_file_type ON pdfs(file_type);
CREATE INDEX IF NOT EXISTS idx_processing_log_pdf_id ON processing_log(pdf_id);
CREATE INDEX IF NOT EXISTS idx_processing_log_chunk_index ON processing_log(chunk_index);

-- Insert sample documents for testing
INSERT INTO pdfs (id, filename, file_type, upload_date, processing_status, content, metadata) 
VALUES (
    'sample-prd-001',
    'TikTok_Creator_Studio_v2.1_Live_Shopping.md',
    'prd',
    CURRENT_TIMESTAMP,
    'completed',
    'Live Shopping Platform Requirements
    
    # Overview
    This document outlines the requirements for TikTok Creator Studio v2.1 Live Shopping features.
    
    ## Core Features
    - Real-time payment processing with multiple currencies
    - Age verification for purchases under 18 years
    - Inventory management with real-time synchronization
    - Content creator commission tracking
    - Viewer engagement metrics during live shopping sessions
    
    ## Compliance Requirements
    - GDPR compliance for EU users data retention (max 180 days)
    - California CCPA privacy requirements
    - Utah Social Media Act age verification
    - Payment Card Industry (PCI) compliance
    
    ## Technical Requirements
    - 99.9% uptime during live sessions
    - Sub-second payment processing latency
    - Support for 50,000+ concurrent viewers
    - Multi-language support (English, Spanish, French, German, Chinese)',
    '{"sample_document": true, "version": "2.1", "team": "Creator Platform"}'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO processing_log (pdf_id, chunk_index, chunk_content, metadata)
VALUES 
    ('sample-prd-001', 0, 'Live Shopping Platform Requirements - Real-time payment processing with multiple currencies, age verification for purchases under 18 years, inventory management with real-time synchronization', '{"sample_chunk": true}'),
    ('sample-prd-001', 1, 'Compliance Requirements - GDPR compliance for EU users data retention (max 180 days), California CCPA privacy requirements, Utah Social Media Act age verification, Payment Card Industry (PCI) compliance', '{"sample_chunk": true}'),
    ('sample-prd-001', 2, 'Technical Requirements - 99.9% uptime during live sessions, Sub-second payment processing latency, Support for 50,000+ concurrent viewers, Multi-language support', '{"sample_chunk": true}')
ON CONFLICT DO NOTHING;