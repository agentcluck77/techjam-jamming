"""
TRD Workflows UI Components
Streamlit interface for the three TRD workflows with document upload and user interaction
"""
import streamlit as st
import asyncio
import tempfile
import os
from typing import Dict, Any, Optional
from datetime import datetime

from ...core.agents.lawyer_trd_agent import LawyerTRDAgent, ComplianceReport, RequirementsComplianceReport


class TRDWorkflowsUI:
    """UI components for TRD workflows with document upload and HITL support"""
    
    def __init__(self):
        self.lawyer_agent = LawyerTRDAgent()
        
        # Initialize session state
        if 'trd_uploaded_docs' not in st.session_state:
            st.session_state.trd_uploaded_docs = {
                'legal': {},
                'requirements': {}
            }
        
        if 'trd_workflow_results' not in st.session_state:
            st.session_state.trd_workflow_results = {}
        
        if 'user_interaction_queue' not in st.session_state:
            st.session_state.user_interaction_queue = []
    
    def render_main_page(self):
        """Main TRD workflows page with workflow selection"""
        
        st.title("🏛️ Lawyer Agent - TRD Compliance Workflows")
        st.markdown("""
        **Three core compliance workflows for automated legal and requirements analysis:**
        
        1. **Legal Document → Requirements Compliance**: Upload legal documents to check existing requirements
        2. **Past Law Iteration Management**: Automatically detect and manage outdated law versions  
        3. **Requirements → Legal Compliance**: Upload requirements to check against legal regulations
        """)
        
        # Workflow selection tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Workflow 1: Legal → Requirements", 
            "🔄 Workflow 2: Past Iterations",
            "⚖️ Workflow 3: Requirements → Legal",
            "📚 Knowledge Base"
        ])
        
        with tab1:
            self.render_workflow_1()
            
        with tab2:
            self.render_workflow_2()
            
        with tab3:
            self.render_workflow_3()
            
        with tab4:
            self.render_knowledge_base()
    
    def render_workflow_1(self):
        """Workflow 1: Legal Document Upload → Requirements Compliance Check"""
        
        st.header("📋 Workflow 1: Legal Document → Requirements Compliance")
        st.markdown("""
        **Purpose**: Check all existing requirements against new legal regulations
        
        **Process**:
        1. Upload a legal document (PDF/text)
        2. System extracts regulatory topics
        3. Searches requirements for potential conflicts
        4. Generates compliance report with actionable issues
        """)
        
        # Document upload section
        st.subheader("📄 Upload Legal Document")
        
        uploaded_file = st.file_uploader(
            "Choose a legal document",
            type=['pdf', 'txt', 'docx'],
            help="Upload legal documents like regulations, acts, amendments, or legal notices",
            key="workflow1_upload"
        )
        
        if uploaded_file:
            # Process uploaded file
            doc_id = self._process_uploaded_file(uploaded_file, 'legal')
            
            if doc_id:
                st.success(f"✅ Document uploaded: {uploaded_file.name}")
                st.session_state.trd_uploaded_docs['legal'][doc_id] = {
                    'filename': uploaded_file.name,
                    'upload_time': datetime.now(),
                    'type': 'legal'
                }
                
                # Analysis button
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🔍 Start Compliance Analysis", key="workflow1_analyze"):
                        self._run_workflow_1(doc_id)
                
                with col2:
                    st.info("💡 Analysis will check requirements for conflicts with this legal document")
        
        # Display previous results
        self._display_workflow_results("workflow_1")
    
    def render_workflow_2(self):
        """Workflow 2: Past Law Iteration Detection & Management"""
        
        st.header("🔄 Workflow 2: Past Law Iteration Detection")
        st.markdown("""
        **Purpose**: Detect and manage outdated law iterations automatically
        
        **Process**:
        1. Upload a legal document
        2. System searches for similar/previous versions
        3. User decides whether to keep or delete past iterations
        4. Database is updated accordingly
        """)
        
        st.subheader("📄 Upload Legal Document for Iteration Check")
        
        uploaded_file = st.file_uploader(
            "Choose a legal document",
            type=['pdf', 'txt', 'docx'],
            help="Upload legal documents to check for past iterations",
            key="workflow2_upload"
        )
        
        if uploaded_file:
            doc_id = self._process_uploaded_file(uploaded_file, 'legal')
            
            if doc_id:
                st.success(f"✅ Document uploaded: {uploaded_file.name}")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🔍 Check for Past Iterations", key="workflow2_analyze"):
                        self._run_workflow_2(doc_id, uploaded_file.name)
                
                with col2:
                    st.info("💡 System will detect similar documents and ask about deletion")
        
        self._display_workflow_results("workflow_2")
    
    def render_workflow_3(self):
        """Workflow 3: Requirements Document → Legal Compliance Check"""
        
        st.header("⚖️ Workflow 3: Requirements → Legal Compliance")
        st.markdown("""
        **Purpose**: Check new requirements against all existing legal regulations
        
        **Process**:
        1. Upload a requirements document (PDF/text)  
        2. System extracts structured requirements
        3. Searches legal database for applicable regulations
        4. Generates compliance assessment with user input
        """)
        
        st.subheader("📄 Upload Requirements Document")
        
        uploaded_file = st.file_uploader(
            "Choose a requirements document",
            type=['pdf', 'txt', 'docx'],
            help="Upload PRDs, technical specs, user stories, or feature requirements",
            key="workflow3_upload"
        )
        
        if uploaded_file:
            doc_id = self._process_uploaded_file(uploaded_file, 'requirements')
            
            if doc_id:
                st.success(f"✅ Document uploaded: {uploaded_file.name}")
                st.session_state.trd_uploaded_docs['requirements'][doc_id] = {
                    'filename': uploaded_file.name,
                    'upload_time': datetime.now(),
                    'type': 'requirements'
                }
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("⚖️ Start Legal Compliance Check", key="workflow3_analyze"):
                        self._run_workflow_3(doc_id)
                
                with col2:
                    st.info("💡 Analysis will check requirements against legal regulations")
        
        self._display_workflow_results("workflow_3")
    
    def render_knowledge_base(self):
        """Knowledge Base Editor"""
        
        st.header("📚 Knowledge Base Editor")
        st.markdown("""
        **Purpose**: Customize the lawyer agent's knowledge for better analysis
        
        **Content**: Add TikTok terminology, legal precedents, compliance patterns, and domain expertise
        """)
        
        # Get current knowledge base content
        current_content = asyncio.run(self.lawyer_agent.knowledge_base.get_knowledge_base_content())
        
        # Large text area for editing
        new_content = st.text_area(
            "Knowledge Base Content",
            value=current_content,
            height=400,
            help="Add TikTok terminology, legal notes, compliance patterns, custom definitions, etc.",
            placeholder="""Example content:

TikTok Terminology:
- "Live Shopping" = e-commerce integration allowing users to purchase products during live streams
- "Creator Fund" = monetization program for content creators
- "For You Page" = personalized content recommendation feed

Legal Precedents:
- Utah Social Media Act requires age verification for minor-related features
- EU DSA mandates 24-hour response time for content moderation
- COPPA applies to any feature accessible by users under 13

Compliance Patterns:
- Payment processing features → PCI DSS compliance required
- User data collection → Privacy policy updates needed
- Minor-accessible features → Parental controls required
"""
        )
        
        # Save/Clear buttons
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            if st.button("💾 Save", key="kb_save"):
                success = asyncio.run(
                    self.lawyer_agent.knowledge_base.update_knowledge_base_content(new_content)
                )
                if success:
                    st.success("✅ Knowledge base updated!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update knowledge base")
        
        with col2:
            if st.button("🗑️ Clear", key="kb_clear"):
                if st.session_state.get('confirm_clear', False):
                    asyncio.run(
                        self.lawyer_agent.knowledge_base.update_knowledge_base_content("")
                    )
                    st.success("🗑️ Knowledge base cleared!")
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("⚠️ Click Clear again to confirm deletion")
        
        # Display current content stats
        if current_content:
            word_count = len(current_content.split())
            char_count = len(current_content)
            st.info(f"📊 Current content: {word_count} words, {char_count} characters")
    
    def _process_uploaded_file(self, uploaded_file, doc_type: str) -> Optional[str]:
        """Process uploaded file and return document ID"""
        try:
            # Create temporary file  
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            # Mock document processing - in real implementation, this would:
            # 1. Extract text from PDF/DOCX
            # 2. Store in appropriate MCP database
            # 3. Return actual document ID
            
            content = self._extract_text_content(tmp_file_path, uploaded_file.name)
            
            # Generate mock document ID
            doc_id = f"{doc_type}_{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Store in mock database (session state for demo)
            if 'mock_documents' not in st.session_state:
                st.session_state.mock_documents = {}
                
            st.session_state.mock_documents[doc_id] = {
                'document_id': doc_id,
                'title': uploaded_file.name,
                'content': content,
                'type': doc_type,
                'upload_date': datetime.now().isoformat()
            }
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            return doc_id
            
        except Exception as e:
            st.error(f"❌ Failed to process file: {str(e)}")
            return None
    
    def _extract_text_content(self, file_path: str, filename: str) -> str:
        """Extract text content from uploaded file"""
        try:
            if filename.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif filename.lower().endswith('.pdf'):
                # Mock PDF extraction
                return f"[PDF Content from {filename}] This is mock PDF content extraction. In real implementation, this would use PDF parsing libraries to extract actual text content from the uploaded PDF file."
            elif filename.lower().endswith('.docx'):
                # Mock DOCX extraction  
                return f"[DOCX Content from {filename}] This is mock DOCX content extraction. In real implementation, this would use python-docx or similar libraries to extract actual text content."
            else:
                return f"[Content from {filename}] Mock content extraction for demonstration purposes."
                
        except Exception:
            return f"[Mock content from {filename}] Content extraction simulated for demo purposes."
    
    def _run_workflow_1(self, doc_id: str):
        """Execute Workflow 1 with user interaction"""
        
        with st.spinner("🔍 Running Legal Document Compliance Analysis..."):
            try:
                # Create user interaction callback
                def user_callback(question):
                    return self._handle_user_interaction(question)
                
                # Run workflow 1
                result = asyncio.run(
                    self.lawyer_agent.workflow_1_legal_compliance_check(
                        doc_id, user_callback
                    )
                )
                
                # Store result
                st.session_state.trd_workflow_results[f"workflow_1_{doc_id}"] = result
                
                st.success(f"✅ Analysis complete! Found {len(result.issues_found)} compliance issues")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Workflow 1 failed: {str(e)}")
    
    def _run_workflow_2(self, doc_id: str, filename: str):
        """Execute Workflow 2 with user interaction"""
        
        with st.spinner("🔍 Checking for past law iterations..."):
            try:
                # Get document content
                doc_content = st.session_state.mock_documents.get(doc_id, {})
                
                def user_callback(question):
                    return self._handle_user_interaction(question)
                
                # Run workflow 2
                should_continue = asyncio.run(
                    self.lawyer_agent.workflow_2_past_iteration_detection(
                        doc_content, user_callback
                    )
                )
                
                # Store result
                st.session_state.trd_workflow_results[f"workflow_2_{doc_id}"] = {
                    "status": "completed",
                    "should_continue": should_continue,
                    "document": filename,
                    "timestamp": datetime.now()
                }
                
                if should_continue:
                    st.success("✅ Past iteration check complete - document processing can continue")
                else:
                    st.info("⏸️ Processing stopped based on user decision")
                    
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Workflow 2 failed: {str(e)}")
    
    def _run_workflow_3(self, doc_id: str):
        """Execute Workflow 3 with user interaction"""
        
        with st.spinner("⚖️ Running Requirements Legal Compliance Check..."):
            try:
                def user_callback(question):
                    return self._handle_user_interaction(question)
                
                # Run workflow 3
                result = asyncio.run(
                    self.lawyer_agent.workflow_3_requirements_compliance_check(
                        doc_id, user_callback
                    )
                )
                
                # Store result
                st.session_state.trd_workflow_results[f"workflow_3_{doc_id}"] = result
                
                st.success(f"✅ Analysis complete! Checked {result.total_requirements} requirements, found {len(result.compliance_issues)} issues")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Workflow 3 failed: {str(e)}")
    
    def _handle_user_interaction(self, question: Dict[str, Any]) -> str:
        """Handle user interaction dialogs - Streamlit implementation"""
        
        # Use session state to manage dialog state
        dialog_key = f"dialog_{question.get('type', 'unknown')}_{id(question)}"
        
        if f"{dialog_key}_response" not in st.session_state:
            # Display dialog
            st.markdown("---")
            
            # Question title with emoji
            title = question.get('title', '❓ User Input Needed')
            st.markdown(f"### {title}")
            
            # Question text
            question_text = question.get('question', 'Please make a selection:')
            st.markdown(question_text)
            
            # Context information
            if question.get('context'):
                with st.expander("📋 Additional Context", expanded=False):
                    st.json(question['context'])
            
            # Options
            options = question.get('options', ['Continue', 'Cancel'])
            
            # Use radio buttons for single selection
            if question.get('multiple_select', False):
                # Multiple selection - use multiselect
                selected = st.multiselect(
                    "Select applicable options:",
                    options,
                    key=f"{dialog_key}_multiselect"
                )
                user_response = ", ".join(selected) if selected else "No selection"
            else:
                # Single selection - use radio
                user_response = st.radio(
                    "Please select an option:",
                    options,
                    key=f"{dialog_key}_radio"
                )
            
            # Confirmation button
            if st.button("✅ Confirm Selection", key=f"{dialog_key}_confirm"):
                st.session_state[f"{dialog_key}_response"] = user_response
                st.success(f"✅ Selection confirmed: {user_response}")
                st.rerun()
            
            st.markdown("---")
            
            # Return default while waiting for user input
            return "PENDING_USER_INPUT"
        else:
            # Return stored response
            response = st.session_state[f"{dialog_key}_response"]
            # Clean up session state
            del st.session_state[f"{dialog_key}_response"]
            return response
    
    def _display_workflow_results(self, workflow_key: str):
        """Display results for a specific workflow"""
        
        # Find results for this workflow
        workflow_results = {
            k: v for k, v in st.session_state.trd_workflow_results.items() 
            if k.startswith(workflow_key)
        }
        
        if not workflow_results:
            return
        
        st.subheader("📊 Analysis Results")
        
        for result_key, result in workflow_results.items():
            
            with st.expander(f"📋 Result: {result_key}", expanded=True):
                
                if isinstance(result, ComplianceReport):
                    self._display_compliance_report(result)
                elif isinstance(result, RequirementsComplianceReport):
                    self._display_requirements_compliance_report(result)
                elif isinstance(result, dict):
                    # Workflow 2 result
                    st.json(result)
                else:
                    st.write(str(result))
    
    def _display_compliance_report(self, report: ComplianceReport):
        """Display Workflow 1 compliance report"""
        
        st.markdown(f"**📋 COMPLIANCE CHECK RESULTS**")
        st.markdown(f"**Legal Document**: {report.legal_document}")
        st.markdown(f"**Requirements Checked**: {report.total_requirements_checked} | **Issues Found**: {len(report.issues_found)}")
        st.markdown(f"**Timestamp**: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not report.issues_found:
            st.success("✅ **No compliance issues found!** All requirements appear to be compliant with the legal document.")
            return
        
        # Categorize issues
        non_compliant = [issue for issue in report.issues_found if issue.status == "NON-COMPLIANT"]
        needs_review = [issue for issue in report.issues_found if issue.status == "NEEDS-REVIEW"]
        
        if non_compliant:
            st.markdown(f"### ❌ NON-COMPLIANT ({len(non_compliant)} items):")
            for issue in non_compliant:
                st.error(f"""
**• {issue.requirement_id}**: {issue.requirement_summary}
- **Issue**: {issue.reason}
- **Action**: {issue.action_needed}
""")
        
        if needs_review:
            st.markdown(f"### ⚠️ NEEDS REVIEW ({len(needs_review)} items):")
            for issue in needs_review:
                st.warning(f"""
**• {issue.requirement_id}**: {issue.requirement_summary}
- **Issue**: {issue.reason}  
- **Action**: {issue.action_needed}
""")
    
    def _display_requirements_compliance_report(self, report: RequirementsComplianceReport):
        """Display Workflow 3 requirements compliance report"""
        
        st.markdown(f"**⚖️ REQUIREMENTS LEGAL COMPLIANCE RESULTS**")
        st.markdown(f"**Requirements Document ID**: {report.requirements_document_id}")
        st.markdown(f"**Total Requirements**: {report.total_requirements} | **Issues Found**: {len(report.compliance_issues)}")
        st.markdown(f"**Timestamp**: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not report.compliance_issues:
            st.success("✅ **No legal compliance issues found!** All requirements appear to comply with legal regulations.")
            return
        
        # Display issues
        for issue in report.compliance_issues:
            if issue.status == "NON-COMPLIANT":
                st.error(f"""
**❌ {issue.requirement_id}**: {issue.requirement_summary}
- **Conflict**: {issue.reason}
- **Regulation**: {issue.relevant_regulation}
- **Action Needed**: {issue.action_needed}
""")
            else:
                st.warning(f"""
**⚠️ {issue.requirement_id}**: {issue.requirement_summary}
- **Issue**: {issue.reason}
- **Regulation**: {issue.relevant_regulation}
- **Action Needed**: {issue.action_needed}
""")