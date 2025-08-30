'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect } from 'react'
import { cn } from '@/lib/utils'
import { CheckSquare, Building, BookOpen, Brain, BarChart3, Menu, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useWorkflowStore } from '@/lib/stores'

const navigationItems = [
  { href: '/', label: 'Requirements Check', icon: CheckSquare },
  { href: '/legal-documents', label: 'Legal Documents', icon: Building },
  { href: '/document-library', label: 'Document Library', icon: BookOpen },
  { href: '/knowledge-base', label: 'Knowledge Base', icon: Brain },
  { href: '/results', label: 'Results History', icon: BarChart3 },
]

export function Navigation() {
  const pathname = usePathname()
  const { navigationCollapsed, setNavigationCollapsed } = useWorkflowStore()

  // Auto-collapse on small screens
  useEffect(() => {
    const checkScreenSize = () => {
      const isSmallScreen = window.innerWidth < 1024 // lg breakpoint
      if (isSmallScreen && !navigationCollapsed) {
        setNavigationCollapsed(true)
      }
    }

    // Check on mount and resize
    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [navigationCollapsed, setNavigationCollapsed])

  // Calculate dynamic width
  const navWidth = navigationCollapsed ? 'w-16' : 'w-64'

  return (
    <nav className={cn(
      "fixed left-0 top-0 h-full bg-white border-r border-gray-200 transition-all duration-300 ease-in-out",
      navWidth
    )}>
      <div className="p-4">
        {/* Header with toggle button */}
        <div className="flex items-center justify-between mb-8">
          {!navigationCollapsed && (
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2 truncate">
                <Building className="w-6 h-6 flex-shrink-0" />
                <span className="truncate">TikTok Geo-Regulation AI</span>
              </h1>
              <p className="text-sm text-gray-600 mt-1 truncate">
                Compliance Analysis System
              </p>
            </div>
          )}
          
          {/* Toggle Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setNavigationCollapsed(!navigationCollapsed)}
            className={cn(
              "h-8 w-8 p-0 flex-shrink-0",
              navigationCollapsed ? "mx-auto" : "ml-2"
            )}
            title={navigationCollapsed ? "Expand navigation" : "Collapse navigation"}
          >
            {navigationCollapsed ? (
              <Menu className="w-4 h-4" />
            ) : (
              <X className="w-4 h-4" />
            )}
          </Button>
        </div>
        
        {/* Collapsed header - just logo */}
        {navigationCollapsed && (
          <div className="mb-8 flex justify-center">
            <Building className="w-6 h-6 text-gray-900" />
          </div>
        )}
      </div>
      
      {/* Navigation Items */}
      <div className="px-2">
        <ul className="space-y-2">
          {navigationItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== '/' && pathname.startsWith(item.href))
            
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 mx-2 rounded-md text-sm font-medium transition-colors relative group',
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100',
                    navigationCollapsed ? 'justify-center' : ''
                  )}
                  title={navigationCollapsed ? item.label : undefined}
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  {!navigationCollapsed && (
                    <span className="truncate">{item.label}</span>
                  )}
                  
                  {/* Active indicator for collapsed state */}
                  {isActive && navigationCollapsed && (
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-700 rounded-r-full" />
                  )}
                  
                  {/* Tooltip for collapsed state */}
                  {navigationCollapsed && (
                    <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50">
                      {item.label}
                      <div className="absolute right-full top-1/2 transform -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
                    </div>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </div>
    </nav>
  )
}