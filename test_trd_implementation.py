#!/usr/bin/env python3
"""
Test script for TRD Lawyer Agent implementation
Verifies that all components work together correctly
"""
import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.agents.lawyer_trd_agent import (
    LawyerTRDAgent, 
    ComplianceReport, 
    RequirementsComplianceReport,
    LawyerKnowledgeBase
)


async def test_mock_mcps():
    """Test that mock MCPs work correctly"""
    print("🧪 Testing Mock MCPs...")
    
    agent = LawyerTRDAgent()
    
    # Test Legal MCP
    print("📋 Testing Legal MCP...")
    legal_search = await agent.legal_mcp.search_documents(
        search_type="semantic",
        query="age verification"
    )
    print(f"   ✅ Legal semantic search returned {len(legal_search.get('results', []))} results")
    
    similarity_search = await agent.legal_mcp.search_documents(
        search_type="similarity", 
        document_content="Utah Social Media Act establishes age verification"
    )
    print(f"   ✅ Legal similarity search returned {len(similarity_search.get('similar_documents', []))} results")
    
    # Test Requirements MCP
    print("📝 Testing Requirements MCP...")
    req_search = await agent.requirements_mcp.search_requirements(
        search_type="semantic",
        query="data retention"
    )
    print(f"   ✅ Requirements semantic search returned {len(req_search.get('results', []))} results")
    
    metadata_search = await agent.requirements_mcp.search_requirements(
        search_type="metadata",
        document_id="req_doc_001",
        extract_requirements=True
    )
    print(f"   ✅ Requirements metadata search extracted {len(metadata_search.get('extracted_requirements', []))} requirements")


async def test_knowledge_base():
    """Test knowledge base functionality"""
    print("🧠 Testing Knowledge Base...")
    
    kb = LawyerKnowledgeBase()
    
    # Test content management
    test_content = "TikTok terminology: Live Shopping = e-commerce integration"
    success = await kb.update_knowledge_base_content(test_content)
    print(f"   ✅ Knowledge base update: {success}")
    
    retrieved_content = await kb.get_knowledge_base_content()
    print(f"   ✅ Knowledge base retrieval: {len(retrieved_content)} characters")
    
    # Test prompt enhancement
    base_prompt = "Analyze this feature for compliance"
    enhanced_prompt = await kb.enhance_prompt_with_knowledge(base_prompt)
    print(f"   ✅ Prompt enhancement: {len(enhanced_prompt)} characters")


async def test_workflow_1():
    """Test Workflow 1: Legal Document → Requirements Compliance"""
    print("🏛️ Testing Workflow 1: Legal → Requirements Compliance...")
    
    agent = LawyerTRDAgent()
    
    # Mock user interaction callback
    def mock_user_callback(question):
        print(f"   💬 Mock user interaction: {question.get('type', 'unknown')}")
        # Always return first option for testing
        options = question.get('options', ['Continue'])
        return options[0] if options else 'Continue'
    
    try:
        result = await agent.workflow_1_legal_compliance_check(
            legal_document_id="legal_doc_001",
            user_interaction_callback=mock_user_callback
        )
        
        print(f"   ✅ Workflow 1 completed:")
        print(f"      - Document: {result.legal_document}")
        print(f"      - Requirements checked: {result.total_requirements_checked}")
        print(f"      - Issues found: {len(result.issues_found)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Workflow 1 failed: {e}")
        return False


async def test_workflow_2():
    """Test Workflow 2: Past Law Iteration Detection"""
    print("🔄 Testing Workflow 2: Past Iteration Detection...")
    
    agent = LawyerTRDAgent()
    
    def mock_user_callback(question):
        print(f"   💬 Mock user interaction: {question.get('type', 'unknown')}")
        # Always choose to keep both versions for testing
        return "KEEP BOTH - Maintain both versions"
    
    try:
        mock_document = {
            'title': 'Utah Social Media Act 2025',
            'content': 'Utah Social Media Act establishes new age verification requirements...'
        }
        
        should_continue = await agent.workflow_2_past_iteration_detection(
            legal_document_content=mock_document,
            user_interaction_callback=mock_user_callback
        )
        
        print(f"   ✅ Workflow 2 completed: should_continue = {should_continue}")
        return True
        
    except Exception as e:
        print(f"   ❌ Workflow 2 failed: {e}")
        return False


async def test_workflow_3():
    """Test Workflow 3: Requirements → Legal Compliance"""
    print("⚖️ Testing Workflow 3: Requirements → Legal Compliance...")
    
    agent = LawyerTRDAgent()
    
    def mock_user_callback(question):
        print(f"   💬 Mock user interaction: {question.get('type', 'unknown')}")
        # Always return compliant for testing
        options = question.get('options', ['COMPLIANT'])
        return options[0] if options else 'COMPLIANT'
    
    try:
        result = await agent.workflow_3_requirements_compliance_check(
            requirements_document_id="req_doc_001",
            user_interaction_callback=mock_user_callback
        )
        
        print(f"   ✅ Workflow 3 completed:")
        print(f"      - Document: {result.requirements_document_id}")
        print(f"      - Requirements checked: {result.total_requirements}")
        print(f"      - Issues found: {len(result.compliance_issues)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Workflow 3 failed: {e}")
        return False


async def test_legacy_compatibility():
    """Test legacy feature analysis compatibility"""
    print("🔧 Testing Legacy Compatibility...")
    
    agent = LawyerTRDAgent()
    
    # Test enriched context (legacy format)
    enriched_context = {
        'original_feature': 'Live Shopping Feature',
        'expanded_description': 'Feature allowing users to purchase products during live streams',
        'geographic_implications': ['Utah', 'EU'],
        'feature_category': 'Commerce',
        'risk_indicators': ['payment processing', 'minor protection']
    }
    
    try:
        result = await agent.analyze(enriched_context)
        
        print(f"   ✅ Legacy analysis completed:")
        print(f"      - Feature: {result.feature_name}")
        print(f"      - Compliance required: {result.compliance_required}")
        print(f"      - Risk level: {result.risk_level}")
        print(f"      - Confidence: {result.confidence_score:.2f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Legacy compatibility failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting TRD Implementation Tests")
    print("=" * 50)
    
    test_results = []
    
    # Test individual components
    await test_mock_mcps()
    await test_knowledge_base()
    
    # Test workflows
    test_results.append(await test_workflow_1())
    test_results.append(await test_workflow_2())
    test_results.append(await test_workflow_3())
    
    # Test compatibility
    test_results.append(await test_legacy_compatibility())
    
    # Summary
    print("=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"   ✅ Passed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! TRD implementation is working correctly.")
        print("\n🎯 Next steps:")
        print("   1. Run Streamlit app: streamlit run src/ui/app.py")
        print("   2. Navigate to 'TRD Workflows' page")
        print("   3. Test document upload and workflows")
    else:
        print(f"⚠️ {total - passed} tests failed. Check implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)