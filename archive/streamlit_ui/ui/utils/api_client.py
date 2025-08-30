"""
API Client for Streamlit UI - Phase 1C Implementation
Simple HTTP client to communicate with FastAPI backend
"""
import requests
import streamlit as st
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class APIClient:
    """
    Simple API client for communicating with FastAPI backend
    Phase 1C: Basic HTTP requests with error handling
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 30  # 30 second timeout
    
    def analyze_feature(self, feature_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send feature analysis request to FastAPI backend
        Phase 1C: Synchronous requests with basic error handling
        """
        
        url = f"{self.base_url}/api/v1/analyze-feature"
        
        try:
            # Make API request
            response = requests.post(
                url,
                json=feature_data,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # Check response status
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json() if response.content else {"message": "Unknown error"}
                st.error(f"API Error ({response.status_code}): {error_detail.get('message', 'Unknown error')}")
                return None
                
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
            return None
            
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend service. Please ensure the API is running on localhost:8000.")
            return None
            
        except Exception as e:
            logger.error(f"API request failed: {e}")
            st.error(f"Unexpected error: {str(e)}")
            return None
    
    def check_health(self) -> bool:
        """Check if the API backend is healthy"""
        
        url = f"{self.base_url}/api/v1/health"
        
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get system metrics from backend"""
        
        url = f"{self.base_url}/api/v1/metrics"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return None

# TODO: Team Member 2 - Enhanced API client with batch processing
# class EnhancedAPIClient(APIClient):
#     """Enhanced API client with batch processing and real-time updates"""
#     
#     def __init__(self, base_url: str = "http://localhost:8000"):
#         super().__init__(base_url)
#         self.websocket_url = base_url.replace("http", "ws")
#     
#     async def submit_batch_analysis(self, csv_file) -> Optional[str]:
#         # TODO: Team Member 2 - Implement batch CSV upload
#         # 1. Upload CSV file to /api/v1/batch-analyze
#         # 2. Return batch job ID for tracking
#         pass
#     
#     async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
#         # TODO: Team Member 2 - Implement batch status polling
#         # 1. Poll /api/v1/batch-status/{batch_id}
#         # 2. Return progress and results
#         pass
#     
#     async def stream_workflow_updates(self, analysis_id: str):
#         # TODO: Team Member 2 - Implement WebSocket connection
#         # 1. Connect to WebSocket endpoint
#         # 2. Stream real-time workflow updates
#         pass

# Global API client instance
api_client = APIClient()