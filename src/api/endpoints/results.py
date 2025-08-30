"""
Compliance results endpoints for viewing analysis history.
Handles storage and retrieval of compliance analysis results.
"""

import uuid
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from ...core.database import db_manager, ComplianceReportRepository

router = APIRouter(prefix="/api/results", tags=["results"])

# Mock compliance results storage
mock_results: Dict[str, Dict] = {}

class ComplianceIssue(BaseModel):
    type: str  # non-compliant, needs-review
    requirement: str
    regulation: str
    description: str
    severity: str  # high, medium, low
    recommendation: str

class ComplianceResult(BaseModel):
    id: str
    workflowId: str
    documentId: str
    status: str  # compliant, non-compliant, needs-review
    issues: List[ComplianceIssue]
    summary: str
    completedAt: str
    analysisTime: int  # seconds

# Initialize with mock data
def initialize_mock_results():
    """Initialize mock compliance results"""
    
    # Result 1: Recent analysis with issues
    result1_id = str(uuid.uuid4())
    mock_results[result1_id] = {
        "id": result1_id,
        "workflowId": "workflow-123",
        "documentId": "doc-456",
        "status": "non-compliant",
        "summary": "Live Shopping Platform v2.1 → Legal Compliance",
        "completedAt": (datetime.now() - timedelta(hours=2)).isoformat(),
        "analysisTime": 105,
        "issues": [
            {
                "type": "non-compliant",
                "requirement": "Data retention period",
                "regulation": "EU GDPR Article 5",
                "description": "Current retention period exceeds legal limits",
                "severity": "high", 
                "recommendation": "Reduce retention to 24 months maximum"
            },
            {
                "type": "needs-review",
                "requirement": "Content response time SLA",
                "regulation": "EU DSA Article 16", 
                "description": "Response time may not meet DSA requirements",
                "severity": "medium",
                "recommendation": "Review and update SLA to 24 hours"
            }
        ]
    }
    
    # Result 2: Compliant analysis
    result2_id = str(uuid.uuid4())
    mock_results[result2_id] = {
        "id": result2_id,
        "workflowId": "workflow-124",
        "documentId": "doc-457",
        "status": "compliant",
        "summary": "Content Safety Technical Spec → All Jurisdictions",
        "completedAt": (datetime.now() - timedelta(days=1)).isoformat(),
        "analysisTime": 89,
        "issues": []
    }
    
    # Result 3: Mixed compliance
    result3_id = str(uuid.uuid4())
    mock_results[result3_id] = {
        "id": result3_id,
        "workflowId": "workflow-125", 
        "documentId": "doc-458",
        "status": "needs-review",
        "summary": "Payment Flow User Stories → Multi-jurisdictional",
        "completedAt": (datetime.now() - timedelta(days=3)).isoformat(),
        "analysisTime": 156,
        "issues": [
            {
                "type": "needs-review",
                "requirement": "Payment data encryption",
                "regulation": "PCI DSS Requirement 4",
                "description": "Encryption method needs verification",
                "severity": "medium",
                "recommendation": "Verify AES-256 implementation"
            }
        ]
    }
    
    # Result 4: Age verification analysis  
    result4_id = str(uuid.uuid4())
    mock_results[result4_id] = {
        "id": result4_id,
        "workflowId": "workflow-126",
        "documentId": "doc-459", 
        "status": "non-compliant",
        "summary": "Minor Safety Features → Utah Compliance",
        "completedAt": (datetime.now() - timedelta(days=5)).isoformat(),
        "analysisTime": 203,
        "issues": [
            {
                "type": "non-compliant",
                "requirement": "Age verification methods",
                "regulation": "Utah Social Media Act Section 3",
                "description": "Current age verification insufficient for Utah requirements",
                "severity": "high",
                "recommendation": "Implement government ID verification"
            },
            {
                "type": "non-compliant", 
                "requirement": "Time-based restrictions",
                "regulation": "Utah Social Media Act Section 5",
                "description": "Missing 10:30 PM - 6:30 AM curfew enforcement",
                "severity": "high",
                "recommendation": "Add automatic logout during restricted hours"
            }
        ]
    }

# Initialize mock data
initialize_mock_results()

@router.get("", response_model=List[ComplianceResult])
async def get_compliance_results(
    status: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get compliance analysis results with optional filtering"""
    
    results = list(mock_results.values())
    
    # Apply status filter
    if status:
        results = [r for r in results if r["status"] == status]
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        results = [
            r for r in results 
            if search_lower in r["summary"].lower() or
               any(search_lower in issue["requirement"].lower() for issue in r["issues"])
        ]
    
    # Sort by completion date (newest first)
    results.sort(key=lambda x: x["completedAt"], reverse=True)
    
    # Apply limit
    if limit:
        results = results[:limit]
    
    return [
        ComplianceResult(
            id=r["id"],
            workflowId=r["workflowId"],
            documentId=r["documentId"],
            status=r["status"],
            issues=[ComplianceIssue(**issue) for issue in r["issues"]],
            summary=r["summary"],
            completedAt=r["completedAt"],
            analysisTime=r["analysisTime"]
        )
        for r in results
    ]

@router.get("/{result_id}", response_model=ComplianceResult)
async def get_compliance_result(result_id: str):
    """Get specific compliance result"""
    
    if result_id not in mock_results:
        raise HTTPException(status_code=404, detail="Result not found")
    
    result = mock_results[result_id]
    
    return ComplianceResult(
        id=result["id"],
        workflowId=result["workflowId"],
        documentId=result["documentId"],
        status=result["status"],
        issues=[ComplianceIssue(**issue) for issue in result["issues"]],
        summary=result["summary"],
        completedAt=result["completedAt"],
        analysisTime=result["analysisTime"]
    )

@router.get("/stats/overview")
async def get_results_stats():
    """Get results overview statistics"""
    
    results = list(mock_results.values())
    
    total_analyses = len(results)
    
    # This month filter
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    this_month = [
        r for r in results 
        if datetime.fromisoformat(r["completedAt"]) >= month_start
    ]
    
    # Issue statistics
    total_issues = sum(len(r["issues"]) for r in results)
    resolved_issues = sum(
        len([i for i in r["issues"] if i["type"] != "non-compliant"]) 
        for r in results
    )
    
    # Average analysis time
    avg_time = (
        sum(r["analysisTime"] for r in results) / len(results)
        if results else 0
    )
    
    # Most common issue
    issue_types = {}
    for result in results:
        for issue in result["issues"]:
            req = issue["requirement"]
            issue_types[req] = issue_types.get(req, 0) + 1
    
    most_common_issue = (
        max(issue_types.items(), key=lambda x: x[1])[0]
        if issue_types else "No issues found"
    )
    
    return {
        "total_analyses": total_analyses,
        "this_month": len(this_month),
        "issue_resolution_rate": (
            round((resolved_issues / total_issues) * 100) 
            if total_issues > 0 else 100
        ),
        "avg_analysis_time_seconds": round(avg_time),
        "most_common_issue": most_common_issue
    }

@router.post("/{result_id}/mark-resolved")
async def mark_issues_resolved(result_id: str, issue_ids: List[str] = None):
    """Mark specific issues as resolved"""
    
    if result_id not in mock_results:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # In a real implementation, this would update issue status
    # For demo purposes, we'll just return success
    
    return {
        "message": "Issues marked as resolved",
        "result_id": result_id,
        "resolved_issues": issue_ids or "all"
    }

def _generate_csv_export(reports: List[Dict]) -> Response:
    """Generate CSV export of compliance reports"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV headers
    writer.writerow([
        'Document Name', 'Status', 'Summary', 'Issue Count', 
        'High Severity Issues', 'Medium Severity Issues', 'Low Severity Issues',
        'Analysis Date'
    ])
    
    # CSV data rows
    for report in reports:
        issues = report.get('issues', [])
        high_issues = len([i for i in issues if i.get('severity') == 'high'])
        medium_issues = len([i for i in issues if i.get('severity') == 'medium'])
        low_issues = len([i for i in issues if i.get('severity') == 'low'])
        
        writer.writerow([
            report['document_name'],
            report['status'],
            report['summary'][:100] + '...' if len(report['summary']) > 100 else report['summary'],
            len(issues),
            high_issues,
            medium_issues,
            low_issues,
            report['created_at']
        ])
    
    # Return CSV response
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=compliance_reports.csv"}
    )

@router.get("/document/{document_id}")
async def get_document_report(document_id: str):
    """Get latest compliance report for a specific document"""
    try:
        db_session = next(db_manager.get_db_session())
        report_repo = ComplianceReportRepository(db_session)
        report = await report_repo.get_report_by_document_id(document_id)
        
        if not report:
            return {"has_report": False, "message": "No report found for this document"}
        
        return {
            "has_report": True,
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")

@router.post("/export")
async def export_results(result_ids: List[str], format: str = "json"):
    """Export compliance results in CSV format"""
    
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    try:
        db_session = next(db_manager.get_db_session())
        report_repo = ComplianceReportRepository(db_session)
        reports = await report_repo.get_reports_by_ids(result_ids)
        
        if not reports:
            raise HTTPException(status_code=404, detail="No valid results found")
        
        if format == "csv":
            return _generate_csv_export(reports)
        else:  # json
            return {
                "export_data": reports,
                "format": "json",
                "results_count": len(reports),
                "exported_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")