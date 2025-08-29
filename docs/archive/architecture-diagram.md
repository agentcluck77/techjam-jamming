```mermaid
graph TB
    %% Input Layer
    Start([Start]) --> Input[Input: PRD/TRD/Query<br/>Feature Description<br/>Geographic Context]
    
    %% Orchestrator Agent (Main Controller)
    Input --> Orchestrator[Orchestrator Agent<br/>- Route based on input type<br/>- Manage workflow state<br/>- Aggregate responses]
    
    %% JSON Refactorer (Context Enrichment)
    Orchestrator --> JSONRefactor[JSON-Refactorer LLM<br/>- Expand internal jargon<br/>- Add missing context<br/>- Geographic inference<br/>- Document parsing]
    
    %% Parallel Law MCP Analysis
    JSONRefactor --> LawyerAgent[Lawyer Agent<br/>Central Coordinator]
    
    LawyerAgent --> UtahMCP[Utah Law MCP<br/>Social Media Regulation Act<br/>Age verification & curfews]
    LawyerAgent --> BrazilMCP[Brazil Law MCP<br/>Data localization<br/>LGPD compliance]
    LawyerAgent --> EUMCP[EU Law MCP<br/>Digital Service Act<br/>Content moderation]
    LawyerAgent --> FloridaMCP[Florida Law MCP<br/>Online Protections for Minors<br/>Parental controls]
    LawyerAgent --> CaliforniaMCP[California Law MCP<br/>COPPA compliance<br/>Child protection]
    
    %% Aggregation and Decision
    UtahMCP --> LawyerAgent
    BrazilMCP --> LawyerAgent  
    EUMCP --> LawyerAgent
    FloridaMCP --> LawyerAgent
    CaliforniaMCP --> LawyerAgent
    
    %% Decision Logic in Lawyer Agent
    LawyerAgent --> Decision{Any Compliance<br/>Requirements Found?}
    
    %% Output Paths
    Decision -->|YES| ComplianceOutput[Compliance Required Output<br/>- Applicable regulations<br/>- Risk level<br/>- Required actions<br/>- Implementation steps]
    
    Decision -->|NO| NoComplianceOutput[No Compliance Required<br/>- Reasoning<br/>- Confidence score<br/>- Business vs legal distinction]
    
    ComplianceOutput --> End([End: Return Table/Advice])
    NoComplianceOutput --> End
    
    %% Handle User Queries (Different Path)
    Orchestrator --> UserQuery{Is this a<br/>User Query?}
    UserQuery -->|YES| DirectToLawyer[Skip JSON Refactoring<br/>Go directly to Lawyer Agent]
    UserQuery -->|NO| JSONRefactor
    DirectToLawyer --> LawyerAgent
    
    %% Supporting Services Layer
    subgraph "Supporting Services"
        LLMRouter[LLM Service Router<br/>- Claude Sonnet 4<br/>- GPT-4 fallback<br/>- Load balancing]
        
        CacheLayer[Cache Layer<br/>- Redis cache<br/>- Feature similarity<br/>- Regulation lookups]
        
        DatabaseLayer[Database Layer<br/>- PostgreSQL<br/>- Analysis history<br/>- Audit trails]
        
        MetricsService[Metrics & Monitoring<br/>- Performance tracking<br/>- Accuracy measurement<br/>- Error handling]
    end
    
    %% All agents use supporting services
    JSONRefactor -.-> LLMRouter
    LawyerAgent -.-> LLMRouter
    UtahMCP -.-> LLMRouter
    BrazilMCP -.-> LLMRouter
    EUMCP -.-> LLMRouter
    FloridaMCP -.-> LLMRouter
    CaliforniaMCP -.-> LLMRouter
    
    LawyerAgent -.-> CacheLayer
    LawyerAgent -.-> DatabaseLayer
    Orchestrator -.-> MetricsService
    
    %% API Layer
    subgraph "API & UI Layer"
        FastAPI[FastAPI Endpoints<br/>POST /analyze-feature<br/>POST /batch-analyze<br/>GET /health]
        StreamlitUI[Streamlit Demo UI<br/>Interactive testing<br/>Batch upload<br/>Results visualization]
    end
    
    FastAPI --> Input
    StreamlitUI --> FastAPI
    
    %% Styling
    classDef agent fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef database fill:#f3e5f5,stroke:#4a148c,stroke-width:2px  
    classDef llm fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef decision fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class Orchestrator,JSONRefactor,LawyerAgent agent
    class UtahMCP,BrazilMCP,EUMCP,FloridaMCP,CaliforniaMCP llm
    class Decision,UserQuery decision
    class ComplianceOutput,NoComplianceOutput,End output```