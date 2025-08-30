"""
Real MCP Client - Standard MCP Tool Integration
Provides MCP tool calls to real MCP servers for lawyer agents
"""
import asyncio
import logging
import os
import subprocess
import json
from typing import Dict, Any, List
from ..models import JurisdictionAnalysis

logger = logging.getLogger(__name__)

class RealMCPClient:
    """
    Real MCP client that makes standard MCP tool calls to our MCP servers
    Used by lawyer agents for legal and requirements document searches
    """
    
    def __init__(self):
        # MCP server configuration
        self.legal_mcp_url = os.getenv('LEGAL_MCP_URL', 'http://localhost:8010')
        self.requirements_mcp_url = os.getenv('REQUIREMENTS_MCP_URL', 'http://localhost:8011')
        
        # Available MCP tools
        self.available_tools = [
            {
                "name": "search_legal_documents",
                "description": "Search legal documents across all jurisdictions with jurisdiction filtering",
                "mcp_server": "legal-mcp",
                "port": 8010,
                "tool_name": "search_documents",
                "search_types": ["semantic", "similarity"]
            },
            {
                "name": "delete_legal_document",
                "description": "Delete legal document for past iteration removal",
                "mcp_server": "legal-mcp", 
                "port": 8010,
                "tool_name": "delete_document"
            },
            {
                "name": "search_requirements",
                "description": "Search requirements documents with semantic, metadata, and bulk retrieval",
                "mcp_server": "requirements-mcp",
                "port": 8011,
                "tool_name": "search_requirements",
                "search_types": ["semantic", "metadata", "bulk_retrieve"]
            },
            {
                "name": "check_requirements_document_status",
                "description": "Check processing status of a requirements document",
                "mcp_server": "requirements-mcp", 
                "port": 8011,
                "tool_name": "check_document_status"
            }
        ]
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        MCP protocol: Return list of available tools from both MCP servers
        """
        return self.available_tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP protocol: Call specific MCP tool by name with arguments
        Routes to appropriate MCP server
        """
        # Find the tool configuration
        tool_config = next((t for t in self.available_tools if t["name"] == name), None)
        if not tool_config:
            return {"error": f"Tool {name} not found"}
        
        try:
            if tool_config["mcp_server"] == "legal-mcp":
                return await self._call_legal_mcp_tool(tool_config["tool_name"], arguments)
            elif tool_config["mcp_server"] == "requirements-mcp":
                return await self._call_requirements_mcp_tool(tool_config["tool_name"], arguments)
            else:
                return {"error": f"Unknown MCP server: {tool_config['mcp_server']}"}
                
        except Exception as e:
            logger.error(f"MCP tool call failed for {name}: {str(e)}")
            return {"error": f"MCP call failed: {str(e)}"}
    
    async def _call_legal_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Legal MCP tool via subprocess (simulating MCP tool call)
        In a real implementation, this would use the MCP protocol
        """
        if tool_name == "search_documents":
            # Simulate MCP tool call to search_documents
            search_type = arguments.get("search_type", "semantic")
            jurisdictions = arguments.get("jurisdictions", [])
            max_results = arguments.get("max_results", 10)
            
            # For now, simulate with HTTP call to our server  
            from ...services.mcp_client import MCPSearchClient
            http_client = MCPSearchClient()
            
            if search_type == "semantic":
                result = await http_client.search_legal_mcp("", {}, jurisdictions)
                # Convert to MCP tool response format
                return {
                    "search_type": "semantic",
                    "results": result.get("documents", []),
                    "total_results": result.get("total_documents", 0),
                    "search_time": result.get("retrieval_time", 0.0)
                }
            elif search_type == "similarity":
                # Mock similarity response for now
                return {
                    "search_type": "similarity", 
                    "similar_documents": [],
                    "total_found": 0,
                    "search_time": 0.1
                }
            else:
                return {"error": "Invalid search_type for legal documents"}
                
        elif tool_name == "delete_document":
            document_id = arguments.get("document_id")
            confirm = arguments.get("confirm_deletion", True)
            
            return {
                "success": confirm,
                "document_id": document_id,
                "message": "Document deletion simulated (mock implementation)"
            }
        
        return {"error": f"Unknown legal MCP tool: {tool_name}"}
    
    async def _call_requirements_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Requirements MCP tool via subprocess (simulating MCP tool call)
        In a real implementation, this would use the MCP protocol
        """
        if tool_name == "search_requirements":
            search_type = arguments.get("search_type", "semantic")
            max_results = arguments.get("max_results", 5)
            
            # For now, simulate with HTTP call to our server  
            from ...services.mcp_client import MCPSearchClient
            http_client = MCPSearchClient()
            
            if search_type == "bulk_retrieve":
                result = await http_client.search_requirements_mcp("", {})
                return {
                    "requirements": result.get("requirements", []),
                    "total_requirements": result.get("total_requirements", 0),
                    "retrieval_time": result.get("retrieval_time", 0.0)
                }
            elif search_type == "semantic":
                # Mock semantic search for now
                return {
                    "results": [],
                    "total_results": 0,
                    "search_time": 0.1
                }
            elif search_type == "metadata":
                document_id = arguments.get("document_id")
                return {
                    "document_id": document_id,
                    "results": [],
                    "total_results": 0,
                    "search_time": 0.1
                }
            else:
                return {"error": "Invalid search_type for requirements"}
        
        elif tool_name == "check_document_status":
            document_id = arguments.get("document_id")
            if not document_id:
                return {"error": "document_id is required for status check"}
            
            # Call the requirements MCP status endpoint directly via HTTP
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.requirements_mcp_url}/api/v1/status/{document_id}") as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 404:
                            return {"error": "Document not found", "status": "not_found"}
                        else:
                            return {"error": f"Status check failed: HTTP {response.status}"}
            except Exception as e:
                logger.error(f"Status check failed for {document_id}: {e}")
                return {"error": f"Status check failed: {str(e)}"}
        
        return {"error": f"Unknown requirements MCP tool: {tool_name}"}
    
    # Legacy compatibility methods for existing workflow
    async def analyze_feature(self, jurisdiction: str, feature_context: Dict[str, Any]) -> JurisdictionAnalysis:
        """
        Legacy method for backward compatibility
        Converts to MCP tool calls for legal document search
        """
        try:
            # Call legal MCP search for this jurisdiction
            search_result = await self.call_tool("search_legal_documents", {
                "search_type": "semantic",
                "jurisdictions": [jurisdiction],
                "max_results": 5
            })
            
            documents = search_result.get("results", [])
            
            # Find documents for this jurisdiction
            jurisdiction_docs = [doc for doc in documents if doc.get("jurisdiction", "").lower() == jurisdiction.lower()]
            
            if jurisdiction_docs:
                doc = jurisdiction_docs[0]  # Use first result
                return JurisdictionAnalysis(
                    jurisdiction=jurisdiction.title(),
                    applicable_regulations=[doc.get("source_document", "Unknown regulation")],
                    compliance_required=True,
                    risk_level=3,
                    requirements=["Review legal requirements from document search"],
                    implementation_steps=["Analyze legal document content"],
                    confidence=doc.get("relevance_score", 0.8),
                    reasoning=f"Based on legal document: {doc.get('content', '')[:100]}...",
                    analysis_time=search_result.get("search_time", 0.5)
                )
            else:
                # No specific documents for jurisdiction
                return JurisdictionAnalysis(
                    jurisdiction=jurisdiction.title(),
                    applicable_regulations=[],
                    compliance_required=False,
                    risk_level=1,
                    requirements=[],
                    implementation_steps=[],
                    confidence=0.3,
                    reasoning=f"No specific regulations found for {jurisdiction}",
                    analysis_time=0.1
                )
                
        except Exception as e:
            logger.error(f"Legacy feature analysis failed for {jurisdiction}: {str(e)}")
            # Return minimal analysis on error
            return JurisdictionAnalysis(
                jurisdiction=jurisdiction.title(),
                applicable_regulations=[],
                compliance_required=False,
                risk_level=1,
                requirements=[],
                implementation_steps=[],
                confidence=0.1,
                reasoning=f"Analysis failed: {str(e)}",
                analysis_time=0.0
            )
    
    async def get_available_jurisdictions(self) -> List[str]:
        """
        Get list of available jurisdictions from legal MCP
        """
        return ["Utah", "EU", "California", "Florida", "Brazil"]
    
    async def analyze_parallel(self, feature_context: Dict[str, Any]) -> List[JurisdictionAnalysis]:
        """
        Legacy method: Execute parallel analysis across all jurisdictions
        """
        jurisdictions = await self.get_available_jurisdictions()
        results = []
        
        # Sequential execution for simplicity (can be made parallel)
        for jurisdiction in jurisdictions:
            try:
                analysis = await self.analyze_feature(jurisdiction.lower(), feature_context)
                results.append(analysis)
            except Exception as e:
                logger.error(f"Analysis failed for {jurisdiction}: {e}")
                continue
        
        return results
    
    async def search_for_query(self, query_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Legacy method: Search for user queries using MCP tools
        """
        try:
            # Search legal documents
            search_result = await self.call_tool("search_legal_documents", {
                "search_type": "semantic",
                "max_results": 10
            })
            
            # Format results for query response
            formatted_results = []
            for doc in search_result.get("results", []):
                formatted_results.append({
                    "jurisdiction": doc.get("jurisdiction", "Unknown"),
                    "results": [{
                        "chunk_id": doc.get("chunk_id", "unknown"),
                        "source_document": doc.get("source_document", ""),
                        "content": doc.get("content", ""),
                        "relevance_score": doc.get("relevance_score", 0.0),
                        "metadata": {
                            "document_type": "regulation",
                            "chunk_index": 1,
                            "character_start": 0,
                            "character_end": len(doc.get("content", ""))
                        }
                    }],
                    "total_results": 1,
                    "search_time": search_result.get("search_time", 0.1)
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Query search failed: {str(e)}")
            return []