-- Create law regulations table for each location

-- file location: 
-- statute: "EU_DSA" || "UTAH_SB976"
-- law_id: "Article_28" || "Section 27000"
-- regulations: "Very large online platforms that are likely to be accessed by minors shall..."}

CREATE TABLE IF NOT EXISTS techjam.t_law_{{region}}_regulations (
    file_location VARCHAR(255),
    statute VARCHAR(255), 
    law_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    regulations VARCHAR(255)
);

-- Create law definitions table for each location
CREATE TABLE IF NOT EXISTS techjam.t_law_{{region}}_definitions (
    file_location VARCHAR(255),
    region VARCHAR(255),
    statute VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    definitions VARCHAR(255)
);

-- Create PRD table for all PRDs
CREATE TABLE IF NOT EXISTS techjam.t_prd (
    file_location VARCHAR(255),
    feature VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    relevant_laws VARCHAR(255)
)