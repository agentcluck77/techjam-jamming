'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useDocumentStore } from '@/lib/stores'
import { getDocuments, startBulkRequirementsAnalysis, startBulkLegalAnalysis, getBatchJobStatus, getDocumentReport, deleteDocument } from '@/lib/api'
import { Document } from '@/lib/types'
import { BookOpen, Trash2, Zap, FileText, Eye, RefreshCw } from 'lucide-react'

export default function DocumentLibrary() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | 'requirements' | 'legal'>('all')
  const [bulkJobStatus, setBulkJobStatus] = useState<{[key: string]: string}>({})
  const [documentReports, setDocumentReports] = useState<{[key: string]: any}>({})
  const [selectedReport, setSelectedReport] = useState<any>(null)
  const [isReportDialogOpen, setIsReportDialogOpen] = useState(false)
  const [rerunningDocuments, setRerunningDocuments] = useState<Set<string>>(new Set())
  const [isDeleting, setIsDeleting] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const docs = await getDocuments()
        setDocuments(docs)
      } catch (error) {
        console.error('Failed to load documents:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDocuments()
  }, [])

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = typeFilter === 'all' || doc.type === typeFilter
    return matchesSearch && matchesType
  })

  const handleDocumentSelect = (docId: string) => {
    setSelectedDocs(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    )
  }

  const handleSelectAll = () => {
    if (selectedDocs.length === filteredDocuments.length) {
      setSelectedDocs([])
    } else {
      setSelectedDocs(filteredDocuments.map(doc => doc.id))
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    })
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      analyzed: 'bg-green-100 text-green-700',
      stored: 'bg-blue-100 text-blue-700',
      pending: 'bg-yellow-100 text-yellow-700',
      processing: 'bg-orange-100 text-orange-700'
    }
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-700'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  const requirementDocs = documents.filter(doc => doc.type === 'requirements')
  const legalDocs = documents.filter(doc => doc.type === 'legal')
  const totalSize = documents.reduce((sum, doc) => sum + doc.size, 0)
  
  const selectedRequirementDocs = selectedDocs.filter(id => 
    documents.find(doc => doc.id === id)?.type === 'requirements'
  )
  const selectedLegalDocs = selectedDocs.filter(id => 
    documents.find(doc => doc.id === id)?.type === 'legal'
  )
  
  // Load document reports on mount
  useEffect(() => {
    const loadDocumentReports = async () => {
      const reports: {[key: string]: any} = {}
      for (const doc of documents) {
        try {
          const reportData = await getDocumentReport(doc.id)
          if (reportData.has_report) {
            reports[doc.id] = reportData.report
          }
        } catch (error) {
          console.error(`Failed to load report for ${doc.id}:`, error)
        }
      }
      setDocumentReports(reports)
    }
    
    if (documents.length > 0) {
      loadDocumentReports()
    }
  }, [documents])

  // Function to refresh a specific document's report
  const refreshDocumentReport = async (documentId: string) => {
    try {
      const reportData = await getDocumentReport(documentId)
      setDocumentReports(prev => ({
        ...prev,
        [documentId]: reportData.has_report ? reportData.report : null
      }))
    } catch (error) {
      console.error(`Failed to refresh report for ${documentId}:`, error)
    }
  }
  
  const handleBulkRequirementsAnalysis = async () => {
    if (selectedRequirementDocs.length === 0) return
    
    try {
      const result = await startBulkRequirementsAnalysis(selectedRequirementDocs, selectedLegalDocs.length > 0 ? selectedLegalDocs : undefined)
      setBulkJobStatus(prev => ({...prev, [result.job_id]: 'processing'}))
      
      // Poll for job status
      const pollInterval = setInterval(async () => {
        try {
          const status = await getBatchJobStatus(result.job_id)
          setBulkJobStatus(prev => ({...prev, [result.job_id]: status.status}))
          
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollInterval)
            // Refresh documents to show updated reports
            const docs = await getDocuments()
            setDocuments(docs)
          }
        } catch (error) {
          console.error('Failed to poll job status:', error)
          clearInterval(pollInterval)
        }
      }, 2000)
      
    } catch (error) {
      console.error('Failed to start bulk requirements analysis:', error)
    }
  }
  
  const handleBulkLegalAnalysis = async () => {
    if (selectedLegalDocs.length === 0) return
    
    try {
      const result = await startBulkLegalAnalysis(selectedLegalDocs, selectedRequirementDocs.length > 0 ? selectedRequirementDocs : undefined)
      setBulkJobStatus(prev => ({...prev, [result.job_id]: 'processing'}))
      
      // Poll for job status  
      const pollInterval = setInterval(async () => {
        try {
          const status = await getBatchJobStatus(result.job_id)
          setBulkJobStatus(prev => ({...prev, [result.job_id]: status.status}))
          
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollInterval)
            // Refresh documents to show updated reports
            const docs = await getDocuments()
            setDocuments(docs)
          }
        } catch (error) {
          console.error('Failed to poll job status:', error)
          clearInterval(pollInterval)
        }
      }, 2000)
      
    } catch (error) {
      console.error('Failed to start bulk legal analysis:', error)
    }
  }
  
  

  const handleDeleteConfirmation = () => {
    if (selectedDocs.length > 0) {
      setIsDeleteDialogOpen(true)
    }
  }

  const handleDeleteDocuments = async () => {
    if (selectedDocs.length === 0) return

    setIsDeleting(true)
    try {
      // Delete documents one by one
      for (const docId of selectedDocs) {
        await deleteDocument(docId)
      }
      
      // Refresh the documents list
      const docs = await getDocuments()
      setDocuments(docs)
      setSelectedDocs([])
      
      console.log('Documents deleted successfully')
    } catch (error) {
      console.error('Failed to delete documents:', error)
      alert('Failed to delete documents. Please try again.')
    } finally {
      setIsDeleting(false)
      setIsDeleteDialogOpen(false)
    }
  }
  
  const handleViewReport = (documentId: string) => {
    const report = documentReports[documentId]
    if (report) {
      setSelectedReport(report)
      setIsReportDialogOpen(true)
    }
  }
  
  const handleRerunAnalysis = async (documentId: string) => {
    const doc = documents.find(d => d.id === documentId)
    if (!doc) return
    
    try {
      // Mark document as rerunning
      setRerunningDocuments(prev => new Set([...prev, documentId]))
      
      // Clear any existing report for this document (keep only latest)
      setDocumentReports(prev => ({
        ...prev,
        [documentId]: null
      }))
      
      // Trigger the same auto-analysis flow as PDF upload
      const autoAnalysisPrompt = `I have uploaded a ${doc.type} document "${doc.name}". Please analyze it for compliance requirements and provide a comprehensive legal analysis.`
      
      // Trigger auto-analysis event (same as PDF upload flow)
      const autoAnalysisEvent = new CustomEvent('autoAnalysisTriggered', {
        detail: {
          prompt: autoAnalysisPrompt,
          documentId: documentId,
          documentName: doc.name,
          documentType: doc.type
        }
      })
      
      // Dispatch the event to trigger the same flow as PDF upload
      window.dispatchEvent(autoAnalysisEvent)
      
      console.log('✅ Rerun analysis triggered for:', doc.name)
      
      // Set up polling to check for analysis completion and refresh the report
      const pollForCompletion = async () => {
        let attempts = 0
        const maxAttempts = 60 // Poll for up to 2 minutes (every 2 seconds)
        
        const pollInterval = setInterval(async () => {
          attempts++
          try {
            const reportData = await getDocumentReport(documentId)
            if (reportData.has_report && reportData.report.status !== 'pending') {
              // Analysis is complete, update the report
              setDocumentReports(prev => ({
                ...prev,
                [documentId]: reportData.report
              }))
              // Remove from rerunning state
              setRerunningDocuments(prev => {
                const newSet = new Set(prev)
                newSet.delete(documentId)
                return newSet
              })
              clearInterval(pollInterval)
              console.log('✅ Analysis complete, report updated for:', doc.name)
            } else if (attempts >= maxAttempts) {
              // Stop polling after max attempts
              setRerunningDocuments(prev => {
                const newSet = new Set(prev)
                newSet.delete(documentId)
                return newSet
              })
              clearInterval(pollInterval)
              console.log('⏱️ Polling timeout for:', doc.name)
            }
          } catch (error) {
            console.error('Error polling for report completion:', error)
            if (attempts >= maxAttempts) {
              setRerunningDocuments(prev => {
                const newSet = new Set(prev)
                newSet.delete(documentId)
                return newSet
              })
              clearInterval(pollInterval)
            }
          }
        }, 2000) // Poll every 2 seconds
      }
      
      // Start polling after a short delay to allow the analysis to start
      setTimeout(pollForCompletion, 3000)
      
    } catch (error) {
      console.error('Failed to rerun analysis:', error)
      // Remove from rerunning state on error
      setRerunningDocuments(prev => {
        const newSet = new Set(prev)
        newSet.delete(documentId)
        return newSet
      })
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <BookOpen className="w-8 h-8" />
              Document Library
            </h1>
            <p className="text-gray-600 mt-2">
              Unified document management and organization
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Input 
              placeholder="Search documents..." 
              className="w-64"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <select 
              className="p-2 border border-gray-300 rounded-md"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as 'all' | 'requirements' | 'legal')}
            >
              <option value="all">All Types</option>
              <option value="requirements">Requirements</option>
              <option value="legal">Legal</option>
            </select>
            <Button variant="outline" size="sm">Sort ▼</Button>
          </div>
        </div>

        {/* Library Stats */}
        <Card className="bg-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-8">
                <div>
                  <p className="text-2xl font-bold text-gray-900">{documents.length}</p>
                  <p className="text-sm text-gray-600">Total Documents</p>
                </div>
                <div>
                  <p className="text-lg font-semibold text-blue-600">{requirementDocs.length}</p>
                  <p className="text-sm text-gray-600">Requirements</p>
                </div>
                <div>
                  <p className="text-lg font-semibold text-purple-600">{legalDocs.length}</p>
                  <p className="text-sm text-gray-600">Legal</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">Storage used: {(totalSize / 1024 / 1024).toFixed(1)}MB / 1GB</p>
                <p className="text-sm text-gray-600">Last upload: 2 hours ago</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Document Table */}
        <Card className="bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                All Documents ({filteredDocuments.length})
              </h2>
              {selectedDocs.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">
                    {selectedDocs.length} selected
                  </span>
                  <Button 
                    variant="outline" 
                    size="sm"
                    disabled={selectedDocs.length === 0 || isDeleting}
                    onClick={handleDeleteConfirmation}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="animate-pulse flex items-center space-x-4">
                    <div className="w-4 h-4 bg-gray-200 rounded"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                      <div className="h-3 bg-gray-100 rounded w-1/6"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <input
                        type="checkbox"
                        checked={selectedDocs.length === filteredDocuments.length && filteredDocuments.length > 0}
                        onChange={handleSelectAll}
                        className="rounded"
                      />
                    </TableHead>
                    <TableHead>Document Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDocuments.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell>
                        <input
                          type="checkbox"
                          checked={selectedDocs.includes(doc.id)}
                          onChange={() => handleDocumentSelect(doc.id)}
                          className="rounded"
                        />
                      </TableCell>
                      <TableCell className="font-medium">{doc.name}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          doc.type === 'requirements' 
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-purple-100 text-purple-700'
                        }`}>
                          {doc.type === 'requirements' ? 'Req' : 'Legal'}
                        </span>
                      </TableCell>
                      <TableCell>{formatDate(doc.uploadDate)}</TableCell>
                      <TableCell>{getStatusBadge(doc.status)}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {documentReports[doc.id] ? (
                            <>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleViewReport(doc.id)}
                              >
                                <Eye className="w-4 h-4 mr-1" />
                                View Report
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleRerunAnalysis(doc.id)}
                                disabled={rerunningDocuments.has(doc.id)}
                              >
                                <RefreshCw className={`w-4 h-4 mr-1 ${rerunningDocuments.has(doc.id) ? 'animate-spin' : ''}`} />
                                {rerunningDocuments.has(doc.id) ? 'Analyzing...' : 'Rerun'}
                              </Button>
                            </>
                          ) : (
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleRerunAnalysis(doc.id)}
                              disabled={rerunningDocuments.has(doc.id)}
                            >
                              <FileText className={`w-4 h-4 mr-1 ${rerunningDocuments.has(doc.id) ? 'animate-spin' : ''}`} />
                              {rerunningDocuments.has(doc.id) ? 'Analyzing...' : 'Analyze'}
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        

        {/* Report Dialog */}
        <Dialog open={isReportDialogOpen} onOpenChange={setIsReportDialogOpen}>
          <DialogContent className="max-w-[90vw] w-full max-h-[85vh] overflow-hidden flex flex-col">
            <DialogHeader>
              <DialogTitle>
                Compliance Report - {selectedReport?.document_name || 'Unknown Document'}
              </DialogTitle>
            </DialogHeader>
            {selectedReport && (
              <div className="flex-1 overflow-y-auto pr-2 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold text-gray-900">Status</h4>
                    <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                      selectedReport.status === 'completed' 
                        ? 'bg-green-100 text-green-700'
                        : selectedReport.status === 'failed'
                        ? 'bg-red-100 text-red-700' 
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {selectedReport.status?.charAt(0).toUpperCase() + selectedReport.status?.slice(1)}
                    </span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Document ID</h4>
                    <p className="text-sm text-gray-600 font-mono">{selectedReport.id}</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Summary</h4>
                  <p className="text-gray-700 text-sm bg-gray-50 p-3 rounded border">
                    {selectedReport.summary || 'No summary available'}
                  </p>
                </div>

                {selectedReport.issues && selectedReport.issues.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Issues Identified</h4>
                    <div className="bg-red-50 border border-red-200 rounded p-3">
                      {selectedReport.issues.map((issue: string, index: number) => (
                        <p key={index} className="text-red-700 text-sm mb-1">
                          • {issue}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {selectedReport.recommendations && selectedReport.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Recommendations</h4>
                    <div className="bg-blue-50 border border-blue-200 rounded p-3">
                      {selectedReport.recommendations.map((rec: string, index: number) => (
                        <p key={index} className="text-blue-700 text-sm mb-1">
                          • {rec}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Raw Report Data</h4>
                  <pre className="text-xs bg-gray-100 p-3 rounded border overflow-auto max-h-48">
                    {JSON.stringify(selectedReport, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Are you sure?</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <p>You are about to delete {selectedDocs.length} document{selectedDocs.length > 1 ? 's' : ''}. This action cannot be undone.</p>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>Cancel</Button>
              <Button variant="destructive" onClick={handleDeleteDocuments} disabled={isDeleting}>
                {isDeleting ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}