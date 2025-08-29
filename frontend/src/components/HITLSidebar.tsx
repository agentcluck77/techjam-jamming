'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { useHITL } from '@/hooks/use-hitl'
import { useWorkflowStore } from '@/lib/stores'
import { cn } from '@/lib/utils'

export function HITLSidebar() {
  const { sidebarOpen, progress, setSidebarOpen } = useWorkflowStore()
  const { hitlPrompt, isResponding, respond } = useHITL()
  const [selectedOption, setSelectedOption] = useState<string | null>(null)

  const handleResponse = async (response: string) => {
    try {
      await respond(response)
      setSelectedOption(null)
    } catch (error) {
      console.error('Failed to respond:', error)
    }
  }

  if (!sidebarOpen) return null

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-white border-l border-gray-200 shadow-lg z-50 overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Workflow Progress</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(false)}
          >
            ✕
          </Button>
        </div>
        
        {progress && (
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
        {hitlPrompt ? (
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
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-sm text-gray-500">Processing workflow...</p>
          </div>
        )}
      </div>
    </div>
  )
}