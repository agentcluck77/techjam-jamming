'use client'

import { useState, useRef, useEffect } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { useDocumentStore } from '@/lib/stores'
import { getDocuments } from '@/lib/api'
import { cn } from '@/lib/utils'
import { FileText, Folder } from 'lucide-react'

interface MentionTextareaProps {
  value: string
  onChange: (value: string) => void
  onSubmit?: () => void
  placeholder?: string
  disabled?: boolean
  className?: string
  minHeight?: string
}

export function MentionTextarea({ 
  value, 
  onChange, 
  onSubmit, 
  placeholder,
  disabled,
  className,
  minHeight = 'min-h-[80px]',
  ...props 
}: MentionTextareaProps) {
  const [showMentions, setShowMentions] = useState(false)
  const [mentionQuery, setMentionQuery] = useState('')
  const [mentionStartPos, setMentionStartPos] = useState(0)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { documents, setDocuments } = useDocumentStore()

  // Fetch all documents from backend on component mount
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const allDocs = await getDocuments()
        setDocuments(allDocs)
      } catch (error) {
        console.error('Failed to load documents for mentions:', error)
      }
    }

    // Only load if store is empty
    if (documents.length === 0) {
      loadDocuments()
    }
  }, [])

  // Filter requirements documents based on query
  const filteredDocs = documents.filter(doc => 
    doc.type === 'requirements' && 
    doc.name.toLowerCase().includes(mentionQuery.toLowerCase())
  )

  // Group documents by folder structure (if we want to show hierarchy)
  const groupedDocs = [
    {
      type: 'header',
      label: 'Requirements Documents',
      icon: Folder
    },
    ...filteredDocs.map(doc => ({
      type: 'document',
      document: doc,
      icon: FileText
    }))
  ]

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value
    const cursorPos = e.target.selectionStart

    // Check for @ mention pattern
    const beforeCursor = text.slice(0, cursorPos)
    const atMatch = beforeCursor.match(/@(\w*)$/)

    if (atMatch) {
      setShowMentions(true)
      setMentionQuery(atMatch[1])
      setMentionStartPos(cursorPos - atMatch[0].length)
      setSelectedIndex(0)
    } else {
      setShowMentions(false)
      setMentionQuery('')
    }

    onChange(text)
  }

  const insertMention = (docName: string) => {
    const beforeMention = value.slice(0, mentionStartPos)
    const afterCursor = value.slice(textareaRef.current?.selectionStart || 0)
    const newValue = `${beforeMention}@${docName} ${afterCursor}`
    
    onChange(newValue)
    setShowMentions(false)
    setMentionQuery('')
    
    // Focus back to textarea
    setTimeout(() => {
      textareaRef.current?.focus()
      const newCursorPos = mentionStartPos + docName.length + 2
      textareaRef.current?.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showMentions && filteredDocs.length > 0) {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex(prev => Math.min(prev + 1, filteredDocs.length - 1))
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex(prev => Math.max(prev - 1, 0))
          break
        case 'Enter':
          if (filteredDocs[selectedIndex]) {
            e.preventDefault()
            insertMention(filteredDocs[selectedIndex].name)
          }
          break
        case 'Escape':
          e.preventDefault()
          setShowMentions(false)
          break
      }
    } else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && onSubmit) {
      e.preventDefault()
      onSubmit()
    }
  }


  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          textareaRef.current && !textareaRef.current.contains(event.target as Node)) {
        setShowMentions(false)
      }
    }

    if (showMentions) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showMentions])

  return (
    <div className="relative w-full">
      <Textarea
        {...props}
        ref={textareaRef}
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(minHeight, 'resize-none', className)}
      />
      
      {showMentions && (
        <div
          ref={dropdownRef}
          className="absolute left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-xl max-h-64 overflow-y-auto z-[60]"
          style={{
            bottom: 'calc(100% + 4px)'
          }}
        >
          {/* Header */}
          <div className="px-3 py-2 border-b border-gray-200 flex items-center gap-2">
            <span className="text-xs text-gray-600">@{mentionQuery}</span>
          </div>
          
          {/* Files & Folders section */}
          <div className="px-3 py-1">
            <div className="text-xs text-gray-500 mb-1">Files & Folders</div>
          </div>

          {filteredDocs.length > 0 ? (
            <div className="space-y-1 px-2 pb-2">
              {filteredDocs.map((doc, index) => (
                <button
                  key={doc.id}
                  onClick={() => insertMention(doc.name)}
                  className={cn(
                    "w-full px-2 py-1 text-left rounded flex items-center gap-2 text-sm transition-colors",
                    index === selectedIndex 
                      ? "bg-blue-50 text-blue-700" 
                      : "hover:bg-gray-50 text-gray-700"
                  )}
                >
                  <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="truncate">{doc.name}</div>
                    <div className="text-xs text-gray-500 truncate">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="px-3 py-4 text-center">
              <div className="text-gray-500 text-sm">No requirements documents found</div>
              <div className="text-gray-400 text-xs mt-1">
                Upload a requirements document to mention it here
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}