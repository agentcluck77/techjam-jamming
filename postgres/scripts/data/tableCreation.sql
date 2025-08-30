-- Create law regulations table for each location

-- file location: 
-- statute: "EU_DSA" || "UTAH_SB976"
-- law_id: "Article_28" || "Section 27000"
-- regulations: "Very large online platforms that are likely to be accessed by minors shall..."}

CREATE TABLE IF NOT EXISTS techjam.t_law_{{region}}_regulations (
    file_location TEXT,
    statute TEXT, 
    law_id TEXT,
    regulations TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT unique_law_id_{{region}} UNIQUE (law_id)
);

-- Create law definitions table for each location
CREATE TABLE IF NOT EXISTS techjam.t_law_{{region}}_definitions (
    file_location TEXT,
    region TEXT,
    statute TEXT,
    definitions TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT unique_statute_{{region}} UNIQUE (statute, region)
);

-- Create PRD table for all PRDs
CREATE TABLE IF NOT EXISTS techjam.t_prd (
    file_location TEXT,
    feature TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    relevant_laws TEXT
)