'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { getComplianceResults } from '@/lib/api'
import { ComplianceResult } from '@/lib/types'
import { BarChart3, TrendingUp, Clock, FileText } from 'lucide-react'

export default function ResultsHistory() {
  const [results, setResults] = useState<ComplianceResult[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const loadResults = async () => {
      try {
        const data = await getComplianceResults()
        setResults(data)
      } catch (error) {
        console.error('Failed to load results:', error)
        // Mock data for demonstration
        setResults(mockResults)
      } finally {
        setLoading(false)
      }
    }

    loadResults()
  }, [])

  const filteredResults = results.filter(result => 
    result.summary.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds}s`
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    } else {
      return 'Just now'
    }
  }

  const getStatusCounts = () => {
    const total = results.length
    const thisMonth = results.filter(r => {
      const resultDate = new Date(r.completedAt)
      const now = new Date()
      return resultDate.getMonth() === now.getMonth() && 
             resultDate.getFullYear() === now.getFullYear()
    }).length
    
    const totalIssues = results.reduce((sum, r) => sum + r.issues.length, 0)
    const resolvedIssues = results.reduce((sum, r) => 
      sum + r.issues.filter(i => i.type !== 'non-compliant').length, 0
    )
    
    const avgTime = results.length > 0 
      ? results.reduce((sum, r) => sum + r.analysisTime, 0) / results.length
      : 0

    return {
      total,
      thisMonth,
      issueResolutionRate: totalIssues > 0 ? Math.round((resolvedIssues / totalIssues) * 100) : 100,
      avgTime: Math.round(avgTime)
    }
  }

  const stats = getStatusCounts()

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <BarChart3 className="w-8 h-8" />
              Compliance Analysis History
            </h1>
            <p className="text-gray-600 mt-2">
              Access past compliance analysis results
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Input 
              placeholder="Search results..." 
              className="w-64"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Button variant="outline" size="sm">Filter</Button>
            <Button variant="outline" size="sm">Export ▼</Button>
          </div>
        </div>

        {/* Results Summary */}
        <Card className="bg-white">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Analysis Overview
            </h2>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
                <p className="text-sm text-gray-600">Total analyses</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-600">{stats.thisMonth}</p>
                <p className="text-sm text-gray-600">This month</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600">{stats.issueResolutionRate}%</p>
                <p className="text-sm text-gray-600">Issues resolved</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-orange-600">{formatDuration(stats.avgTime)}</p>
                <p className="text-sm text-gray-600">Average analysis time</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                Most common issue: <span className="font-medium text-gray-900">Data retention policies</span>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Recent Results */}
        <Card className="bg-white">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Recent Compliance Checks
            </h2>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-32 bg-gray-200 rounded-lg"></div>
                  </div>
                ))}
              </div>
            ) : filteredResults.length > 0 ? (
              filteredResults.map((result) => {
                const nonCompliantIssues = result.issues.filter(i => i.type === 'non-compliant').length
                const needsReviewIssues = result.issues.filter(i => i.type === 'needs-review').length
                const compliantCount = 15 - result.issues.length // Mock total requirements

                return (
                  <Card key={result.id} className="border border-gray-200">
                    <CardContent className="p-6">
                      <div className="space-y-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                              <FileText className="w-4 h-4" />
                              {result.summary}
                            </h3>
                            <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                              <span>Completed: {formatTimeAgo(result.completedAt)}</span>
                              <span>Duration: {formatDuration(result.analysisTime)}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-6">
                          {nonCompliantIssues > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                              <span className="text-sm font-medium text-red-700">
                                {nonCompliantIssues} non-compliant
                              </span>
                            </div>
                          )}
                          {needsReviewIssues > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
                              <span className="text-sm font-medium text-yellow-700">
                                {needsReviewIssues} needs review
                              </span>
                            </div>
                          )}
                          <div className="flex items-center gap-2">
                            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                            <span className="text-sm font-medium text-green-700">
                              {compliantCount} compliant
                            </span>
                          </div>
                        </div>

                        {result.issues.length > 0 && (
                          <div className="bg-gray-50 p-3 rounded-md">
                            <p className="text-sm font-medium text-gray-700 mb-1">Key Issues:</p>
                            <p className="text-sm text-gray-600">
                              {result.issues.slice(0, 2).map(issue => issue.requirement).join(', ')}
                              {result.issues.length > 2 && ` and ${result.issues.length - 2} more...`}
                            </p>
                          </div>
                        )}

                        <div className="flex items-center gap-2">
                          <Button size="sm">View Details</Button>
                          <Button variant="outline" size="sm">Export Report</Button>
                          {nonCompliantIssues > 0 && (
                            <Button variant="outline" size="sm">Mark Issues Resolved</Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No compliance analysis results found.</p>
                <p className="text-sm mt-1">
                  {searchQuery ? 'Try adjusting your search terms.' : 'Start by uploading documents for analysis.'}
                </p>
              </div>
            )}

            {filteredResults.length > 0 && (
              <div className="text-center pt-4">
                <Button variant="outline">Load More Results</Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Mock data for demonstration
const mockResults: ComplianceResult[] = [
  {
    id: '1',
    workflowId: 'wf-1',
    documentId: 'doc-1',
    status: 'non-compliant',
    summary: 'Live Shopping Platform v2.1 → Legal Compliance',
    completedAt: '2025-01-29T10:00:00Z',
    analysisTime: 105, // seconds
    issues: [
      {
        type: 'non-compliant',
        requirement: 'Data retention period',
        regulation: 'EU GDPR Article 5',
        description: 'Current retention period exceeds legal limits',
        severity: 'high',
        recommendation: 'Reduce retention to 24 months maximum'
      },
      {
        type: 'needs-review',
        requirement: 'Content response time SLA',
        regulation: 'EU DSA Article 16',
        description: 'Response time may not meet DSA requirements',
        severity: 'medium',
        recommendation: 'Review and update SLA to 24 hours'
      }
    ]
  },
  {
    id: '2',
    workflowId: 'wf-2',
    documentId: 'doc-2',
    status: 'compliant',
    summary: 'Content Safety Technical Spec → All Jurisdictions',
    completedAt: '2025-01-28T14:30:00Z',
    analysisTime: 89,
    issues: []
  }
]