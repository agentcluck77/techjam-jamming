-- Legal MCP Vector Search Migration
-- Add pgvector support to existing legal document tables

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add vector columns to regulations tables for all regions
-- Note: This assumes your regions are already created. 
-- You may need to run this for each specific region table.

-- For now, let's create a generic template that can be applied to each region
-- You'll need to replace {{region}} with actual region names like 'eu', 'utah', 'california', etc.

-- Add embedding column to regulations table (1536 dimensions for all-MiniLM-L6-v2)
-- Uncomment and modify for each region:

-- ALTER TABLE techjam.t_law_{{region}}_regulations 
-- ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Add index for vector similarity search
-- CREATE INDEX IF NOT EXISTS idx_{{region}}_regulations_embedding 
-- ON techjam.t_law_{{region}}_regulations USING ivfflat (embedding vector_cosine_ops);

-- Add embedding column to definitions table 
-- ALTER TABLE techjam.t_law_{{region}}_definitions 
-- ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Add index for vector similarity search on definitions
-- CREATE INDEX IF NOT EXISTS idx_{{region}}_definitions_embedding 
-- ON techjam.t_law_{{region}}_definitions USING ivfflat (embedding vector_cosine_ops);

-- Example for specific regions (uncomment and run for your actual regions):

-- EU region
ALTER TABLE techjam.t_law_eu_regulations 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_eu_regulations_embedding 
ON techjam.t_law_eu_regulations USING ivfflat (embedding vector_cosine_ops);

ALTER TABLE techjam.t_law_eu_definitions 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_eu_definitions_embedding 
ON techjam.t_law_eu_definitions USING ivfflat (embedding vector_cosine_ops);

-- Utah region  
ALTER TABLE techjam.t_law_utah_regulations 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_utah_regulations_embedding 
ON techjam.t_law_utah_regulations USING ivfflat (embedding vector_cosine_ops);

ALTER TABLE techjam.t_law_utah_definitions 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_utah_definitions_embedding 
ON techjam.t_law_utah_definitions USING ivfflat (embedding vector_cosine_ops);

-- California region
ALTER TABLE techjam.t_law_california_regulations 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_california_regulations_embedding 
ON techjam.t_law_california_regulations USING ivfflat (embedding vector_cosine_ops);

ALTER TABLE techjam.t_law_california_definitions 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_california_definitions_embedding 
ON techjam.t_law_california_definitions USING ivfflat (embedding vector_cosine_ops);

-- Florida region
ALTER TABLE techjam.t_law_florida_regulations 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_florida_regulations_embedding 
ON techjam.t_law_florida_regulations USING ivfflat (embedding vector_cosine_ops);

ALTER TABLE techjam.t_law_florida_definitions 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_florida_definitions_embedding 
ON techjam.t_law_florida_definitions USING ivfflat (embedding vector_cosine_ops);

-- Brazil region
ALTER TABLE techjam.t_law_brazil_regulations 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_brazil_regulations_embedding 
ON techjam.t_law_brazil_regulations USING ivfflat (embedding vector_cosine_ops);

ALTER TABLE techjam.t_law_brazil_definitions 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_brazil_definitions_embedding 
ON techjam.t_law_brazil_definitions USING ivfflat (embedding vector_cosine_ops);

-- Add metadata columns for tracking embeddings
ALTER TABLE techjam.t_law_eu_regulations 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE techjam.t_law_utah_regulations 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE techjam.t_law_california_regulations 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE techjam.t_law_florida_regulations 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE techjam.t_law_brazil_regulations 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

-- Same for definitions tables
ALTER TABLE techjam.t_law_eu_definitions 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE techjam.t_law_utah_definitions 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE techjam.t_law_california_definitions 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE techjam.t_law_florida_definitions 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE techjam.t_law_brazil_definitions 
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMPTZ DEFAULT NULL;

-- Create function to update embeddings when text content changes
CREATE OR REPLACE FUNCTION update_embedding_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    -- Reset embedding timestamp when regulations text is updated
    IF TG_OP = 'UPDATE' AND OLD.regulations IS DISTINCT FROM NEW.regulations THEN
        NEW.embedding_created_at = NULL;
    END IF;
    -- Reset embedding timestamp when definitions text is updated  
    IF TG_OP = 'UPDATE' AND OLD.definitions IS DISTINCT FROM NEW.definitions THEN
        NEW.embedding_created_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers to reset embedding timestamps when content changes
-- (This helps us know when we need to regenerate embeddings)

-- Regulations tables
CREATE TRIGGER update_embedding_timestamp_eu_regulations
    BEFORE UPDATE ON techjam.t_law_eu_regulations
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_embedding_timestamp_utah_regulations
    BEFORE UPDATE ON techjam.t_law_utah_regulations
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_embedding_timestamp_california_regulations
    BEFORE UPDATE ON techjam.t_law_california_regulations
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_embedding_timestamp_florida_regulations
    BEFORE UPDATE ON techjam.t_law_florida_regulations
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_embedding_timestamp_brazil_regulations
    BEFORE UPDATE ON techjam.t_law_brazil_regulations
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();

-- Definitions tables  
CREATE TRIGGER update_embedding_timestamp_eu_definitions
    BEFORE UPDATE ON techjam.t_law_eu_definitions
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_embedding_timestamp_utah_definitions
    BEFORE UPDATE ON techjam.t_law_utah_definitions
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_embedding_timestamp_california_definitions
    BEFORE UPDATE ON techjam.t_law_california_definitions
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_embedding_timestamp_florida_definitions
    BEFORE UPDATE ON techjam.t_law_florida_definitions
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_embedding_timestamp_brazil_definitions
    BEFORE UPDATE ON techjam.t_law_brazil_definitions
    FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp();