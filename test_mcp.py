#!/usr/bin/env python3
"""
Test script to call Requirements MCP directly
"""

import asyncio
import json
from src.core.agents.lawyer_agent import LawyerAgent

async def test_mcp():
    print("🧪 Testing Requirements MCP directly...")
    
    # Initialize lawyer agent (which has MCP connections)
    lawyer_agent = LawyerAgent()
    
    # Test document ID that we know exists
    document_id = "16863f3f-597f-44aa-bb6a-2737e405e046"
    
    print(f"📄 Testing document: {document_id}")
    
    try:
        # Test 1: Metadata search (by document ID)
        print("\n🔍 Test 1: Metadata search by document ID")
        result1 = await lawyer_agent.requirements_mcp.search_requirements(
            search_type="metadata",
            document_id=document_id,
            max_results=10
        )
        
        print(f"✅ Metadata search results:")
        print(json.dumps(result1, indent=2))
        
        # Test 2: Semantic search
        print("\n🔍 Test 2: Semantic search")
        result2 = await lawyer_agent.requirements_mcp.search_requirements(
            search_type="semantic",
            query="user status API requirements",
            max_results=5
        )
        
        print(f"✅ Semantic search results:")
        print(json.dumps(result2, indent=2))
        
    except Exception as e:
        print(f"❌ MCP test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp())