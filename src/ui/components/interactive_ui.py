"""
Interactive UI Component for User Clarifications
Handles user interaction during analysis for ambiguous features
"""
import streamlit as st
from typing import Dict, Any, List
import asyncio
from datetime import datetime

class InteractiveUIHandler:
    """
    Handles user interaction for clarifications during analysis
    Integrates with Streamlit UI to pause analysis and ask user questions
    """
    
    def __init__(self):
        # Initialize state for managing interaction flows
        if 'clarification_responses' not in st.session_state:
            st.session_state.clarification_responses = {}
        if 'waiting_for_response' not in st.session_state:
            st.session_state.waiting_for_response = None
    
    async def ask_geographic_scope(self, clarification_request: Dict[str, Any]) -> str:
        """Ask user about geographic scope of feature deployment"""
        
        question = clarification_request.get("question", "Where is this feature being deployed?")
        context = clarification_request.get("context", {})
        # Get dynamic options from the clarification request, or use defaults
        default_options = [
            "Global (all regions)", 
            "Multiple specific regions"
        ]
        options = clarification_request.get("options", default_options)
        
        # Display clarification UI
        st.warning("🤔 **Clarification Needed**")
        st.write(f"**Feature**: {context.get('feature', 'Unknown')}")
        if context.get('description'):
            st.write(f"**Description**: {context['description']}")
        
        st.write(f"**Question**: {question}")
        
        # Create unique key for this clarification
        clarification_key = f"geo_scope_{hash(question)}"
        
        # Use selectbox for geographic scope
        response = st.selectbox(
            "Select deployment scope:",
            options,
            key=clarification_key
        )
        
        # Wait for user to confirm
        if st.button("Continue Analysis", key=f"confirm_{clarification_key}"):
            return response
        
        # Return current selection (will be used when button is clicked)
        return response
    
    async def ask_specific_regions(self, clarification_request: Dict[str, Any]) -> str:
        """Ask user to select specific regions"""
        
        question = clarification_request.get("question", "Which specific regions?")
        # Get available jurisdictions from the request context
        available_jurisdictions = clarification_request.get("available_jurisdictions", [])
        options = clarification_request.get("options", available_jurisdictions if available_jurisdictions else ["No jurisdictions available"])
        
        st.info("📍 **Select Specific Regions**")
        st.write(f"**Question**: {question}")
        
        # Use multiselect for multiple regions
        clarification_key = f"specific_regions_{hash(question)}"
        selected_regions = st.multiselect(
            "Select all applicable regions:",
            options,
            key=clarification_key
        )
        
        if st.button("Confirm Selection", key=f"confirm_{clarification_key}"):
            return ", ".join(selected_regions) if selected_regions else "California"
        
        return ", ".join(selected_regions) if selected_regions else "California"
    
    async def ask_clarification(self, clarification_request: Dict[str, Any]) -> str:
        """Ask for clarification on unclear user response"""
        
        question = clarification_request.get("question", "Could you clarify your response?")
        options = clarification_request.get("options", ["Global (all regions)", "Specific regions only"])
        context = clarification_request.get("context", {})
        
        st.warning("❓ **Response Unclear**")
        if context.get("unclear_response"):
            st.write(f"**Your previous response**: '{context['unclear_response']}'")
        st.write(f"**Clarification needed**: {question}")
        
        clarification_key = f"clarify_{hash(question)}"
        response = st.selectbox(
            "Please clarify:",
            options,
            key=clarification_key
        )
        
        if st.button("Submit Clarification", key=f"submit_{clarification_key}"):
            return response
        
        return response
    
    async def ask_feature_category(self, clarification_request: Dict[str, Any]) -> str:
        """Ask user about feature category for better analysis"""
        
        question = clarification_request.get("question", "What type of feature is this?")
        
        st.info("🏷️ **Feature Category**")
        st.write(f"**Question**: {question}")
        
        categories = [
            "Content Moderation",
            "Commerce & Payments", 
            "Data Processing",
            "Social Features",
            "Safety & Security",
            "User Interface",
            "Analytics & Metrics",
            "Other"
        ]
        
        clarification_key = f"feature_cat_{hash(question)}"
        response = st.selectbox(
            "Select feature category:",
            categories,
            key=clarification_key
        )
        
        if st.button("Continue", key=f"continue_{clarification_key}"):
            return response
        
        return response
    
    async def ask_risk_assessment(self, clarification_request: Dict[str, Any]) -> str:
        """Ask user about risk factors for better compliance analysis"""
        
        question = clarification_request.get("question", "Are there any risk factors we should consider?")
        
        st.warning("⚠️ **Risk Assessment**")
        st.write(f"**Question**: {question}")
        
        risk_factors = st.multiselect(
            "Select all applicable risk factors:",
            [
                "Handles payment/financial data",
                "Accessible to minors (under 18)",
                "Processes personal data",
                "Content creation/sharing",
                "Live interactions",
                "Cross-border data transfers",
                "Location tracking",
                "None of the above"
            ],
            key=f"risk_assess_{hash(question)}"
        )
        
        if st.button("Submit Risk Assessment", key=f"submit_risk_{hash(question)}"):
            return ", ".join(risk_factors) if risk_factors else "None specified"
        
        return ", ".join(risk_factors) if risk_factors else "None specified"
    
    async def ask_general_clarification(self, clarification_request: Dict[str, Any]) -> str:
        """Handle general clarification requests"""
        
        question = clarification_request.get("question", "Additional information needed")
        clarification_type = clarification_request.get("clarification_type", "general")
        
        st.info(f"💭 **Clarification Required** ({clarification_type})")
        st.write(f"**Question**: {question}")
        
        clarification_key = f"general_{hash(question)}"
        
        # Use text input for general clarifications
        response = st.text_area(
            "Please provide additional information:",
            key=clarification_key,
            help="Your response will help improve the accuracy of the compliance analysis"
        )
        
        if st.button("Submit Response", key=f"submit_general_{clarification_key}"):
            return response if response.strip() else "No additional information provided"
        
        return response if response.strip() else "No additional information provided"

class StreamlitInteractionManager:
    """
    Manages the overall interaction flow in Streamlit
    Coordinates between analysis and user clarifications
    """
    
    def __init__(self):
        self.ui_handler = InteractiveUIHandler()
        self.callback = None
    
    def create_callback(self):
        """Create callback function for the workflow orchestrator"""
        
        async def interaction_callback(clarification_request: Dict[str, Any]) -> str:
            # Store the request in session state
            st.session_state.waiting_for_response = clarification_request
            st.session_state.clarification_active = True
            
            # Force rerun to show clarification UI
            st.rerun()
        
        return interaction_callback
    
    def handle_clarification_ui(self):
        """Handle active clarification in the UI"""
        
        if not hasattr(st.session_state, 'clarification_active') or not st.session_state.clarification_active:
            return None
            
        if not st.session_state.waiting_for_response:
            return None
        
        clarification_request = st.session_state.waiting_for_response
        request_type = clarification_request.get("type") or clarification_request.get("clarification_type")
        
        # Create a container for the clarification UI
        clarification_container = st.container()
        
        with clarification_container:
            if request_type == "geographic_scope":
                response = asyncio.run(self.ui_handler.ask_geographic_scope(clarification_request))
            elif request_type == "specific_regions":
                response = asyncio.run(self.ui_handler.ask_specific_regions(clarification_request))
            elif request_type == "clarify_response":
                response = asyncio.run(self.ui_handler.ask_clarification(clarification_request))
            elif request_type == "feature_category":
                response = asyncio.run(self.ui_handler.ask_feature_category(clarification_request))
            elif request_type == "risk_assessment":
                response = asyncio.run(self.ui_handler.ask_risk_assessment(clarification_request))
            else:
                response = asyncio.run(self.ui_handler.ask_general_clarification(clarification_request))
        
        return response
    
    def clear_clarification_state(self):
        """Clear clarification state after response"""
        if 'clarification_active' in st.session_state:
            st.session_state.clarification_active = False
        if 'waiting_for_response' in st.session_state:
            st.session_state.waiting_for_response = None