#!/usr/bin/env python3
"""
Script to run mock MCP servers for testing
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_legal_mcp_http():
    """Run Legal MCP HTTP server on port 8010"""
    print("Starting Legal MCP HTTP server on port 8010...")
    legal_server = Path(__file__).parent.parent / "src" / "legal-mcp" / "server.py"
    subprocess.run([sys.executable, str(legal_server), "http"])

def run_requirements_mcp_http():
    """Run Requirements MCP HTTP server on port 8011"""
    print("Starting Requirements MCP HTTP server on port 8011...")
    req_server = Path(__file__).parent.parent / "src" / "requirements-mcp" / "server.py" 
    subprocess.run([sys.executable, str(req_server), "http"])

def run_both_http_servers():
    """Run both MCP HTTP servers in parallel"""
    import threading
    
    print("Starting both Mock MCP HTTP servers...")
    print("Legal MCP: http://localhost:8010")
    print("Requirements MCP: http://localhost:8011")
    print("Press Ctrl+C to stop both servers")
    
    # Run servers in separate threads
    legal_thread = threading.Thread(target=run_legal_mcp_http)
    req_thread = threading.Thread(target=run_requirements_mcp_http)
    
    legal_thread.daemon = True
    req_thread.daemon = True
    
    legal_thread.start()
    req_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Mock MCP servers...")
        sys.exit(0)

def test_servers():
    """Test both MCP servers"""
    import requests
    import json
    
    print("Testing Mock MCP servers...")
    
    # Test Legal MCP
    try:
        response = requests.get("http://localhost:8010/health", timeout=5)
        if response.status_code == 200:
            print("✅ Legal MCP (port 8010): Healthy")
            print(f"   Document count: {response.json().get('document_count', 'N/A')}")
        else:
            print(f"❌ Legal MCP (port 8010): HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Legal MCP (port 8010): Connection failed - {e}")
    
    # Test Requirements MCP
    try:
        response = requests.get("http://localhost:8011/health", timeout=5)
        if response.status_code == 200:
            print("✅ Requirements MCP (port 8011): Healthy")
            print(f"   Document count: {response.json().get('document_count', 'N/A')}")
        else:
            print(f"❌ Requirements MCP (port 8011): HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Requirements MCP (port 8011): Connection failed - {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "legal":
            run_legal_mcp_http()
        elif command == "requirements":
            run_requirements_mcp_http()
        elif command == "test":
            test_servers()
        elif command == "both":
            run_both_http_servers()
        else:
            print("Usage:")
            print("  python run_mock_mcps.py legal        # Run Legal MCP only")
            print("  python run_mock_mcps.py requirements  # Run Requirements MCP only")
            print("  python run_mock_mcps.py both          # Run both MCPs")
            print("  python run_mock_mcps.py test          # Test running servers")
    else:
        run_both_http_servers()