'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { useDocumentStore, useWorkflowStore } from '@/lib/stores'
import { uploadDocument, uploadLegalDocument, addStoredLegalDocument, StoredLegalDocument } from '@/lib/api'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'
import { FileText, Edit, Link, Building, Sparkles, Lightbulb, CheckCircle } from 'lucide-react'

interface DocumentUploadProps {
  documentType: 'requirements' | 'legal'
  onUploadComplete?: (documentId: string) => void
  className?: string
}

export function DocumentUpload({ documentType, onUploadComplete, className }: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [showLibraryPrompt, setShowLibraryPrompt] = useState(false)
  const [uploadedDocument, setUploadedDocument] = useState<{ id: string; name: string; type: 'file' | 'text'; inputMode: string } | null>(null)
  const [selectedJurisdictions, setSelectedJurisdictions] = useState<string[]>(['Global'])
  const [inputMode, setInputMode] = useState<'file' | 'text' | 'url'>('file')
  const [textContent, setTextContent] = useState('')
  const [urlInput, setUrlInput] = useState('')
  const [jurisdiction, setJurisdiction] = useState('')
  const [lawTitle, setLawTitle] = useState('')
  const [showJurisdictionPrompt, setShowJurisdictionPrompt] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const { addDocument, addUploadProgress, updateUploadProgress, removeUploadProgress } = useDocumentStore()
  const { setSidebarOpen } = useWorkflowStore()

  // Common jurisdictions for quick selection (for legal documents)
  const commonJurisdictions = [
    'Utah', 'California', 'Florida', 'Texas', 'New York',
    'European Union', 'United Kingdom', 'Canada', 'Australia', 
    'Brazil', 'India', 'Singapore', 'Japan', 'South Korea'
  ]

  // Available jurisdictions for requirements analysis
  const availableJurisdictions = [
    'Global', 'Utah', 'California', 'Florida', 'Texas', 'New York',
    'European Union', 'United Kingdom', 'Canada', 'Australia', 
    'Brazil', 'India', 'Singapore', 'Japan', 'South Korea'
  ]

  // API base URL
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // Universal auto-analysis function
  const triggerAutoAnalysis = async (documentInfo: {
    id: string,
    name: string,
    type: 'file' | 'text',
    inputMode: string
  }) => {
    // Show toast notification
    toast.success('Starting compliance analysis...')
    
    // Forcefully open sidebar and ensure it stays open
    console.log('🔧 Force opening sidebar...')
    setSidebarOpen(true)
    
    // Store the auto-analysis prompt for the sidebar to use
    const autoPrompt = `Analyze requirements document '${documentInfo.name}' (ID: ${documentInfo.id}) for compliance across ${selectedJurisdictions.join(', ')}.

Document Details:
- Input Type: ${documentInfo.type === 'file' ? 'File Upload' : 'Text Input'}
- Source: ${documentInfo.inputMode}
- Uploaded: ${new Date().toISOString()}

Please:
1. Extract key requirements using MCP search
2. Check against regulations in: ${selectedJurisdictions.join(', ')}
3. Identify compliance gaps and risks
4. Provide actionable recommendations

Use the requirements MCP to search and analyze the full document content.`

    // Store the prompt in sessionStorage for the sidebar to pick up
    console.log('💾 Storing auto-analysis prompt in sessionStorage...')
    console.log('📝 Prompt:', autoPrompt)
    sessionStorage.setItem('autoAnalysisPrompt', autoPrompt)
    sessionStorage.setItem('autoAnalysisTriggered', 'true')
    
    // Verify storage
    console.log('✅ sessionStorage set:', {
      autoAnalysisTriggered: sessionStorage.getItem('autoAnalysisTriggered'),
      hasPrompt: !!sessionStorage.getItem('autoAnalysisPrompt')
    })
    
    console.log('📡 Dispatching auto-analysis event...')
    
    // Dispatch a custom event to trigger the sidebar immediately
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('autoAnalysisTriggered', {
        detail: { prompt: autoPrompt }
      }))
      console.log('🚀 Auto-analysis event dispatched!')
    }, 100)
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // For legal documents, show jurisdiction prompt first
    if (documentType === 'legal') {
      setPendingFile(file)
      setShowJurisdictionPrompt(true)
      return
    }

    // For requirements documents, upload directly
    await processUpload(file)
  }, [documentType])

  const processUpload = async (file: File, selectedJurisdiction?: string) => {
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

      if (documentType === 'legal' && selectedJurisdiction && lawTitle) {
        // Use Legal MCP API for legal documents
        updateUploadProgress(fileId, { progress: 40, status: 'uploading to Legal MCP' })
        
        const mcpResponse = await uploadLegalDocument(file, selectedJurisdiction, lawTitle)
        
        updateUploadProgress(fileId, { progress: 80, status: 'storing in database' })
        
        // Store document information locally
        const documentId = `legal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        const storedDocument: StoredLegalDocument = {
          id: documentId,
          filename: file.name,
          jurisdiction: selectedJurisdiction,
          statute: lawTitle,
          uploadDate: new Date().toISOString(),
          status: 'stored',
          mcpResponse
        }
        
        addStoredLegalDocument(storedDocument)
        
        toast.success(`Legal document uploaded to ${selectedJurisdiction} jurisdiction`)
        
        updateUploadProgress(fileId, { progress: 100, status: 'complete' })
        
        // Clean up progress after a short delay
        setTimeout(() => {
          removeUploadProgress(fileId)
        }, 2000)

        onUploadComplete?.(documentId)
      } else {
        // Use regular API for requirements documents
        const metadata: any = {}
        if (selectedJurisdiction) metadata.jurisdiction = selectedJurisdiction
        if (lawTitle && documentType === 'legal') metadata.law_title = lawTitle

        const document = await uploadDocument(file, documentType, metadata)

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
          setUploadedDocument({ 
            id: document.id, 
            name: document.name,
            type: 'file',
            inputMode: 'file'
          })
          setShowLibraryPrompt(true)
        }

        onUploadComplete?.(document.id)
      }
    } catch (error) {
      console.error('Upload failed:', error)
      updateUploadProgress(fileId, { 
        progress: 0, 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Upload failed'
      })
      toast.error(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setUploading(false)
    }
  }

  const handleTextUpload = async () => {
    if (!textContent.trim()) return
    
    // For legal documents, show jurisdiction prompt first
    if (documentType === 'legal') {
      const textBlob = new File([textContent], `legal-document-${Date.now()}.txt`, { type: 'text/plain' })
      setPendingFile(textBlob)
      setShowJurisdictionPrompt(true)
      return
    }

    // For requirements documents, upload directly and show library prompt
    const fileName = `requirements-${Date.now()}.txt`
    const textBlob = new File([textContent], fileName, { type: 'text/plain' })
    
    try {
      const document = await uploadDocument(textBlob, documentType)
      
      // Show library prompt for requirements documents
      if (documentType === 'requirements') {
        setUploadedDocument({ 
          id: document.id, 
          name: fileName,
          type: 'text',
          inputMode: 'text'
        })
        setShowLibraryPrompt(true)
      }
      
      setTextContent('') // Clear text after upload
    } catch (error) {
      console.error('Text upload failed:', error)
      toast.error('Failed to upload text content')
    }
  }

  const handleUrlUpload = async (selectedJurisdiction?: string) => {
    if (!urlInput.trim()) return
    
    setUploading(true)
    const fileId = `url-upload-${Date.now()}`
    
    try {
      addUploadProgress({
        fileId,
        fileName: `URL: ${urlInput}`,
        progress: 0,
        status: 'uploading'
      })

      updateUploadProgress(fileId, { progress: 20, status: 'processing' })

      // Call backend API to fetch and process URL
      const requestBody: any = { 
        url: urlInput, 
        doc_type: documentType 
      }

      // Add jurisdiction and law title to metadata for legal documents
      if (documentType === 'legal') {
        requestBody.metadata = {}
        if (selectedJurisdiction) requestBody.metadata.jurisdiction = selectedJurisdiction
        if (lawTitle) requestBody.metadata.law_title = lawTitle
      }

      const response = await fetch('/api/documents/upload-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error('Failed to fetch from URL')
      }

      const document = await response.json()
      
      updateUploadProgress(fileId, { progress: 80, status: 'processing' })
      addDocument(document)
      updateUploadProgress(fileId, { progress: 100, status: 'complete' })
      
      setTimeout(() => {
        removeUploadProgress(fileId)
      }, 2000)

      // Show library prompt for requirements documents
      if (documentType === 'requirements') {
        setUploadedDocument({ 
          id: document.id, 
          name: document.name,
          type: 'file',
          inputMode: 'file'
        })
        setShowLibraryPrompt(true)
      }

      onUploadComplete?.(document.id)
      setUrlInput('') // Clear URL after upload
    } catch (error) {
      console.error('URL upload failed:', error)
      updateUploadProgress(fileId, { 
        progress: 0, 
        status: 'error', 
        error: error instanceof Error ? error.message : 'URL fetch failed'
      })
    } finally {
      setUploading(false)
    }
  }

  const handleJurisdictionConfirm = async () => {
    if (!jurisdiction.trim() || !lawTitle.trim()) return

    setShowJurisdictionPrompt(false)
    
    if (inputMode === 'url') {
      await handleUrlUpload(jurisdiction)
    } else if (pendingFile) {
      await processUpload(pendingFile, jurisdiction)
      if (inputMode === 'text') {
        setTextContent('') // Clear text after upload
      }
    }

    // Reset state
    setPendingFile(null)
    setJurisdiction('')
    setLawTitle('')
  }

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
    console.log('🎯 handleLibraryResponse called:', { addToLibrary, uploadedDocument, selectedJurisdictions })
    setShowLibraryPrompt(false)
    
    if (uploadedDocument) {
      if (addToLibrary) {
        console.log(`Document ${uploadedDocument.name} added to library`)
      }
      
      console.log('📞 About to trigger auto-analysis...')
      // Trigger analysis for both options
      triggerAutoAnalysis(uploadedDocument)
    } else {
      console.log('❌ No uploaded document to analyze')
    }
    
    // Reset states
    setUploadedDocument(null)
    setSelectedJurisdictions(['Global'])
  }

  return (
    <>
      {/* Mode Toggle */}
      <div className="flex items-center justify-center mb-4">
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setInputMode('file')}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-colors',
              inputMode === 'file' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <FileText className="w-4 h-4 mr-2" />
            Upload File
          </button>
          <button
            onClick={() => setInputMode('text')}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-colors',
              inputMode === 'text' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <Edit className="w-4 h-4 mr-2" />
            Text Input
          </button>
          {documentType === 'legal' && (
            <button
              onClick={() => setInputMode('url')}
              className={cn(
                'px-4 py-2 rounded-md text-sm font-medium transition-colors',
                inputMode === 'url' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              )}
            >
              <Link className="w-4 h-4 mr-2" />
              From URL
            </button>
          )}
        </div>
      </div>

      {inputMode === 'file' ? (
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
          <div className="flex justify-center mb-4">
            <FileText className="w-16 h-16 text-gray-400" />
          </div>
          
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
                <Sparkles className="w-4 h-4 inline mr-1" />
                We'll extract your requirements and check them automatically
                against all legal regulations across jurisdictions
              </p>
            </div>
          )}

          {documentType === 'legal' && (
            <div className="bg-amber-50 p-4 rounded-md">
              <p className="text-sm text-amber-700">
                <Building className="w-4 h-4 inline mr-1" />
                You'll be asked to specify the jurisdiction for this legal document
                to improve compliance analysis accuracy
              </p>
            </div>
          )}
        </div>
        </div>
      ) : inputMode === 'url' ? (
        <div className={cn(
          'border-2 border-gray-300 rounded-lg p-6',
          uploading && 'opacity-50 pointer-events-none',
          className
        )}>
          <div className="space-y-4">
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <Link className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-xl font-medium text-gray-900">
                Import Legal Document from URL
              </h3>
              <p className="text-gray-600 mt-2">
                Enter a URL to legal acts, regulations, or official documents
              </p>
            </div>

            <div className="space-y-4">
              <Input
                placeholder="https://example.com/legal-document.pdf or https://laws.gov/act-name"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                disabled={uploading}
                className="text-sm"
              />

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">
                  Supports: PDFs, HTML pages, government sites
                </span>
                <Button
                  onClick={() => {
                    if (documentType === 'legal') {
                      setShowJurisdictionPrompt(true)
                    } else {
                      handleUrlUpload()
                    }
                  }}
                  disabled={!urlInput.trim() || uploading}
                >
                  {uploading ? 'Fetching...' : 'Import from URL'}
                </Button>
              </div>
            </div>

            {uploading && (
              <div className="space-y-2">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-600 text-center">Fetching document from URL...</p>
              </div>
            )}

            <div className="bg-green-50 p-4 rounded-md">
              <p className="text-sm text-green-700">
                <Lightbulb className="w-4 h-4 inline mr-1" />
                Examples: Government legislation sites, PDF acts, official legal documents
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className={cn(
          'border-2 border-gray-300 rounded-lg p-6',
          uploading && 'opacity-50 pointer-events-none',
          className
        )}>
          <div className="space-y-4">
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <Edit className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-xl font-medium text-gray-900">
                Paste {documentType === 'requirements' ? 'Requirements' : 'Legal Document'} Text
              </h3>
              <p className="text-gray-600 mt-2">
                {documentType === 'requirements' 
                  ? 'Enter PRDs, Technical Specs, or User Stories directly'
                  : 'Enter legal document text, acts, or regulations'
                }
              </p>
            </div>

            <Textarea
              placeholder={documentType === 'requirements' 
                ? 'Paste your requirements here...\n\nExample:\n• Live shopping feature with real-time payments\n• Age verification for users under 18\n• Content moderation with 24-hour response time'
                : 'Paste your legal document text here...'
              }
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              className="min-h-[200px] resize-none"
              disabled={uploading}
            />

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">
                {textContent.length} characters • {textContent.split('\n').length} lines
              </span>
              <Button
                onClick={handleTextUpload}
                disabled={!textContent.trim() || uploading}
              >
                {uploading ? 'Processing...' : 'Process Text'}
              </Button>
            </div>

            {uploading && (
              <div className="space-y-2">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-600 text-center">Processing text input...</p>
              </div>
            )}

            {documentType === 'requirements' && (
              <div className="bg-blue-50 p-4 rounded-md">
                <p className="text-sm text-blue-700">
                  <Sparkles className="w-4 h-4 inline mr-1" />
                  We'll analyze your requirements and check them automatically
                  against all legal regulations across jurisdictions
                </p>
              </div>
            )}

            {documentType === 'legal' && (
              <div className="bg-amber-50 p-4 rounded-md">
                <p className="text-sm text-amber-700">
                  <Building className="w-4 h-4 inline mr-1" />
                  You'll be asked to specify the jurisdiction for this legal document
                  to improve compliance analysis accuracy
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Jurisdiction Prompt Dialog */}
      <Dialog open={showJurisdictionPrompt} onOpenChange={setShowJurisdictionPrompt}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Building className="w-5 h-5" />
              Legal Document Details
            </DialogTitle>
            <DialogDescription>
              Please provide the law title and jurisdiction to help improve compliance analysis accuracy.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Law Title <span className="text-red-500">*</span>
              </label>
              <Input
                placeholder="e.g., Utah Social Media Regulation Act 2025, GDPR, California Consumer Privacy Act"
                value={lawTitle}
                onChange={(e) => setLawTitle(e.target.value)}
                className="w-full"
              />
              <p className="text-xs text-gray-500">
                Enter the official name of the law, act, or regulation
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Jurisdiction <span className="text-red-500">*</span> - Select from common jurisdictions:
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {commonJurisdictions.map((jur) => (
                  <Button
                    key={jur}
                    variant={jurisdiction === jur ? "default" : "outline"}
                    size="sm"
                    onClick={() => setJurisdiction(jur)}
                    className="justify-start"
                  >
                    {jur}
                  </Button>
                ))}
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Or enter custom jurisdiction:
              </label>
              <Input
                placeholder="e.g., Netherlands, Ontario (Canada), Cook County (Illinois), etc."
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                className="w-full"
              />
              <p className="text-xs text-gray-500">
                Be as specific as needed (state, province, county, city)
              </p>
            </div>
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button variant="outline" onClick={() => {
              setShowJurisdictionPrompt(false)
              setJurisdiction('')
              setLawTitle('')
              setPendingFile(null)
            }} className="w-full sm:w-auto">
              Cancel
            </Button>
            <Button 
              onClick={handleJurisdictionConfirm} 
              disabled={!jurisdiction.trim() || !lawTitle.trim()}
              className="w-full sm:w-auto"
            >
              Continue Upload
            </Button>
          </DialogFooter>
          
          <p className="text-xs text-gray-500 mt-2 text-center">
            <Lightbulb className="w-4 h-4 inline mr-1" />
            Law title and jurisdiction help the AI provide more accurate compliance analysis
          </p>
        </DialogContent>
      </Dialog>

      {/* Library Prompt Dialog */}
      <Dialog open={showLibraryPrompt} onOpenChange={setShowLibraryPrompt}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Document Uploaded</DialogTitle>
            <DialogDescription>
              <CheckCircle className="w-4 h-4 inline mr-1" />
              "{uploadedDocument?.name}" uploaded successfully
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-4">
            <p className="text-sm text-gray-700">
              Add this document to your library for future reference and organization?
            </p>
            
            {/* Jurisdiction Selection for Requirements Analysis */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700">
                Select Jurisdictions for Compliance Analysis:
              </label>
              <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto border rounded-md p-2 bg-gray-50">
                {availableJurisdictions.map((jurisdiction) => (
                  <label key={jurisdiction} className="flex items-center text-xs">
                    <input
                      type="checkbox"
                      checked={selectedJurisdictions.includes(jurisdiction)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedJurisdictions(prev => [...prev, jurisdiction])
                        } else {
                          setSelectedJurisdictions(prev => prev.filter(j => j !== jurisdiction))
                        }
                      }}
                      className="mr-2"
                    />
                    <span>{jurisdiction}</span>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-500">
                Selected jurisdictions: {selectedJurisdictions.length === 0 ? 'None' : selectedJurisdictions.join(', ')}
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => handleLibraryResponse(false)}
              disabled={selectedJurisdictions.length === 0}
            >
              Analysis Only
            </Button>
            <Button 
              onClick={() => handleLibraryResponse(true)}
              disabled={selectedJurisdictions.length === 0}
            >
              Analyse and Add to Library
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