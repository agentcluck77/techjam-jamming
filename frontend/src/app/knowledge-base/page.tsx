'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { getKnowledgeBase, updateKnowledgeBase } from '@/lib/api'

export default function KnowledgeBase() {
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState<string | null>(null)
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    const loadKnowledgeBase = async () => {
      try {
        const kb = await getKnowledgeBase()
        setContent(kb)
      } catch (error) {
        console.error('Failed to load knowledge base:', error)
        // Set default content if loading fails
        setContent(defaultKnowledgeBase)
      } finally {
        setLoading(false)
      }
    }

    loadKnowledgeBase()
  }, [])

  const handleSave = async () => {
    if (!hasChanges) return
    
    setSaving(true)
    try {
      await updateKnowledgeBase(content)
      setLastSaved(new Date().toLocaleTimeString())
      setHasChanges(false)
    } catch (error) {
      console.error('Failed to save knowledge base:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleContentChange = (value: string) => {
    setContent(value)
    setHasChanges(true)
  }

  const addTemplate = (template: string) => {
    const templates = {
      terminology: `
# TikTok Terminology
- "Live Shopping" = e-commerce integration during live streams
- "Creator Fund" = monetization program for content creators
- "For You Page" = personalized recommendation feed
`,
      precedents: `
# Legal Precedents
- Utah Social Media Act requires age verification for minor features and 10:30 PM - 6:30 AM curfews
- EU DSA mandates 24-hour content moderation response times
- COPPA applies to any feature accessible by users under 13
`,
      patterns: `
# Compliance Patterns
- Payment processing → PCI DSS compliance required
- User data collection → Privacy policy updates needed
- Minor-accessible features → Parental controls mandatory
`,
      jurisdiction: `
# Jurisdiction Guide
- Utah: Focus on minor protection, time restrictions, and age verification
- EU: Data protection (GDPR), content moderation (DSA), and transparency
- California: Privacy rights (CCPA/CPRA) and consumer protection
- Florida: Social media platform regulations and minor safety
- Brazil: Marco Civil da Internet and LGPD data protection
`,
      violations: `
# Common Violations
- Insufficient age verification mechanisms
- Inadequate content moderation response times
- Missing parental consent for minor features
- Unclear data retention policies
- Non-compliant privacy notices
`,
      practices: `
# Best Practices
- Always implement robust age verification for age-restricted features
- Maintain detailed audit logs for compliance reviews
- Provide clear opt-out mechanisms for data collection
- Regular compliance monitoring and updates
- Document all compliance decisions and rationale
`
    }
    
    const newContent = content + templates[template as keyof typeof templates]
    handleContentChange(newContent)
  }

  const wordCount = content.split(/\s+/).filter(word => word.length > 0).length
  const charCount = content.length

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              🧠 Agent Knowledge Base
            </h1>
            <p className="text-gray-600 mt-2">
              Customize lawyer agent domain expertise
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              onClick={handleSave}
              disabled={!hasChanges || saving}
              variant={hasChanges ? "default" : "outline"}
            >
              {saving ? 'Saving...' : 'Save'}
            </Button>
            <Button variant="outline" disabled>Revert</Button>
            <Button variant="outline" size="sm">Help</Button>
            <Button variant="outline" size="sm">?</Button>
          </div>
        </div>

        {/* Knowledge Editor */}
        <Card className="bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                📝 Customize Agent Expertise
              </h2>
              <div className="text-sm text-gray-500">
                {hasChanges && (
                  <span className="text-orange-600 mr-4">• Unsaved changes</span>
                )}
                {lastSaved && (
                  <span>Last saved: {lastSaved}</span>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              value={content}
              onChange={(e) => handleContentChange(e.target.value)}
              className="min-h-[400px] font-mono text-sm"
              placeholder="Enter your knowledge base content here..."
            />
            
            <div className="flex items-center justify-between text-sm text-gray-500 border-t pt-4">
              <div className="flex items-center gap-4">
                <span>Word count: {wordCount.toLocaleString()}</span>
                <span>Characters: {charCount.toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Content Templates */}
        <Card className="bg-white">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              🔧 Quick Add Sections
            </h2>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => addTemplate('terminology')}
              >
                + TikTok Terminology
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => addTemplate('precedents')}
              >
                + Legal Precedents
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => addTemplate('patterns')}
              >
                + Compliance Patterns
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => addTemplate('jurisdiction')}
              >
                + Jurisdiction Guide
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => addTemplate('violations')}
              >
                + Common Violations
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => addTemplate('practices')}
              >
                + Best Practices
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Impact Preview */}
        <Card className="bg-white">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              🔍 How This Enhances Analysis
            </h2>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 mb-4">
              Your knowledge base is automatically included in every compliance analysis to provide 
              TikTok-specific context and improve accuracy.
            </p>
            <Button variant="outline">
              Preview Enhanced Prompt
            </Button>
            <p className="text-sm text-gray-500 mt-2">
              See how this content improves AI analysis
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

const defaultKnowledgeBase = `# TikTok Terminology
- "Live Shopping" = e-commerce integration during live streams
- "Creator Fund" = monetization program for content creators
- "For You Page" = personalized recommendation feed

# Legal Precedents
- Utah Social Media Act requires age verification for minor features and 10:30 PM - 6:30 AM curfews
- EU DSA mandates 24-hour content moderation response times
- COPPA applies to any feature accessible by users under 13

# Compliance Patterns
- Payment processing → PCI DSS compliance required
- User data collection → Privacy policy updates needed
- Minor-accessible features → Parental controls mandatory`