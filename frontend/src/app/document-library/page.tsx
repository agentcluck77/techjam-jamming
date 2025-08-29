'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useDocumentStore } from '@/lib/stores'
import { getDocuments } from '@/lib/api'
import { Document } from '@/lib/types'

export default function DocumentLibrary() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | 'requirements' | 'legal'>('all')

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

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              📚 Document Library
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
                  <Button size="sm">🔍 Bulk Compliance Check</Button>
                  <Button variant="outline" size="sm">🗂️ Move to Folder</Button>
                  <Button variant="outline" size="sm">🗑️ Delete</Button>
                  <Button variant="outline" size="sm">📤 Export</Button>
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
                        <Button variant="ghost" size="sm">View</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="bg-white">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              🚀 Bulk Operations
            </h2>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg">
                <h3 className="font-medium text-gray-900 mb-2">Requirements Analysis</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Check selected requirements against all legal docs
                </p>
                <Button disabled={selectedDocs.length === 0} size="sm">
                  Run Analysis
                </Button>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-medium text-gray-900 mb-2">Legal Document Review</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Check selected legal docs against all requirements
                </p>
                <Button disabled={selectedDocs.length === 0} size="sm">
                  Run Review
                </Button>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-medium text-gray-900 mb-2">Export Reports</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Export compliance reports for selected documents
                </p>
                <Button disabled={selectedDocs.length === 0} variant="outline" size="sm">
                  Export
                </Button>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-medium text-gray-900 mb-2">Organize Documents</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Move documents to organized folders
                </p>
                <Button disabled={selectedDocs.length === 0} variant="outline" size="sm">
                  Organize
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}