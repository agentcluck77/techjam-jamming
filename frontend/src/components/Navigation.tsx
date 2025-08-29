'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const navigationItems = [
  { href: '/', label: 'Requirements Check', icon: '📋' },
  { href: '/legal-documents', label: 'Legal Documents', icon: '🏛️' },
  { href: '/document-library', label: 'Document Library', icon: '📚' },
  { href: '/knowledge-base', label: 'Knowledge Base', icon: '🧠' },
  { href: '/results', label: 'Results History', icon: '📊' },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200 p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-gray-900">
          🏛️ TikTok Geo-Regulation AI
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Compliance Analysis System
        </p>
      </div>
      
      <ul className="space-y-2">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== '/' && pathname.startsWith(item.href))
          
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                )}
              >
                <span className="text-lg">{item.icon}</span>
                {item.label}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}