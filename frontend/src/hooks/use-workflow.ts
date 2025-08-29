import { useEffect } from 'react'
import { useWorkflowStore } from '@/lib/stores'
import { useSSE } from './use-sse'
import { startWorkflow, getWorkflowStatus } from '@/lib/api'
import { WorkflowProgress, HITLPrompt } from '@/lib/types'

export const useWorkflow = (workflowId?: string) => {
  const {
    currentWorkflow,
    progress,
    sidebarOpen,
    hitlPrompt,
    setCurrentWorkflow,
    setProgress,
    setSidebarOpen,
    setHitlPrompt,
  } = useWorkflowStore()

  // SSE connection for workflow progress
  useSSE(
    workflowId ? `/api/workflow/${workflowId}/progress` : '',
    {
      enabled: !!workflowId,
      onMessage: (data) => {
        if (data.type === 'progress') {
          const progressData: WorkflowProgress = data.payload
          setProgress(progressData)
        } else if (data.type === 'hitl_prompt') {
          const promptData: HITLPrompt = data.payload
          setHitlPrompt(promptData)
          setSidebarOpen(true)
        } else if (data.type === 'workflow_complete') {
          setSidebarOpen(false)
          setProgress(null)
          setHitlPrompt(null)
        }
      },
      onError: (error) => {
        console.error('Workflow SSE error:', error)
      },
    }
  )

  const startNewWorkflow = async (workflowType: string, documentId: string) => {
    try {
      const workflow = await startWorkflow(workflowType, documentId)
      setCurrentWorkflow(workflow)
      setSidebarOpen(true)
      return workflow
    } catch (error) {
      console.error('Failed to start workflow:', error)
      throw error
    }
  }

  const updateWorkflowStatus = async (workflowId: string) => {
    try {
      const workflow = await getWorkflowStatus(workflowId)
      setCurrentWorkflow(workflow)
      return workflow
    } catch (error) {
      console.error('Failed to get workflow status:', error)
      throw error
    }
  }

  const closeSidebar = () => {
    setSidebarOpen(false)
    setHitlPrompt(null)
  }

  return {
    currentWorkflow,
    progress,
    sidebarOpen,
    hitlPrompt,
    startNewWorkflow,
    updateWorkflowStatus,
    closeSidebar,
  }
}