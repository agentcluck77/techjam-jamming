#!/usr/bin/env python3
"""
Debug script to check MCP database connection and queries
"""

import psycopg2
import os

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/geolegal")

def test_direct_db_query():
    print("🔍 Testing direct database connection...")
    
    try:
        # Parse DATABASE_URL
        import urllib.parse
        parsed = urllib.parse.urlparse(DATABASE_URL)
        
        conn = psycopg2.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            database=parsed.path[1:] if parsed.path else "geolegal",
            user=parsed.username or "user",
            password=parsed.password or "password"
        )
        
        cursor = conn.cursor()
        
        document_id = "16863f3f-597f-44aa-bb6a-2737e405e046"
        
        print(f"📄 Testing document: {document_id}")
        
        # Test the exact query the MCP uses
        query = """
            SELECT pl.chunk_content, pl.chunk_index, pl.metadata, p.filename
            FROM pdfs p
            JOIN processing_log pl ON p.id = pl.pdf_id
            WHERE p.id = %s
            ORDER BY pl.chunk_index
            LIMIT %s
        """
        
        print(f"🔍 Executing query: {query}")
        print(f"📋 Parameters: document_id={document_id}, max_results=10")
        
        cursor.execute(query, (document_id, 10))
        results = cursor.fetchall()
        
        print(f"✅ Query executed successfully!")
        print(f"📊 Found {len(results)} chunks")
        
        for i, row in enumerate(results):
            content, chunk_index, metadata, filename = row
            print(f"  Chunk {chunk_index}: {content[:100]}...")
            
        cursor.close()
        conn.close()
        
        return results
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_direct_db_query()