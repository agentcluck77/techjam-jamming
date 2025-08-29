'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useDocumentStore } from '@/lib/stores'
import { uploadDocument } from '@/lib/api'
import { cn } from '@/lib/utils'

interface DocumentUploadProps {
  documentType: 'requirements' | 'legal'
  onUploadComplete?: (documentId: string) => void
  className?: string
}

export function DocumentUpload({ documentType, onUploadComplete, className }: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [showLibraryPrompt, setShowLibraryPrompt] = useState(false)
  const [uploadedDocument, setUploadedDocument] = useState<{ id: string; name: string } | null>(null)
  const { addDocument, addUploadProgress, updateUploadProgress, removeUploadProgress } = useDocumentStore()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setUploading(true)
    const fileId = `upload-${Date.now()}`

    try {
      // Add upload progress tracking
      addUploadProgress({
        fileId,
        fileName: file.name,
        progress: 0,
        status: 'uploading'
      })

      // Simulate upload progress
      updateUploadProgress(fileId, { progress: 20, status: 'uploading' })

      const document = await uploadDocument(file, documentType)

      updateUploadProgress(fileId, { progress: 80, status: 'processing' })

      // Add to document store
      addDocument(document)
      
      updateUploadProgress(fileId, { progress: 100, status: 'complete' })
      
      // Clean up progress after a short delay
      setTimeout(() => {
        removeUploadProgress(fileId)
      }, 2000)

      // Show library prompt for requirements documents
      if (documentType === 'requirements') {
        setUploadedDocument({ id: document.id, name: document.name })
        setShowLibraryPrompt(true)
      }

      onUploadComplete?.(document.id)
    } catch (error) {
      console.error('Upload failed:', error)
      updateUploadProgress(fileId, { 
        progress: 0, 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Upload failed'
      })
    } finally {
      setUploading(false)
    }
  }, [documentType, onUploadComplete, addDocument, addUploadProgress, updateUploadProgress, removeUploadProgress])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
    disabled: uploading
  })

  const handleLibraryResponse = (addToLibrary: boolean) => {
    setShowLibraryPrompt(false)
    
    if (addToLibrary && uploadedDocument) {
      // Document is already added to store, just continue
      console.log(`Document ${uploadedDocument.name} added to library`)
    }
    
    // Continue with analysis regardless of library choice
    setUploadedDocument(null)
  }

  return (
    <>
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer transition-colors',
          isDragActive ? 'border-blue-500 bg-blue-50' : 'hover:border-gray-400',
          uploading && 'pointer-events-none opacity-50',
          className
        )}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="text-6xl">📄</div>
          
          {isDragActive ? (
            <div>
              <h3 className="text-xl font-medium text-blue-700">Drop the file here</h3>
              <p className="text-gray-600">Release to upload your document</p>
            </div>
          ) : (
            <div>
              <h3 className="text-xl font-medium text-gray-900">
                Drop {documentType === 'requirements' ? 'Requirements PDF' : 'Legal Documents'} Here
              </h3>
              <p className="text-gray-600 mt-2">
                {documentType === 'requirements' 
                  ? '(PRDs, Technical Specs, User Stories)'
                  : '(Acts, Regulations, Amendments, Notices)'
                }
              </p>
              <p className="text-gray-500 mt-4">or click to select files</p>
            </div>
          )}

          {uploading && (
            <div className="space-y-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-sm text-gray-600">Uploading and processing...</p>
            </div>
          )}
          
          <p className="text-sm text-gray-500">
            Supported: PDF, DOCX, TXT | Max: 50MB | Processing: ~30 seconds
          </p>

          {documentType === 'requirements' && (
            <div className="bg-blue-50 p-4 rounded-md">
              <p className="text-sm text-blue-700">
                ✨ We'll extract your requirements and check them automatically
                against all legal regulations across jurisdictions
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Library Prompt Dialog */}
      <Dialog open={showLibraryPrompt} onOpenChange={setShowLibraryPrompt}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Document Uploaded</DialogTitle>
            <DialogDescription>
              ✅ "{uploadedDocument?.name}" uploaded successfully
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <p className="text-sm text-gray-700">
              Add this document to your library for future reference and organization?
            </p>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => handleLibraryResponse(false)}>
              Skip - Just Run Analysis
            </Button>
            <Button onClick={() => handleLibraryResponse(true)}>
              Add to Library
            </Button>
          </DialogFooter>
          
          <p className="text-xs text-gray-500 mt-2">
            Note: You can manage documents later in the Document Library page
          </p>
        </DialogContent>
      </Dialog>
    </>
  )
}