#!/usr/bin/env python3
"""
Legal MCP Server Runner
Provides easy startup options for the Legal MCP server
"""

import sys
import os
import asyncio
import argparse
import logging

# Add the legal-mcp source to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src2_path = os.path.join(current_dir, 'src2')
sys.path.insert(0, src2_path)

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn', 
        'asyncpg',
        'sentence_transformers',
        'mcp'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages with:")
        print(f"   pip install -r {current_dir}/requirements.txt")
        return False
    
    return True

def check_database_config():
    """Check if database configuration is set"""
    required_env_vars = [
        'DB_HOST',
        'DB_PORT', 
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Missing database environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nUsing defaults: localhost:5432/postgres with postgres/postgres")
        print("Set these in your .env file or environment for custom configuration.")
    
    return True

def run_http_server(host="0.0.0.0", port=8010):
    """Run the Legal MCP as HTTP server"""
    try:
        import uvicorn
        from server import app
        
        print(f"🚀 Starting Legal MCP HTTP Server on {host}:{port}")
        print(f"   Health check: http://{host}:{port}/health")
        print(f"   API docs: http://{host}:{port}/docs")
        print("   Press Ctrl+C to stop")
        
        uvicorn.run(app, host=host, port=port, log_level="info")
        
    except Exception as e:
        print(f"❌ Failed to start HTTP server: {e}")
        return False
    
    return True

def run_mcp_server():
    """Run as MCP protocol server"""
    try:
        from server import main
        
        print("🔧 Starting Legal MCP Protocol Server")
        print("   This will run in stdio mode for MCP protocol communication")
        print("   Press Ctrl+C to stop")
        
        asyncio.run(main())
        
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        return False
    
    return True

def run_embedding_generation():
    """Run embedding generation for existing documents"""
    try:
        from scripts.generate_embeddings import main as generate_main
        
        print("🧠 Starting embedding generation for existing documents")
        print("   This will process all documents in the database and generate vector embeddings")
        
        asyncio.run(generate_main())
        
    except Exception as e:
        print(f"❌ Failed to run embedding generation: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Legal MCP Server - PostgreSQL + pgvector semantic search for legal documents"
    )
    
    parser.add_argument(
        'mode',
        choices=['http', 'mcp', 'embeddings', 'check'],
        help='Server mode: http (FastAPI), mcp (MCP protocol), embeddings (generate embeddings), check (verify setup)'
    )
    
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind HTTP server (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8010, help='Port for HTTP server (default: 8010)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    print("🏛️  Legal MCP Server")
    print("   PostgreSQL + pgvector semantic search for legal documents")
    print()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check database config
    check_database_config()
    
    if args.mode == 'check':
        print("✅ All checks passed! Legal MCP is ready to run.")
        return 0
    
    elif args.mode == 'http':
        success = run_http_server(args.host, args.port)
        return 0 if success else 1
    
    elif args.mode == 'mcp':
        success = run_mcp_server()
        return 0 if success else 1
    
    elif args.mode == 'embeddings':
        success = run_embedding_generation()
        return 0 if success else 1
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())