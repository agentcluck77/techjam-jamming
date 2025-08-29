"""
Streamlit Demo Interface - Phase 1C Implementation
Basic UI for single feature analysis and system monitoring
"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from typing import Dict, Any

try:
    from src.ui.utils.api_client import api_client
    from src.ui.components.workflow_viz import workflow_visualizer
    from src.ui.components.trd_workflows import TRDWorkflowsUI
except ImportError:
    # Fallback for direct streamlit run
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from src.ui.utils.api_client import api_client
    from src.ui.components.workflow_viz import workflow_visualizer
    from src.ui.components.trd_workflows import TRDWorkflowsUI
import requests

# Configure Streamlit page
st.set_page_config(
    page_title="TikTok Geo-Regulation AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """
    Main Streamlit application
    Phase 1C: Basic single analysis interface
    Team Member 2 will enhance with batch processing and visualization
    """
    
    # Header
    st.title("🎯 TikTok Geo-Regulation AI System")
    st.markdown("*Automated compliance analysis for TikTok features across global jurisdictions*")
    
    # Sidebar for navigation and system status
    with st.sidebar:
        st.header("📊 System Status")
        
        # Health check
        if api_client.check_health():
            st.success("✅ Backend API Online")
        else:
            st.error("❌ Backend API Offline")
            st.warning("Please start the FastAPI backend on localhost:8000")
        
        # Model Selection
        st.header("🤖 AI Model")
        render_model_selection()
        
        # System metrics
        with st.expander("System Metrics", expanded=False):
            metrics = api_client.get_metrics()
            if metrics:
                st.json(metrics)
            else:
                st.info("Metrics unavailable")
        
        # Navigation
        st.header("🧭 Navigation")
        page = st.radio(
            "Select Page",
            ["Single Analysis", "TRD Workflows", "Workflow Visualization", "System Info", "Coming Soon"],
            index=0
        )
    
    # Main content area
    if page == "Single Analysis":
        render_single_analysis()
    elif page == "TRD Workflows":
        render_trd_workflows()
    elif page == "Workflow Visualization":
        workflow_visualizer.render_workflow_page()
    elif page == "System Info":
        render_system_info()
    elif page == "Coming Soon":
        render_coming_soon()

def render_model_selection():
    """Render AI model selection interface"""
    try:
        # Get available models
        response = requests.get("http://localhost:8000/api/v1/models/available")
        if response.status_code == 200:
            data = response.json()
            models = data["gemini_models"]
            current_model = data["current_model"]
            
            # Create model options
            model_options = []
            model_mapping = {}
            
            for model_id, model_info in models.items():
                display_name = f"{model_info['name']} - {model_info['description']}"
                model_options.append(display_name)
                model_mapping[display_name] = model_id
            
            # Find current selection index
            current_display = None
            for display_name, model_id in model_mapping.items():
                if model_id == current_model:
                    current_display = display_name
                    break
            
            current_index = model_options.index(current_display) if current_display else 0
            
            # Model selection
            selected_display = st.selectbox(
                "Select Gemini Model",
                model_options,
                index=current_index,
                help="Choose which Gemini model to use for analysis"
            )
            
            selected_model_id = model_mapping[selected_display]
            
            # Update model if changed
            if selected_model_id != current_model:
                if st.button("Update Model", type="secondary", use_container_width=True):
                    try:
                        update_response = requests.post(
                            "http://localhost:8000/api/v1/models/select",
                            json={"model_id": selected_model_id}
                        )
                        if update_response.status_code == 200:
                            st.success(f"✅ Model updated to {models[selected_model_id]['name']}")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update model")
                    except Exception as e:
                        st.error(f"❌ Error updating model: {e}")
            
            # Show current model info
            current_info = models[current_model]
            with st.expander("ℹ️ Model Details", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Input Tokens", f"{current_info['input_tokens']:,}")
                with col2:
                    st.metric("Output Tokens", f"{current_info['output_tokens']:,}")
                st.info(current_info['description'])
        else:
            st.warning("⚠️ Model selection unavailable")
            
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ Backend offline - model selection unavailable")
    except Exception as e:
        st.error(f"❌ Model selection error: {e}")

def render_single_analysis():
    """
    Single feature analysis interface
    Phase 1C: Basic form and results display
    """
    
    st.header("🔍 Single Feature Analysis")
    st.markdown("Analyze a TikTok feature for compliance requirements across global jurisdictions.")
    
    # Analysis form
    with st.form("feature_analysis", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            feature_name = st.text_input(
                "Feature Name*",
                placeholder="e.g., Live Shopping",
                help="Enter the name of the TikTok feature"
            )
            
            feature_description = st.text_area(
                "Feature Description*",
                height=150,
                placeholder="Describe the feature functionality, user interactions, and technical implementation...",
                help="Provide detailed description including functionality, user experience, and technical aspects"
            )
        
        with col2:
            geographic_context = st.text_input(
                "Geographic Context (Optional)",
                placeholder="e.g., Global rollout, US-only, EU-targeted",
                help="Specify target markets or geographic scope"
            )
            
            feature_type = st.selectbox(
                "Feature Category",
                ["Select Category", "Content Creation", "Social Features", "Commerce", "Discovery", "Safety", "Advertising", "Other"],
                help="Select the most appropriate category for this feature"
            )
        
        # Submit button
        col_center1, col_center2, col_center3 = st.columns([1, 1, 1])
        with col_center2:
            submit = st.form_submit_button("🚀 Analyze Feature", type="primary", use_container_width=True)
    
    # Handle form submission
    if submit:
        if not feature_name or not feature_description:
            st.error("⚠️ Please fill in both Feature Name and Description fields.")
            return
        
        # Prepare request data
        request_data = {
            "name": feature_name,
            "description": feature_description,
            "geographic_context": geographic_context if geographic_context else None,
            "feature_type": feature_type if feature_type != "Select Category" else None
        }
        
        # Execute analysis
        analyze_feature_ui(request_data)
    
    # Example features section
    with st.expander("💡 Example Features", expanded=False):
        st.markdown("""
        **Try these example features:**
        
        **Live Shopping**
        - Description: "Real-time shopping experience where users can purchase products directly during live streams with integrated payment processing and age verification"
        
        **ASL Creator Tools**  
        - Description: "New jellybean for ASL content creation with automated captions and sign language recognition"
        
        **Global Creator Fund**
        - Description: "Monetization program allowing creators worldwide to earn revenue from their content with automated payouts and tax compliance"
        """)

def analyze_feature_ui(request_data: Dict[str, Any]):
    """
    Execute feature analysis and display results
    Phase 1C: Basic results display with error handling
    """
    
    st.markdown("---")
    st.subheader("⚡ Analysis in Progress...")
    
    # Progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulate progress updates (Phase 1C)
    progress_steps = [
        (0.2, "🔄 Processing feature description..."),
        (0.4, "📝 Expanding terminology..."),
        (0.6, "⚖️ Analyzing legal requirements..."),
        (0.8, "🌍 Checking jurisdiction compliance..."),
        (1.0, "✅ Analysis complete!")
    ]
    
    for progress, message in progress_steps:
        progress_bar.progress(progress)
        status_text.text(message)
        time.sleep(0.5)  # Simulate processing time
    
    # Make API call
    with st.spinner("Connecting to legal analysis service..."):
        result = api_client.analyze_feature(request_data)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Display results
    if result:
        render_analysis_results(result)
    else:
        st.error("❌ Analysis failed. Please check the system status and try again.")

def render_analysis_results(result: Dict[str, Any]):
    """
    Display comprehensive analysis results
    Phase 1C: Basic results display
    Team Member 2 will enhance with interactive charts and exports
    """
    
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Overall assessment metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        compliance_color = "red" if result["compliance_required"] else "green"
        compliance_text = "REQUIRED" if result["compliance_required"] else "NOT REQUIRED"
        st.metric(
            "Compliance Status",
            compliance_text,
            help="Whether regulatory compliance is required for this feature"
        )
    
    with col2:
        risk_level = result["risk_level"]
        risk_color = "red" if risk_level >= 4 else "orange" if risk_level >= 3 else "green"
        st.metric(
            "Risk Level",
            f"{risk_level}/5",
            help="Overall regulatory risk assessment"
        )
    
    with col3:
        confidence = result["confidence_score"]
        st.metric(
            "Confidence",
            f"{confidence:.0%}",
            help="Confidence in the analysis results"
        )
    
    with col4:
        analysis_time = result["analysis_time"]
        st.metric(
            "Analysis Time",
            f"{analysis_time:.1f}s",
            help="Time taken to complete the analysis"
        )
    
    # Compliance details
    if result["compliance_required"]:
        st.subheader("⚠️ Compliance Requirements")
        
        # Applicable jurisdictions
        st.write("**📍 Applicable Jurisdictions:**")
        for jurisdiction in result["applicable_jurisdictions"]:
            st.write(f"• {jurisdiction}")
        
        # Requirements
        if result["requirements"]:
            st.write("**📋 Regulatory Requirements:**")
            for req in result["requirements"]:
                st.write(f"• {req}")
        
        # Implementation steps
        if result["implementation_steps"]:
            st.write("**🛠️ Implementation Steps:**")
            for i, step in enumerate(result["implementation_steps"], 1):
                st.write(f"{i}. {step}")
    
    else:
        st.success("✅ No significant compliance requirements identified for this feature.")
    
    # Reasoning
    st.subheader("🧠 Analysis Reasoning")
    st.write(result["reasoning"])
    
    # Jurisdiction details
    if result.get("jurisdiction_details"):
        st.subheader("🌍 Jurisdiction Breakdown")
        
        for jurisdiction in result["jurisdiction_details"]:
            with st.expander(f"📍 {jurisdiction['jurisdiction']} - Risk Level {jurisdiction['risk_level']}/5"):
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write("**Compliance Required:**", "Yes" if jurisdiction["compliance_required"] else "No")
                    st.write("**Confidence:**", f"{jurisdiction['confidence']:.0%}")
                    
                    if jurisdiction["applicable_regulations"]:
                        st.write("**Applicable Regulations:**")
                        for reg in jurisdiction["applicable_regulations"]:
                            st.write(f"• {reg}")
                
                with col_b:
                    if jurisdiction["requirements"]:
                        st.write("**Requirements:**")
                        for req in jurisdiction["requirements"]:
                            st.write(f"• {req}")
                    
                    if jurisdiction["implementation_steps"]:
                        st.write("**Implementation Steps:**")
                        for step in jurisdiction["implementation_steps"]:
                            st.write(f"• {step}")
                
                st.write("**Reasoning:**", jurisdiction["reasoning"])
    
    # Export options (Phase 1C - basic)
    st.subheader("📤 Export Results")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        # JSON export
        if st.button("📄 Export as JSON", use_container_width=True):
            st.download_button(
                label="Download JSON",
                data=st.json(result),
                file_name=f"analysis_{result['feature_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # TODO: Team Member 2 - Add more export formats and interactive features
    # with col_exp2:
    #     if st.button("📊 Export as CSV", use_container_width=True):
    #         # Generate CSV export
    #         pass

def render_system_info():
    """System information and development tools"""
    
    st.header("🔧 System Information")
    
    # API status
    st.subheader("API Backend Status")
    if api_client.check_health():
        st.success("✅ FastAPI backend is running and healthy")
        
        # Show metrics
        metrics = api_client.get_metrics()
        if metrics:
            st.json(metrics)
    else:
        st.error("❌ FastAPI backend is not accessible")
        st.code("To start the backend:\npython -m uvicorn src.main:app --reload")
    
    # Development info
    st.subheader("Development Information")
    st.info("""
    **Phase 1C+ Status: Enhanced UI Implementation**
    
    ✅ Single feature analysis working
    ✅ Real-time progress indicators  
    ✅ Results display with jurisdiction breakdown
    ✅ Basic export functionality
    ✅ **Workflow visualization with Mermaid diagrams**
    ✅ **System architecture overview**
    ✅ **Agent interaction patterns**
    
    **Coming in Phase 2 (Team Member 2):**
    🔄 Batch CSV processing
    📈 Performance metrics dashboard
    🎨 Enhanced UI/UX
    """)

def render_coming_soon():
    """Placeholder for features coming in Phase 2"""
    
    st.header("🚧 Coming Soon")
    
    st.info("""
    **Team Member 2 will implement these features in Phase 2:**
    
    📄 **Batch Processing**
    - CSV file upload and processing
    - Progress tracking for large batches
    - Results export and download
    
    🎯 **Workflow Visualization**
    - Real-time LangGraph execution tracking
    - Interactive workflow diagrams
    - Performance monitoring
    
    📊 **Analytics Dashboard**
    - System performance metrics
    - Usage statistics
    - Historical analysis trends
    
    🎨 **Enhanced UI**
    - Interactive charts and graphs
    - Advanced filtering and search
    - Improved mobile experience
    """)
    
    # TODO: Team Member 2 - Replace this with actual implementations
    st.write("**Placeholder buttons for future features:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Batch Analysis", disabled=True):
            st.info("Feature coming soon!")
    
    with col2:
        if st.button("📊 Workflow Viz", disabled=False):
            st.success("✅ Available! Check the 'Workflow Visualization' page in sidebar.")
    
    with col3:
        if st.button("📈 Dashboard", disabled=True):
            st.info("Feature coming soon!")


def render_trd_workflows():
    """Render TRD Workflows page with document upload and compliance analysis"""
    
    # Initialize TRD UI component
    trd_ui = TRDWorkflowsUI()
    
    # Render the main TRD workflows interface
    trd_ui.render_main_page()


if __name__ == "__main__":
    main()