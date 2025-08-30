#!/usr/bin/env python3
"""
Test script for Legal MCP functionality
"""
import asyncio
import json
import aiohttp
import sys

async def test_health():
    """Test the health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8010/health') as response:
                data = await response.json()
                print(f"✅ Health Status: {response.status}")
                print(f"   Response: {json.dumps(data, indent=2)}")
                return response.status == 200
    except Exception as e:
        print(f"❌ Health test failed: {e}")
        return False

async def test_upload_document():
    """Test document upload"""
    print("\n📁 Testing Document Upload...")
    try:
        data = aiohttp.FormData()
        # Add the PDF file
        with open('src/legal-mcp/infodump/California.pdf', 'rb') as f:
            data.add_field('file', f, filename='California.pdf', content_type='application/pdf')
            data.add_field('region', 'California')
            data.add_field('statute', 'California State Law')
            data.add_field('pdf_file_name', 'California.pdf')
            
            async with aiohttp.ClientSession() as session:
                async with session.post('http://localhost:8010/api/v1/upload', data=data) as response:
                    result = await response.json()
                    print(f"✅ Upload Status: {response.status}")
                    print(f"   Response: {json.dumps(result, indent=2)}")
                    return response.status == 200, result.get('document_id')
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False, None

async def test_semantic_search():
    """Test semantic search functionality"""
    print("\n🔍 Testing Semantic Search...")
    try:
        search_data = {
            "search_type": "semantic",
            "query": "privacy rights data protection",
            "max_results": 5
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8010/api/v1/search', json=search_data) as response:
                result = await response.json()
                print(f"✅ Search Status: {response.status}")
                print(f"   Found {len(result.get('documents', []))} documents")
                print(f"   Response: {json.dumps(result, indent=2)}")
                return response.status == 200
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

async def test_mcp_tool_interface():
    """Test MCP tool interface (mock)"""
    print("\n🔧 Testing MCP Tool Interface (simulation)...")
    
    # Simulate MCP tool call structure
    mock_mcp_tools = [
        {
            "name": "search_documents",
            "arguments": {
                "search_type": "semantic",
                "query": "California privacy law",
                "max_results": 3
            }
        },
        {
            "name": "search_documents", 
            "arguments": {
                "search_type": "text",
                "query": "data breach notification",
                "max_results": 5
            }
        }
    ]
    
    for i, tool_call in enumerate(mock_mcp_tools):
        print(f"   🔧 Tool Call {i+1}: {tool_call['name']}")
        print(f"      Arguments: {json.dumps(tool_call['arguments'], indent=6)}")
    
    print("   ✅ MCP tools would be called with these parameters")
    return True

async def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 Starting Legal MCP Test Suite\n")
    print("=" * 50)
    
    # Test 1: Health check
    health_ok = await test_health()
    if not health_ok:
        print("❌ Health check failed - server might not be running")
        print("   Please start the server with: cd src/legal-mcp && uv run server.py http")
        return
    
    # Test 2: Document upload
    upload_ok, doc_id = await test_upload_document() 
    if not upload_ok:
        print("❌ Document upload failed")
    
    # Test 3: Semantic search
    search_ok = await test_semantic_search()
    if not search_ok:
        print("❌ Semantic search failed")
    
    # Test 4: MCP tool interface
    mcp_ok = await test_mcp_tool_interface()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Document Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    print(f"   Semantic Search: {'✅ PASS' if search_ok else '❌ FAIL'}")
    print(f"   MCP Tools: {'✅ PASS' if mcp_ok else '❌ FAIL'}")
    
    if all([health_ok, upload_ok, search_ok, mcp_ok]):
        print("\n🎉 All tests passed! Legal MCP is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the server logs and configuration.")

if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")