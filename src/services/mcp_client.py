"""
HTTP MCP Client - Real MCP Integration Implementation
Provides HTTP calls to real MCP search services
"""
from typing import Dict, Any, List
import asyncio
import aiohttp
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class MCPSearchClient:
    """
    HTTP client for calling real MCP search services
    """
    
    def __init__(self):
        # MCP service URLs from environment variables
        self.mcp_services = {
            'legal': {
                'url': os.getenv('LEGAL_MCP_URL', 'http://localhost:8010'), 
                'timeout': int(os.getenv('MCP_TIMEOUT_SECONDS', '30'))
            },
            'requirements': {
                'url': os.getenv('REQUIREMENTS_MCP_URL', 'http://localhost:8011'), 
                'timeout': int(os.getenv('MCP_TIMEOUT_SECONDS', '30'))
            }
        }
    
    async def search_legal_mcp(self, search_query: str, feature_context: Dict[str, Any], jurisdictions: List[str] = None) -> Dict[str, Any]:
        """
        Call real Legal MCP service for document search using PostgreSQL + pgvector
        Search legal MCP across all jurisdictions with jurisdiction filtering
        
        Args:
            search_query: Natural language search query
            feature_context: Enriched context from JSON Refactorer
            jurisdictions: Optional list of jurisdictions to filter (Utah, EU, California, Florida, Brazil)
            
        Returns:
            Search results from legal MCP with jurisdiction metadata
        """
        service = self.mcp_services['legal']
        
        try:
            async with aiohttp.ClientSession() as session:
                # Use semantic search if we have a query, otherwise bulk retrieve
                if search_query and search_query.strip():
                    url = f"{service['url']}/api/v1/search"
                    payload = {
                        "search_type": "semantic",
                        "query": search_query,
                        "jurisdictions": jurisdictions,
                        "max_results": 50
                    }
                else:
                    # Fallback to bulk retrieve for empty queries
                    url = f"{service['url']}/api/v1/bulk_retrieve"
                    payload = {
                        "include_content": True,
                        "jurisdictions": ','.join(jurisdictions) if jurisdictions else None,
                        "max_results": 50
                    }
                
                async with session.post(
                    url, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=service['timeout'])
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Legal MCP search completed: {result.get('total_documents', 0)} documents")
                        return result
                    else:
                        logger.error(f"Legal MCP search failed: HTTP {response.status}")
                        return {"documents": [], "total_documents": 0, "retrieval_time": 0.0}
                        
        except Exception as e:
            logger.error(f"Legal MCP search error: {str(e)}")
            return {"documents": [], "total_documents": 0, "retrieval_time": 0.0}
        
    async def search_requirements_mcp(self, search_query: str, feature_context: Dict[str, Any], doc_types: List[str] = None) -> Dict[str, Any]:
        """
        Call requirements MCP service for document search
        Search requirements MCP for PRDs, specs, and user stories
        
        Args:
            search_query: Natural language search query  
            feature_context: Enriched context from JSON Refactorer
            doc_types: Optional list of document types to filter (prd, technical, feature, user_story)
            
        Returns:
            Search results from requirements MCP with document metadata
        """
        service = self.mcp_services['requirements']
        url = f"{service['url']}/api/v1/bulk_retrieve"
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "format": "structured",
                    "include_content": True,
                    "limit": 50
                }
                if doc_types:
                    payload["doc_types"] = doc_types
                
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=service['timeout'])
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Requirements MCP search completed: {result.get('total_requirements', 0)} requirements")
                        return result
                    else:
                        logger.error(f"Requirements MCP search failed: HTTP {response.status}")
                        return {"requirements": [], "total_requirements": 0, "retrieval_time": 0.0}
                        
        except Exception as e:
            logger.error(f"Requirements MCP search error: {str(e)}")
            return {"requirements": [], "total_requirements": 0, "retrieval_time": 0.0}
    
    async def search_both_mcps(self, search_query: str, feature_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search both legal and requirements MCPs in parallel
        Comprehensive search across legal documents and requirements documents
        
        Args:
            search_query: Natural language search query
            feature_context: Enriched context from JSON Refactorer
            
        Returns:
            Combined search results from both MCPs
        """
        try:
            # Execute parallel searches
            legal_task = self.search_legal_mcp(search_query, feature_context)
            requirements_task = self.search_requirements_mcp(search_query, feature_context)
            
            legal_results, requirements_results = await asyncio.gather(
                legal_task, requirements_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(legal_results, Exception):
                logger.error(f"Legal MCP search failed: {legal_results}")
                legal_results = {"documents": [], "total_documents": 0, "retrieval_time": 0.0}
                
            if isinstance(requirements_results, Exception):
                logger.error(f"Requirements MCP search failed: {requirements_results}")
                requirements_results = {"requirements": [], "total_requirements": 0, "retrieval_time": 0.0}
            
            return {
                "legal_results": legal_results,
                "requirements_results": requirements_results,
                "combined_search_time": legal_results.get("retrieval_time", 0) + requirements_results.get("retrieval_time", 0)
            }
            
        except Exception as e:
            logger.error(f"Parallel MCP search failed: {str(e)}")
            return {
                "legal_results": {"documents": [], "total_documents": 0, "retrieval_time": 0.0},
                "requirements_results": {"requirements": [], "total_requirements": 0, "retrieval_time": 0.0},
                "combined_search_time": 0.0
            }
    
    async def health_check_all_services(self) -> Dict[str, bool]:
        """
        Check health status of both MCP services
        
        Returns:
            Dict mapping service names to health status
        """
        health_status = {}
        
        for service_name, service_config in self.mcp_services.items():
            try:
                url = f"{service_config['url']}/health"
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        health_status[service_name] = response.status == 200
                        if response.status == 200:
                            health_data = await response.json()
                            logger.info(f"{service_name} MCP healthy: {health_data.get('status', 'unknown')}")
                        else:
                            logger.warning(f"{service_name} MCP unhealthy: HTTP {response.status}")
                            
            except Exception as e:
                logger.error(f"{service_name} MCP health check failed: {str(e)}")
                health_status[service_name] = False
                
        return health_status
    
    async def search_for_query(self, query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for user query context
        Special search method for user queries (not feature analysis)
        Searches legal MCP for relevant regulations and context
        
        Args:
            query_data: Query information with user question and context
            
        Returns:
            Search results from legal MCP formatted for query response
        """
        try:
            query = query_data.get("query", "")
            context = query_data.get("context", {})
            
            # Search legal MCP for relevant regulations
            legal_results = await self.search_legal_mcp(query, context)
            
            # Format results for query advisory response
            formatted_results = []
            for document in legal_results.get("documents", []):
                formatted_results.append({
                    "jurisdiction": document.get("jurisdiction", "Unknown"),
                    "content": document.get("content", ""),
                    "source_document": document.get("source_document", ""),
                    "relevance_score": document.get("relevance_score", 0.0)
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Query search failed: {str(e)}")
            return []