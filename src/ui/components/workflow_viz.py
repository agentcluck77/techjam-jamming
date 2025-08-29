"""
Workflow Visualization Component for Streamlit UI
Dynamic visualization of LangGraph workflow with Mermaid diagrams and system architecture
"""
import streamlit as st
import io
import base64
from typing import Dict, Any, Optional
from src.core.workflow import EnhancedWorkflowOrchestrator

# Always use HTML fallback as default - Mermaid option removed as requested
MERMAID_AVAILABLE = False
st_mermaid = None

def render_mermaid_html(mermaid_code: str, height: str = "500px") -> str:
    """Generate HTML for rendering Mermaid diagrams as fallback"""
    return f"""
    <div id="mermaid-diagram" style="height: {height}; border: 1px solid #ddd; padding: 10px;">
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        <div class="mermaid">
            {mermaid_code}
        </div>
    </div>
    """

class WorkflowVisualizer:
    """
    Dynamic workflow visualization component that adapts to code changes
    """
    
    def __init__(self):
        self.orchestrator = EnhancedWorkflowOrchestrator()
        self._node_descriptions = {
            "smart_router": {
                "name": "Smart Input Router",
                "purpose": "Automatically detect input type and route to appropriate processing path",
                "description": "Uses Python logic to classify feature descriptions, user queries, and PDF documents without LLM overhead",
                "color": "#FFE0B2"  # Light orange
            },
            "json_refactorer": {
                "name": "Enhanced JSON Refactorer Agent",
                "purpose": "Transform TikTok jargon with completeness validation and retry logic",
                "description": "Expands abbreviations, adds geographic implications, validates completeness, and retries up to 2 times if analysis is incomplete",
                "color": "#E3F2FD"  # Light blue
            },
            "legal_analysis": {
                "name": "Legal Analysis Engine", 
                "purpose": "Coordinate analysis across multiple jurisdiction MCPs",
                "description": "Manages parallel analysis across Utah, EU, California, Florida, and Brazil MCPs for compliance decisions",
                "color": "#F3E5F5"  # Light purple
            },
            "decision_synthesis": {
                "name": "Decision Synthesis Agent",
                "purpose": "Aggregate MCP results into final compliance decision",
                "description": "Synthesizes jurisdiction-specific analyses into comprehensive compliance requirements with risk scoring",
                "color": "#E8F5E8"  # Light green
            },
            "query_handler": {
                "name": "Dual-Mode Query Handler",
                "purpose": "Process user questions with MCP search + LLM advisory responses",
                "description": "Searches legal databases across all jurisdictions and generates contextual advisory responses using LLM synthesis",
                "color": "#F1F8E9"  # Light light green
            },
            "pdf_processor": {
                "name": "PDF Document Processor",
                "purpose": "Extract and analyze legal requirements from PDF documents",
                "description": "Placeholder for Team Member 3 - will extract feature specifications from PDF uploads and route to compliance analysis",
                "color": "#FAFAFA"  # Light gray
            }
        }
        
    def render_workflow_page(self):
        """Render the complete workflow visualization page"""
        st.header("🔄 Workflow Visualization")
        st.markdown("*Dynamic system workflow and architecture diagrams*")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "🌊 Workflow Diagram", 
            "🏗️ System Architecture", 
            "🤖 Agent Interactions",
            "📚 Legend & Docs"
        ])
        
        with tab1:
            self._render_workflow_diagram()
            
        with tab2:
            self._render_system_architecture()
            
        with tab3:
            self._render_agent_interactions()
            
        with tab4:
            self._render_legend_and_docs()
    
    def _render_workflow_diagram(self):
        """Render the main LangGraph workflow diagram"""
        st.subheader("📊 LangGraph Workflow Structure")
        st.markdown("This diagram shows the current execution flow and is **automatically updated** when code changes.")
        
        # Get the current workflow graph
        try:
            # Use feature workflow as the main workflow for visualization
            workflow_graph = self.orchestrator.feature_workflow.get_graph()
            
            # Generate Mermaid diagram
            mermaid_code = self._generate_mermaid_diagram(workflow_graph)
            
            # Display options - HTML fallback as default
            viz_options = ["HTML Diagram", "PNG Image", "ASCII Text"]
                
            viz_type = st.radio(
                "Visualization Type:",
                viz_options,
                horizontal=True
            )
            
            if viz_type == "HTML Diagram":
                st.components.v1.html(render_mermaid_html(mermaid_code), height=550)
                
            elif viz_type == "PNG Image":
                self._render_png_diagram(workflow_graph)
                
            elif viz_type == "ASCII Text":
                self._render_ascii_diagram(workflow_graph)
                
            # Show raw Mermaid code in expander
            with st.expander("📋 View Mermaid Code", expanded=False):
                st.code(mermaid_code, language="mermaid")
                
        except Exception as e:
            st.error(f"Failed to generate workflow diagram: {str(e)}")
            st.info("This may happen if the workflow structure has changed. Please restart the application.")
    
    def _generate_mermaid_diagram(self, graph) -> str:
        """Generate Mermaid diagram code from LangGraph"""
        try:
            # Try to use built-in Mermaid generation if available
            if hasattr(graph, 'draw_mermaid'):
                return graph.draw_mermaid()
        except:
            pass
            
        # Enhanced workflow diagram showing smart routing
        mermaid_lines = [
            "graph TD",
            "    %% Enhanced TikTok Geo-Regulation AI Workflow with Smart Routing",
            "    START([🚀 Start]) --> router{🔀 Smart Router<br/>Input Type Detection}",
            "",
            "    %% Feature Analysis Path",
            "    router -->|Feature Description| json_refactorer[📝 JSON Refactorer<br/>Transform TikTok jargon<br/>Completeness validation<br/>with retry logic]",
            "    json_refactorer --> legal_analysis[⚖️ Legal Analysis<br/>Coordinate MCP analysis<br/>across jurisdictions]",
            "    legal_analysis --> decision_synthesis[🎯 Decision Synthesis<br/>Aggregate results into<br/>compliance decision]",
            "    decision_synthesis --> END_FEATURE([✅ Compliance Analysis<br/>Complete])",
            "",
            "    %% User Query Path", 
            "    router -->|User Query| query_handler[🤖 Query Handler<br/>MCP Search + LLM<br/>Advisory responses]",
            "    query_handler --> END_QUERY([💡 Advisory Response<br/>Complete])",
            "",
            "    %% PDF Path (Placeholder)",
            "    router -->|PDF Document| pdf_placeholder[📄 PDF Processor<br/>Team Member 3<br/>Implementation pending]",
            "    pdf_placeholder --> END_PDF([📋 PDF Analysis<br/>Not implemented])",
            "",
            "    %% Styling",
            "    classDef router fill:#FFE0B2,stroke:#FF9800,stroke-width:3px",
            "    classDef refactorer fill:#E3F2FD,stroke:#1976D2,stroke-width:2px",
            "    classDef analysis fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px", 
            "    classDef synthesis fill:#E8F5E8,stroke:#388E3C,stroke-width:2px",
            "    classDef query fill:#F1F8E9,stroke:#689F38,stroke-width:2px",
            "    classDef placeholder fill:#FAFAFA,stroke:#9E9E9E,stroke-width:2px,stroke-dasharray: 5 5",
            "    classDef terminal fill:#FFF3E0,stroke:#F57C00,stroke-width:2px",
            "",
            "    class router router",
            "    class json_refactorer refactorer",
            "    class legal_analysis analysis",
            "    class decision_synthesis synthesis",
            "    class query_handler query", 
            "    class pdf_placeholder placeholder",
            "    class START,END_FEATURE,END_QUERY,END_PDF terminal"
        ]
        
        return "\\n".join(mermaid_lines)
    
    def _render_png_diagram(self, graph):
        """Render PNG version of the workflow diagram"""
        try:
            # Try built-in PNG generation
            if hasattr(graph, 'draw_png'):
                png_data = graph.draw_png()
                if png_data:
                    st.image(png_data, caption="Workflow PNG Diagram")
                    return
                    
            # Fallback message
            st.info("PNG generation requires additional dependencies (graphviz). Using HTML diagram instead.")
            mermaid_code = self._generate_mermaid_diagram(graph)
            st.components.v1.html(render_mermaid_html(mermaid_code, "450px"), height=500)
            
        except Exception as e:
            st.warning(f"PNG generation failed: {str(e)}. Showing HTML diagram instead.")
            mermaid_code = self._generate_mermaid_diagram(graph)
            st.components.v1.html(render_mermaid_html(mermaid_code, "450px"), height=500)
    
    def _render_ascii_diagram(self, graph):
        """Render ASCII text version of the workflow"""
        try:
            if hasattr(graph, 'draw_ascii'):
                ascii_diagram = graph.draw_ascii()
                st.text(ascii_diagram)
            else:
                # Fallback ASCII representation
                ascii_art = """
    ┌─────────────┐
    │    START    │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ JSON        │
    │ Refactorer  │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Legal       │
    │ Analysis    │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Decision    │
    │ Synthesis   │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │     END     │
    └─────────────┘
                """
                st.text(ascii_art)
                
        except Exception as e:
            st.error(f"ASCII generation failed: {str(e)}")
    
    def _render_system_architecture(self):
        """Render high-level system architecture diagram"""
        st.subheader("🏗️ System Architecture Overview")
        st.markdown("High-level view of the complete TikTok Geo-Regulation AI System")
        
        architecture_mermaid = """
graph TB
    subgraph "Frontend Layer"
        UI[🖥️ Streamlit UI<br/>Interactive Demo Interface]
        API_DOCS[📚 FastAPI Docs<br/>Interactive API Documentation]
    end
    
    subgraph "API Layer" 
        FASTAPI[🚀 FastAPI Backend<br/>REST API & Business Logic]
        HEALTH[💚 Health Checks<br/>System Status Monitoring]
    end
    
    subgraph "Core Processing Engine"
        WORKFLOW[🔄 LangGraph Orchestrator<br/>Workflow Management]
        JSON_REF[📝 JSON Refactorer Agent<br/>Terminology Enhancement]
        LAWYER[⚖️ Lawyer Agent<br/>Decision Coordination]
    end
    
    subgraph "Multi-Jurisdiction MCPs"
        UTAH[🏔️ Utah MCP<br/>Social Media Regulation Act]
        EU[🇪🇺 EU MCP<br/>Digital Services Act]
        CA[🌴 California MCP<br/>COPPA & Privacy Laws]
        FL[🌊 Florida MCP<br/>Minor Protection Act]
        BR[🇧🇷 Brazil MCP<br/>LGPD & Data Localization]
    end
    
    subgraph "Data Layer"
        POSTGRES[(🐘 PostgreSQL<br/>Analysis History & Audit)]
        REDIS[(🔴 Redis<br/>Caching & Performance)]
    end
    
    subgraph "External Services"
        CLAUDE[🤖 Claude Sonnet 4<br/>Primary LLM]
        GPT[🧠 GPT-4<br/>Fallback LLM]
        GEMINI[💎 Google Gemini<br/>Optional LLM]
    end
    
    %% Connections
    UI --> FASTAPI
    API_DOCS --> FASTAPI
    FASTAPI --> WORKFLOW
    FASTAPI --> HEALTH
    WORKFLOW --> JSON_REF
    WORKFLOW --> LAWYER
    LAWYER --> UTAH
    LAWYER --> EU  
    LAWYER --> CA
    LAWYER --> FL
    LAWYER --> BR
    FASTAPI --> POSTGRES
    FASTAPI --> REDIS
    JSON_REF --> CLAUDE
    LAWYER --> CLAUDE
    UTAH --> GPT
    EU --> GEMINI
    
    %% Styling
    classDef frontend fill:#E3F2FD,stroke:#1976D2
    classDef api fill:#F3E5F5,stroke:#7B1FA2
    classDef core fill:#E8F5E8,stroke:#388E3C
    classDef mcp fill:#FFF3E0,stroke:#F57C00
    classDef data fill:#FCE4EC,stroke:#C2185B
    classDef external fill:#F1F8E9,stroke:#689F38
    
    class UI,API_DOCS frontend
    class FASTAPI,HEALTH api
    class WORKFLOW,JSON_REF,LAWYER core
    class UTAH,EU,CA,FL,BR mcp
    class POSTGRES,REDIS data
    class CLAUDE,GPT,GEMINI external
        """
        
        # Add visualization type selector for architecture
        arch_viz_type = st.radio(
            "Architecture Visualization:",
            ["HTML Diagram", "Code View"],
            horizontal=True,
            key="arch_viz"
        )
        
        if arch_viz_type == "HTML Diagram":
            st.components.v1.html(render_mermaid_html(architecture_mermaid, "650px"), height=700)
        else:  # Code View
            st.code(architecture_mermaid, language="mermaid")
        
        # Architecture explanation
        st.markdown("### 📋 Architecture Components")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Frontend Layer:**
            - Streamlit UI for interactive demonstrations
            - FastAPI auto-generated documentation
            
            **API Layer:**
            - REST API with health monitoring
            - Request validation and response formatting
            
            **Core Engine:**
            - LangGraph workflow orchestration
            - Specialized AI agents for different tasks
            """)
            
        with col2:
            st.markdown("""
            **MCP Layer:**
            - 5 specialized jurisdiction analysis agents
            - Each trained on specific legal frameworks
            
            **Data Layer:**
            - PostgreSQL for persistent storage and audit trails
            - Redis for caching and performance optimization
            
            **External Services:**
            - Multiple LLM providers for redundancy
            """)
    
    def _render_agent_interactions(self):
        """Render detailed agent interaction patterns"""
        st.subheader("🤖 Agent Interaction Patterns")
        st.markdown("Detailed view of how AI agents communicate and coordinate")
        
        interaction_mermaid = """
sequenceDiagram
    participant User as 👤 User Request
    participant API as 🚀 FastAPI
    participant Workflow as 🔄 LangGraph
    participant JSON as 📝 JSON Refactorer
    participant Lawyer as ⚖️ Lawyer Agent
    participant Utah as 🏔️ Utah MCP
    participant EU as 🇪🇺 EU MCP
    participant CA as 🌴 CA MCP
    participant FL as 🌊 FL MCP
    participant BR as 🇧🇷 BR MCP
    participant LLM as 🤖 Claude/GPT
    
    User->>API: POST /api/v1/analyze-feature
    API->>Workflow: Initialize Analysis
    
    Note over Workflow: Phase 1: Feature Enhancement
    Workflow->>JSON: Enhance feature description
    JSON->>LLM: Expand TikTok jargon
    LLM-->>JSON: Enhanced terminology
    JSON-->>Workflow: Enriched context
    
    Note over Workflow: Phase 2: Legal Analysis
    Workflow->>Lawyer: Coordinate MCP analysis
    
    par Parallel MCP Analysis
        Lawyer->>Utah: Analyze for Utah compliance
        Utah->>LLM: Check Social Media Act
        LLM-->>Utah: Compliance assessment
        Utah-->>Lawyer: Utah results
    and
        Lawyer->>EU: Analyze for EU compliance  
        EU->>LLM: Check DSA/GDPR
        LLM-->>EU: Compliance assessment
        EU-->>Lawyer: EU results
    and
        Lawyer->>CA: Analyze for CA compliance
        CA->>LLM: Check COPPA/Privacy
        LLM-->>CA: Compliance assessment
        CA-->>Lawyer: CA results
    and
        Lawyer->>FL: Analyze for FL compliance
        FL->>LLM: Check Minor Protection
        LLM-->>FL: Compliance assessment  
        FL-->>Lawyer: FL results
    and
        Lawyer->>BR: Analyze for BR compliance
        BR->>LLM: Check LGPD
        LLM-->>BR: Compliance assessment
        BR-->>Lawyer: BR results
    end
    
    Note over Workflow: Phase 3: Decision Synthesis
    Lawyer->>Workflow: Synthesized compliance decision
    Workflow->>API: Complete analysis results
    API->>User: JSON response with compliance requirements
        """
        
        # Add visualization type selector for interactions
        int_viz_type = st.radio(
            "Interaction Visualization:",
            ["HTML Diagram", "Code View"],
            horizontal=True,
            key="int_viz"
        )
        
        if int_viz_type == "HTML Diagram":
            st.components.v1.html(render_mermaid_html(interaction_mermaid, "850px"), height=900)
        else:  # Code View
            st.code(interaction_mermaid, language="mermaid")
        
        # Interaction explanation
        st.markdown("### 🔄 Interaction Flow Explanation")
        
        st.markdown("""
        **Phase 1 - Feature Enhancement:**
        1. JSON Refactorer receives raw TikTok feature description
        2. Expands jargon (ASL→Age Status Logic, GH→Geographic Handler, etc.)
        3. Adds geographic context and regulatory implications
        
        **Phase 2 - Parallel Legal Analysis:**
        1. Lawyer Agent coordinates analysis across all 5 MCPs simultaneously
        2. Each MCP specializes in specific jurisdictions and regulations
        3. LLM providers (Claude/GPT) provide legal reasoning capabilities
        
        **Phase 3 - Decision Synthesis:**
        1. Lawyer Agent aggregates all MCP responses
        2. Synthesizes into unified compliance requirements
        3. Calculates overall risk level and confidence scores
        """)
    
    def _render_legend_and_docs(self):
        """Render comprehensive legend and documentation"""
        st.subheader("📚 Legend & Documentation")
        
        # Node descriptions
        st.markdown("### 🔧 Workflow Nodes")
        
        for node_id, info in self._node_descriptions.items():
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(f'<div style="background-color: {info["color"]}; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;">{info["name"]}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**Purpose:** {info['purpose']}")
                    st.markdown(f"**Description:** {info['description']}")
                st.markdown("---")
        
        # System capabilities
        st.markdown("### ⚡ System Capabilities")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Analysis Features:**
            - ✅ Single feature analysis
            - ✅ Multi-jurisdiction compliance checking
            - ✅ Risk level assessment (1-5 scale)
            - ✅ Confidence scoring
            - ✅ Implementation step generation
            - ✅ Audit trail and history
            """)
            
        with col2:
            st.markdown("""
            **Technical Features:**
            - ✅ LangGraph workflow orchestration
            - ✅ Multi-LLM provider support
            - ✅ PostgreSQL persistent storage
            - ✅ Redis caching for performance
            - ✅ REST API with OpenAPI docs
            - ✅ Real-time health monitoring
            """)
        
        # Jurisdiction coverage
        st.markdown("### 🌍 Jurisdiction Coverage")
        
        jurisdiction_data = {
            "Utah": {"regulations": "Social Media Regulation Act (2024)", "focus": "Minor protection, curfews, parental controls"},
            "European Union": {"regulations": "DSA, GDPR, DMA", "focus": "Content moderation, transparency, data rights"},
            "California": {"regulations": "COPPA, CCPA, Age-Appropriate Design", "focus": "Child privacy, data protection"},
            "Florida": {"regulations": "Online Protections for Minors Act", "focus": "Parental oversight, content filtering"},
            "Brazil": {"regulations": "LGPD, Data Localization", "focus": "Data residency, cross-border transfers"}
        }
        
        for jurisdiction, details in jurisdiction_data.items():
            with st.expander(f"🏛️ {jurisdiction}", expanded=False):
                st.markdown(f"**Primary Regulations:** {details['regulations']}")
                st.markdown(f"**Focus Areas:** {details['focus']}")
        
        # Performance metrics
        st.markdown("### 📊 Performance Characteristics")
        
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            st.metric("Analysis Time", "< 5 seconds", "Single feature")
            st.metric("Accuracy Target", "> 90%", "Competition dataset")
            
        with metrics_col2:
            st.metric("Jurisdictions", "5", "Global coverage")
            st.metric("Confidence Score", "0.6 - 0.9", "Typical range")
            
        with metrics_col3:
            st.metric("Risk Levels", "1-5 scale", "Standardized")
            st.metric("Implementation", "Phase 1", "Complete ✅")

# Global visualizer instance
workflow_visualizer = WorkflowVisualizer()