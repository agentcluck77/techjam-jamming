import { useState } from 'react'
import { useWorkflowStore } from '@/lib/stores'
import { respondToHITL } from '@/lib/api'
import { HITLResponse } from '@/lib/types'

export const useHITL = () => {
  const [isResponding, setIsResponding] = useState(false)
  const { hitlPrompt, currentWorkflow, setHitlPrompt } = useWorkflowStore()

  const respond = async (response: string) => {
    if (!hitlPrompt || !currentWorkflow) {
      throw new Error('No active HITL prompt or workflow')
    }

    setIsResponding(true)
    
    try {
      const hitlResponse: HITLResponse = {
        promptId: hitlPrompt.promptId,
        response,
        timestamp: new Date().toISOString(),
      }

      await respondToHITL(currentWorkflow.id, hitlResponse)
      
      // Clear the current prompt - new one will come via SSE if needed
      setHitlPrompt(null)
    } catch (error) {
      console.error('Failed to respond to HITL:', error)
      throw error
    } finally {
      setIsResponding(false)
    }
  }

  return {
    hitlPrompt,
    isResponding,
    respond,
  }
}