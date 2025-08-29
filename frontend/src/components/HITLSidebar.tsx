'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { useHITL } from '@/hooks/use-hitl'
import { useWorkflowStore } from '@/lib/stores'
import { cn } from '@/lib/utils'

export function HITLSidebar() {
  const { sidebarOpen, progress, setSidebarOpen } = useWorkflowStore()
  const { hitlPrompt, isResponding, respond } = useHITL()
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [queryMode, setQueryMode] = useState(false)
  const [userQuery, setUserQuery] = useState('')
  const [queryResponse, setQueryResponse] = useState('')
  const [isQuerying, setIsQuerying] = useState(false)

  const handleResponse = async (response: string) => {
    try {
      await respond(response)
      setSelectedOption(null)
    } catch (error) {
      console.error('Failed to respond:', error)
    }
  }

  const handleQuickQuery = async () => {
    if (!userQuery.trim()) return
    
    setIsQuerying(true)
    try {
      const response = await fetch('/api/v1/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userQuery })
      })
      const result = await response.json()
      setQueryResponse(result.response || 'No response received')
    } catch (error) {
      setQueryResponse('Error processing query')
      console.error('Query failed:', error)
    } finally {
      setIsQuerying(false)
    }
  }

  // Always render sidebar, but show/hide with transform
  const isVisible = sidebarOpen || true // Always show for now

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-white border-l border-gray-200 shadow-lg z-50 overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {hitlPrompt || progress ? 'Workflow Assistant' : 'Legal Compliance Assistant'}
          </h2>
          <div className="flex items-center gap-2">
            <Button
              variant={queryMode ? "default" : "ghost"}
              size="sm"
              onClick={() => setQueryMode(!queryMode)}
            >
              💬
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(false)}
            >
              ✕
            </Button>
          </div>
        </div>
        
        {progress && !queryMode && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Step {progress.currentStep} of {progress.totalSteps}</span>
              <span>{progress.progress}%</span>
            </div>
            <Progress value={progress.progress} className="w-full" />
            <p className="text-sm text-gray-700">{progress.message}</p>
          </div>
        )}
      </div>

      <div className="p-4">
        {queryMode ? (
          <Card>
            <CardHeader>
              <h3 className="font-medium text-gray-900">Quick Compliance Query</h3>
              <p className="text-sm text-gray-600">Ask about regulations, requirements, or compliance questions</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="e.g., What are Utah's age verification requirements for social media?"
                value={userQuery}
                onChange={(e) => setUserQuery(e.target.value)}
                className="min-h-[80px]"
              />
              <Button 
                onClick={handleQuickQuery}
                disabled={isQuerying || !userQuery.trim()}
                className="w-full"
              >
                {isQuerying ? 'Analyzing...' : 'Ask Question'}
              </Button>
              
              {queryResponse && (
                <div className="bg-gray-50 p-3 rounded-md">
                  <h4 className="text-sm font-medium text-gray-800 mb-2">Response:</h4>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{queryResponse}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ) : hitlPrompt ? (
          <Card>
            <CardHeader>
              <h3 className="font-medium text-gray-900">Human Input Required</h3>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-700">{hitlPrompt.question}</p>
              
              {hitlPrompt.context && Object.keys(hitlPrompt.context).length > 0 && (
                <div className="bg-gray-50 p-3 rounded-md">
                  <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-2">
                    Context
                  </h4>
                  {Object.entries(hitlPrompt.context).map(([key, value]) => (
                    <div key={key} className="mb-2">
                      <span className="text-xs font-medium text-gray-600">{key}:</span>
                      <p className="text-sm text-gray-800 mt-1">
                        {typeof value === 'string' ? value : JSON.stringify(value)}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <div className="space-y-2">
                {hitlPrompt.options.map((option) => (
                  <Button
                    key={option}
                    variant={selectedOption === option ? "default" : "outline"}
                    className="w-full justify-start"
                    onClick={() => setSelectedOption(option)}
                    disabled={isResponding}
                  >
                    {option}
                  </Button>
                ))}
              </div>

              <Button
                className="w-full"
                onClick={() => selectedOption && handleResponse(selectedOption)}
                disabled={!selectedOption || isResponding}
              >
                {isResponding ? 'Submitting...' : 'Submit Response'}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="text-center py-8">
            <div className="mb-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">💬</span>
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Legal Compliance Assistant</h3>
              <p className="text-sm text-gray-600 mb-4">
                Ready to help with compliance questions and document analysis
              </p>
              <Button 
                onClick={() => setQueryMode(true)}
                className="mb-4"
              >
                Ask a Question
              </Button>
              <div className="text-xs text-gray-500 space-y-1">
                <p>• Upload documents for full workflow analysis</p>
                <p>• Ask quick compliance questions</p>
                <p>• Get regulatory guidance</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}