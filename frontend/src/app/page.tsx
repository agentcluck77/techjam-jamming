'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DocumentUpload } from '@/components/DocumentUpload'
import { useDocumentStore } from '@/lib/stores'
import { getRecentDocuments } from '@/lib/api'
import { Document } from '@/lib/types'
import { CheckSquare, Clock, Settings, CheckCircle, Loader2, FileText } from 'lucide-react'

export default function RequirementsCheck() {
  const [recentUploads, setRecentUploads] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadRecentUploads = async () => {
      try {
        const documents = await getRecentDocuments(5)
        setRecentUploads(documents.filter(doc => doc.type === 'requirements'))
      } catch (error) {
        console.error('Failed to load recent uploads:', error)
      } finally {
        setLoading(false)
      }
    }

    loadRecentUploads()
  }, [])

        const handleUploadComplete = (documentId: string) => {
        // All analysis now handled by lawyer agent in DocumentUpload component
        console.log('📋 Document upload completed:', documentId)
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

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <CheckSquare className="w-8 h-8" />
              Requirements Compliance Check
            </h1>
            <p className="text-gray-600 mt-2">
              Streamlined requirements PDF compliance checking
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">Recent</Button>
            <Button variant="outline" size="sm">Help</Button>
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Main Upload Area */}
        <Card className="bg-white">
          <CardContent className="p-8">
            <DocumentUpload
              documentType="requirements"
              onUploadComplete={handleUploadComplete}
              className="min-h-[400px]"
            />
          </CardContent>
        </Card>

        {/* Recent Checks */}
        <Card className="bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Recent Compliance Checks
              </h2>
              <Button variant="ghost" size="sm">
                View All →
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-100 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : recentUploads.length > 0 ? (
              <div className="space-y-3">
                {recentUploads.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-900">
                        {doc.name}
                      </span>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        doc.status === 'analyzed' 
                          ? 'bg-green-100 text-green-700' 
                          : doc.status === 'processing'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {doc.status === 'analyzed' ? (
                          <span className="flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" />
                            Analyzed
                          </span>
                        ) : doc.status === 'processing' ? (
                          <span className="flex items-center gap-1">
                            <Loader2 className="w-3 h-3 animate-spin" />
                            Processing
                          </span>
                        ) : (
                          <span className="flex items-center gap-1">
                            <FileText className="w-3 h-3" />
                            Pending
                          </span>
                        )}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-500">
                        {formatTimeAgo(doc.uploadDate)}
                      </span>
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No recent compliance checks yet.</p>
                <p className="text-sm mt-1">Upload your first requirements document above to get started.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
