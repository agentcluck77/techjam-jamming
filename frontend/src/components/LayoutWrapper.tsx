'use client'

import { useEffect, useState } from 'react'
import { Navigation } from "@/components/Navigation"
import { HITLSidebar } from "@/components/HITLSidebar"
import { Button } from "@/components/ui/button"
import { MessageSquare } from 'lucide-react'
import { useWorkflowStore, useApiKeyStore } from '@/lib/stores'
import { cn } from '@/lib/utils'

export function LayoutWrapper({
  children,
}: {
  children: React.ReactNode
}) {
  const { sidebarOpen, setSidebarOpen, navigationCollapsed } = useWorkflowStore()
  const { apiKeys } = useApiKeyStore()
  const [sidebarWidth, setSidebarWidth] = useState(320) // Default 320px

  // Listen for sidebar width changes
  useEffect(() => {
    const handleSidebarResize = (event: CustomEvent<{ width: number; open: boolean }>) => {
      setSidebarWidth(event.detail.width)
      // Don't override the store state here, let the sidebar manage it
    }

    window.addEventListener('sidebar-resize', handleSidebarResize as EventListener)
    
    return () => {
      window.removeEventListener('sidebar-resize', handleSidebarResize as EventListener)
    }
  }, [])

  // Calculate dynamic navigation width
  const navigationWidth = navigationCollapsed ? 64 : 256 // w-16 = 64px, w-64 = 256px
  const minMainContentWidth = 400 // Minimum main content width
  const actualSidebarWidth = sidebarOpen ? sidebarWidth : 0
  
  // Ensure main content doesn't get too narrow
  const windowWidth = typeof window !== 'undefined' ? window.innerWidth : 1200
  const availableWidth = windowWidth - navigationWidth
  const maxSidebarWidth = Math.max(280, availableWidth - minMainContentWidth)
  const effectiveSidebarWidth = Math.min(actualSidebarWidth, maxSidebarWidth)

  return (
    <div className="min-h-screen">
      <Navigation />
      <main 
        className={cn(
          "min-h-screen transition-all duration-300 ease-in-out",
          navigationCollapsed ? "ml-16" : "ml-64"
        )}
        style={{ 
          marginRight: sidebarOpen ? `${effectiveSidebarWidth}px` : '0px',
        }}
      >
        {children}
      </main>
      
      {/* Floating button to reopen sidebar when closed */}
      {!sidebarOpen && (
        <Button
          onClick={() => setSidebarOpen(true)}
          className="fixed bottom-6 right-6 h-12 w-12 rounded-full shadow-lg z-50 bg-blue-600 hover:bg-blue-700 text-white"
          size="sm"
          title="Open Legal Chat Assistant"
        >
          <MessageSquare className="w-5 h-5" />
        </Button>
      )}
      
      <HITLSidebar 
        apiKeys={apiKeys}
        onWidthChange={(width, open) => {
          setSidebarWidth(width)
          if (!open) {
            setSidebarOpen(false)
          }
          // Dispatch custom event for any other components that need to listen
          window.dispatchEvent(new CustomEvent('sidebar-resize', { 
            detail: { width, open } 
          }))
        }}
      />
    </div>
  )
}