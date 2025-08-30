'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DocumentUpload } from '@/components/DocumentUpload'
import ApiKeyManager from '@/components/ApiKeyManager'
import { useDocumentStore } from '@/lib/stores'
import { getRecentDocuments } from '@/lib/api'
import { Document } from '@/lib/types'
import { CheckSquare, Clock, Settings, CheckCircle, Loader2, FileText } from 'lucide-react'

export default function RequirementsCheck() {
  const [recentUploads, setRecentUploads] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [apiKeys, setApiKeys] = useState<any>({})

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
            <ApiKeyManager onApiKeysChange={setApiKeys} />
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

      </div>
    </div>
  )
}
