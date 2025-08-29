'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DocumentUpload } from '@/components/DocumentUpload'
import { useWorkflow } from '@/hooks/use-workflow'
import { useDocumentStore } from '@/lib/stores'
import { getDocuments } from '@/lib/api'
import { Document } from '@/lib/types'

export default function LegalDocuments() {
  const [legalDocuments, setLegalDocuments] = useState<Document[]>([])
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const { startNewWorkflow } = useWorkflow()

  useEffect(() => {
    const loadLegalDocuments = async () => {
      try {
        const documents = await getDocuments({ type: 'legal' })
        setLegalDocuments(documents)
      } catch (error) {
        console.error('Failed to load legal documents:', error)
      } finally {
        setLoading(false)
      }
    }

    loadLegalDocuments()
  }, [])

  const handleUploadComplete = async (documentId: string) => {
    // Refresh the document list
    const documents = await getDocuments({ type: 'legal' })
    setLegalDocuments(documents)
  }

  const handleDocumentSelect = (docId: string) => {
    setSelectedDocs(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    )
  }

  const handleStartWorkflow1 = async () => {
    if (selectedDocs.length === 0) return
    
    try {
      // For now, start workflow with the first selected document
      await startNewWorkflow('workflow_1', selectedDocs[0])
    } catch (error) {
      console.error('Failed to start workflow 1:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'analyzed': return '✅'
      case 'stored': return '✅'
      case 'processing': return '🔄'
      case 'pending': return '📋'
      default: return '📋'
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
              🏛️ Legal Documents Workflow
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
              📤 Upload Legal Documents
            </h2>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <DocumentUpload
                  documentType="legal"
                  onUploadComplete={handleUploadComplete}
                  className="min-h-[200px]"
                />
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Document Type
                  </label>
                  <select className="w-full p-2 border border-gray-300 rounded-md">
                    <option>Regulation</option>
                    <option>Act</option>
                    <option>Amendment</option>
                    <option>Notice</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Jurisdiction
                  </label>
                  <select className="w-full p-2 border border-gray-300 rounded-md">
                    <option>Utah</option>
                    <option>EU</option>
                    <option>California</option>
                    <option>Florida</option>
                    <option>Brazil</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Effective Date
                  </label>
                  <Input type="date" defaultValue="2025-01-15" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Legal Documents */}
        <Card className="bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                📋 Recent Legal Documents ({legalDocuments.length} documents)
              </h2>
              <Button variant="ghost" size="sm">
                Manage All →
              </Button>
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
            ) : legalDocuments.length > 0 ? (
              <div className="space-y-3">
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
                
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">
                      Selected: {selectedDocs.length} documents
                    </span>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleStartWorkflow1}
                        disabled={selectedDocs.length === 0}
                        size="sm"
                      >
                        🔍 Run Compliance Check
                      </Button>
                      <Button variant="outline" size="sm" disabled={selectedDocs.length === 0}>
                        🗑️ Delete
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No legal documents uploaded yet.</p>
                <p className="text-sm mt-1">Upload your first legal document above to get started.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Workflow Actions */}
        <Card className="bg-white">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              🔄 Available Workflows
            </h2>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="border rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-2">
                Workflow 1: Check Requirements Compliance
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                • Select legal documents above<br />
                • Analysis checks all existing requirements against these laws<br />
              </p>
              <Button
                onClick={handleStartWorkflow1}
                disabled={selectedDocs.length === 0}
                variant={selectedDocs.length > 0 ? "default" : "outline"}
              >
                Start Workflow 1 {selectedDocs.length === 0 && "(Requires: 1+ legal docs selected)"}
              </Button>
            </div>

            <div className="border rounded-lg p-4 bg-gray-50">
              <h3 className="font-medium text-gray-900 mb-2">
                Workflow 2: Past Iteration Management
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                • Automatically triggered during upload<br />
                • Detects and manages outdated law versions<br />
                • HITL prompts guide deletion decisions
              </p>
              <p className="text-sm text-blue-600">
                This workflow runs automatically when you upload legal documents
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}