#!/usr/bin/env python3
"""
Test script to verify Requirements MCP migration from mock to real implementation
"""

import requests
import sys
import time

def test_requirements_mcp():
    """Test the Requirements MCP health endpoint"""
    print("Testing Requirements MCP migration...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8011/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Requirements MCP is responding")
            print(f"   Service: {health_data.get('service')}")
            print(f"   Version: {health_data.get('version')}")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Database Status: {health_data.get('database_status')}")
            print(f"   ChromaDB Status: {health_data.get('chroma_status')}")
            print(f"   Document Count: {health_data.get('document_count')}")
            print(f"   ChromaDB Chunks: {health_data.get('chroma_chunks')}")
            
            if health_data.get('status') == 'healthy':
                print("✅ Real MCP migration successful - all systems connected!")
                return True
            elif health_data.get('status') == 'degraded':
                print("⚠️  Real MCP partially working - some components may be unavailable")
                return True
            else:
                print(f"❌ Real MCP status: {health_data.get('status')}")
                return False
        else:
            print(f"❌ Requirements MCP returned HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Requirements MCP at http://localhost:8011")
        print("   Make sure the service is running with: python src/requirements-mcp/server.py http")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_migration_detection():
    """Test if we can detect the migration from mock to real"""
    print("\nTesting migration detection...")
    
    try:
        response = requests.get("http://localhost:8011/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            
            # Check if this is the real implementation
            has_chroma_status = 'chroma_status' in health_data
            has_database_status = 'database_status' in health_data
            has_chroma_chunks = 'chroma_chunks' in health_data
            
            if has_chroma_status and has_database_status and has_chroma_chunks:
                print("✅ Detected REAL MCP implementation")
                print("   - Has ChromaDB integration")
                print("   - Has PostgreSQL integration") 
                print("   - Has real health monitoring")
                return "real"
            else:
                print("⚠️  Detected MOCK MCP implementation")
                print("   - Missing ChromaDB status")
                print("   - Missing real database integration")
                return "mock"
        else:
            print("❌ Cannot determine MCP implementation type")
            return "unknown"
    except Exception as e:
        print(f"❌ Migration detection failed: {e}")
        return "error"

if __name__ == "__main__":
    print("Requirements MCP Migration Test")
    print("=" * 50)
    
    # Test migration detection
    implementation_type = test_migration_detection()
    
    # Test health endpoint
    health_ok = test_requirements_mcp()
    
    print("\nMigration Summary:")
    print("=" * 50)
    print(f"Implementation Type: {implementation_type.upper()}")
    print(f"Health Status: {'PASS' if health_ok else 'FAIL'}")
    
    if implementation_type == "real" and health_ok:
        print("🎉 MIGRATION SUCCESSFUL!")
        print("   The Requirements MCP has been successfully migrated from mock to real implementation.")
        sys.exit(0)
    elif implementation_type == "mock":
        print("⚠️  MIGRATION INCOMPLETE!")
        print("   The Requirements MCP is still using the mock implementation.")
        sys.exit(1)
    else:
        print("❌ MIGRATION FAILED!")
        print("   Could not verify the Requirements MCP implementation.")
        sys.exit(1)