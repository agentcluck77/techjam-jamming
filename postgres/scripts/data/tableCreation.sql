-- Create law regulations table for each location
CREATE TABLE IF NOT EXISTS techjam.t_law_{{table_name}}_regulations (
    pdf_path VARCHAR(255),
    law_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    regulations VARCHAR(255)
);

-- Create law definitions table for each location
CREATE TABLE IF NOT EXISTS techjam.t_law_{{table_name}}_definitions (
    pdf_path VARCHAR(255),
    law_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    definitions VARCHAR(255)
);

-- Create PRD table for all PRDs
CREATE TABLE IF NOT EXISTS techjam.t_prd (
    pdf_path VARCHAR(255),
    feature VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    relevant_laws VARCHAR(255)
)