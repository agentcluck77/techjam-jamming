'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DocumentUpload } from '@/components/DocumentUpload'
import { useDocumentStore } from '@/lib/stores'
import { getDocuments, getStoredLegalDocuments, removeStoredLegalDocument, StoredLegalDocument, getLegalMCPDocuments, deleteLegalMCPDocument } from '@/lib/api'
import { Document } from '@/lib/types'
import { Building, Upload, FileText, Loader2, CheckCircle, Search, Trash2, RotateCcw } from 'lucide-react'

export default function LegalDocuments() {
  const [legalDocuments, setLegalDocuments] = useState<Document[]>([])
  const [storedLegalDocuments, setStoredLegalDocuments] = useState<StoredLegalDocument[]>([])
  const [mcpDocuments, setMcpDocuments] = useState<{ region: string; statute: string; chunks: number; uploadDate: string }[]>([])
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])
  const [selectedMcpDocs, setSelectedMcpDocs] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)
  // Legacy workflow removed - all analysis now handled by lawyer agent

  useEffect(() => {
    const loadLegalDocuments = async () => {
      try {
        // Load regular documents from API
        const documents = await getDocuments({ type: 'legal' })
        setLegalDocuments(documents)
        
        // Load stored legal documents from localStorage (Legal MCP uploads)
        const storedDocuments = getStoredLegalDocuments()
        setStoredLegalDocuments(storedDocuments)
        
        // Load documents from Legal MCP database
        const mcpDocs = await getLegalMCPDocuments()
        setMcpDocuments(mcpDocs)
      } catch (error) {
        console.error('Failed to load legal documents:', error)
      } finally {
        setLoading(false)
      }
    }

    loadLegalDocuments()
  }, [])

  const handleUploadComplete = async (documentId: string) => {
    // Refresh all document lists
    const documents = await getDocuments({ type: 'legal' })
    setLegalDocuments(documents)
    
    const storedDocuments = getStoredLegalDocuments()
    setStoredLegalDocuments(storedDocuments)
    
    const mcpDocs = await getLegalMCPDocuments()
    setMcpDocuments(mcpDocs)
  }

  const handleDocumentSelect = (docId: string) => {
    setSelectedDocs(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    )
  }

  const handleMcpDocumentSelect = (docKey: string) => {
    setSelectedMcpDocs(prev => 
      prev.includes(docKey) 
        ? prev.filter(key => key !== docKey)
        : [...prev, docKey]
    )
  }

  const handleDeleteMcpDocuments = async () => {
    if (selectedMcpDocs.length === 0 && selectedDocs.length === 0) return
    
    setDeleting(true)
    try {
      // Delete selected MCP documents
      for (const docKey of selectedMcpDocs) {
        const doc = mcpDocuments.find(d => `${d.region}-${d.statute}` === docKey)
        if (doc) {
          await deleteLegalMCPDocument(doc.region, doc.statute)
        }
      }
      
      // Delete selected regular documents (if any - placeholder for now)
      // Note: Regular document deletion would need to be implemented in the main API
      if (selectedDocs.length > 0) {
        console.log('Regular document deletion not yet implemented:', selectedDocs)
      }
      
      // Refresh the document lists
      const mcpDocs = await getLegalMCPDocuments()
      setMcpDocuments(mcpDocs)
      setSelectedMcpDocs([])
      setSelectedDocs([])
    } catch (error) {
      console.error('Failed to delete documents:', error)
    } finally {
      setDeleting(false)
    }
  }

  const handleStartWorkflow1 = async () => {
    if (selectedDocs.length === 0) return
    
    try {
      // For now, start workflow with the first selected document
      // Legacy workflow removed - analysis handled by lawyer agent
      console.log('Analysis request for document:', selectedDocs[0])
    } catch (error) {
      console.error('Failed to start workflow 1:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'analyzed': return <CheckCircle className="w-4 h-4" />
      case 'stored': return <CheckCircle className="w-4 h-4" />
      case 'processing': return <Loader2 className="w-4 h-4 animate-spin" />
      case 'pending': return <FileText className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'analyzed': return 'Analyzed'
      case 'stored': return 'Stored, ready for compliance'
      case 'processing': return 'Processing...'
      case 'pending': return 'Pending'
      default: return 'Unknown'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Building className="w-8 h-8" />
              Legal Documents Workflow
            </h1>
            <p className="text-gray-600 mt-2">
              Full legal document workflow for legal team
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Input placeholder="Search documents..." className="w-64" />
            <Button variant="outline" size="sm">Filter</Button>
            <Button variant="outline" size="sm">Batch ▼</Button>
          </div>
        </div>

        {/* Upload & Process Section */}
        <Card className="bg-white">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Upload className="w-5 h-5 mr-2" />
              Upload Legal Documents
            </h2>
          </CardHeader>
          <CardContent>
            <DocumentUpload
              documentType="legal"
              onUploadComplete={handleUploadComplete}
              className="min-h-[200px]"
            />
          </CardContent>
        </Card>

        {/* Legal Documents */}
        <Card className="bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <FileText className="w-5 h-5 mr-2" />
                Legal Documents ({legalDocuments.length + mcpDocuments.length} documents)
              </h2>
              <div className="flex items-center gap-2">
                {(selectedDocs.length > 0 || selectedMcpDocs.length > 0) && (
                  <span className="text-sm text-gray-600">
                    Selected: {selectedDocs.length + selectedMcpDocs.length}
                  </span>
                )}
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleDeleteMcpDocuments}
                  disabled={(selectedDocs.length === 0 && selectedMcpDocs.length === 0) || deleting}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  {deleting ? 'Deleting...' : 'Delete Selected'}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-16 bg-gray-200 rounded mb-3"></div>
                  </div>
                ))}
              </div>
            ) : legalDocuments.length > 0 || mcpDocuments.length > 0 ? (
              <div className="space-y-3">
                {/* Legal MCP Database Documents Section */}
                {mcpDocuments.length > 0 && (
                  <>
                    <div className="mb-3">
                      <h3 className="text-sm font-medium text-green-700 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        Legal MCP Database ({mcpDocuments.length} statutes, {mcpDocuments.reduce((sum, doc) => sum + doc.chunks, 0)} chunks)
                      </h3>
                    </div>
                    {mcpDocuments.map((doc, index) => {
                      const docKey = `${doc.region}-${doc.statute}`
                      return (
                        <div key={`mcp-${index}`} className="p-4 border-2 border-green-100 bg-green-50 rounded-lg">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <input
                                type="checkbox"
                                checked={selectedMcpDocs.includes(docKey)}
                                onChange={() => handleMcpDocumentSelect(docKey)}
                                className="rounded"
                              />
                              <div>
                                <h3 className="font-medium text-gray-900">{doc.statute}</h3>
                                <p className="text-sm text-green-600 flex items-center gap-2">
                                  <span><Building className="w-4 h-4" /></span>
                                  <span>Jurisdiction: {doc.region}</span>
                                </p>
                                <p className="text-sm text-gray-600">
                                  {doc.chunks} chunks available for search
                                </p>
                                <p className="text-xs text-gray-500">
                                  Uploaded: {new Date(doc.uploadDate).toLocaleDateString()} {new Date(doc.uploadDate).toLocaleTimeString()}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </>
                )}


                {/* Regular Documents Section */}
                {legalDocuments.length > 0 && (
                  <>
                    {mcpDocuments.length > 0 && (
                      <div className="mb-3 mt-6">
                        <h3 className="text-sm font-medium text-gray-700">
                          Regular Documents ({legalDocuments.length})
                        </h3>
                      </div>
                    )}
                    {legalDocuments.slice(0, 5).map((doc) => (
                      <div key={doc.id} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={selectedDocs.includes(doc.id)}
                              onChange={() => handleDocumentSelect(doc.id)}
                              className="rounded"
                            />
                            <div>
                              <h3 className="font-medium text-gray-900">{doc.name}</h3>
                              <p className="text-sm text-gray-600 flex items-center gap-2">
                                <span>{getStatusIcon(doc.status)}</span>
                                <span>{getStatusText(doc.status)}</span>
                              </p>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm">
                            View
                          </Button>
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No legal documents uploaded yet.</p>
                <p className="text-sm mt-1">Upload your first legal document above to get started.</p>
              </div>
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  )
}