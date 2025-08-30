'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { getKnowledgeBase, updateKnowledgeBase } from '@/lib/api'
import { Edit, Settings, Search, BookOpen, BarChart3, Brain } from 'lucide-react'

export default function KnowledgeBase() {
  const [content, setContent] = useState('')
  const [originalContent, setOriginalContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState<string | null>(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  useEffect(() => {
    const loadKnowledgeBase = async () => {
      try {
        const kb = await getKnowledgeBase()
        setContent(kb)
        setOriginalContent(kb)
      } catch (error) {
        console.error('Failed to load knowledge base:', error)
        // Set default content if loading fails
        setContent(defaultKnowledgeBase)
        setOriginalContent(defaultKnowledgeBase)
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
      setOriginalContent(content)
      setLastSaved(new Date().toLocaleTimeString())
      setHasChanges(false)
    } catch (error) {
      console.error('Failed to save knowledge base:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleRevert = () => {
    setContent(originalContent)
    setHasChanges(false)
  }

  const toggleHelp = () => {
    setShowHelp(!showHelp)
  }

  const togglePreview = () => {
    setShowPreview(!showPreview)
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
              <Brain className="w-5 h-5 mr-2" />
              Agent Knowledge Base
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
            <Button 
              variant="outline" 
              onClick={handleRevert}
              disabled={!hasChanges}
            >
              Revert
            </Button>
            <Button variant="outline" size="sm" onClick={toggleHelp}>
              Help
            </Button>
          </div>
        </div>

        {/* Knowledge Editor */}
        <Card className="bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Edit className="w-5 h-5 mr-2" />
                Customize Agent Expertise
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
              <Settings className="w-5 h-5 mr-2" />
              Quick Add Sections
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
              <Search className="w-5 h-5 mr-2" />
              How This Enhances Analysis
            </h2>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 mb-4">
              Your knowledge base is automatically included in every compliance analysis to provide 
              TikTok-specific context and improve accuracy.
            </p>
            <Button variant="outline" onClick={togglePreview}>
              {showPreview ? 'Hide Preview' : 'Preview Enhanced Prompt'}
            </Button>
            <p className="text-sm text-gray-500 mt-2">
              See how this content improves AI analysis
            </p>
          </CardContent>
        </Card>

        {/* Help Dialog */}
        <Dialog open={showHelp} onOpenChange={setShowHelp}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <BookOpen className="w-5 h-5" />
                Knowledge Base Help
              </DialogTitle>
              <DialogDescription>
                Learn how to customize your agent's expertise
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 text-sm">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">What is the Knowledge Base?</h3>
                <p className="text-gray-700">
                  The knowledge base provides TikTok-specific context that enhances the lawyer agent's 
                  analysis. This content is automatically included in every compliance assessment to 
                  improve accuracy and relevance.
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Quick Add Sections</h3>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li><strong>TikTok Terminology:</strong> Platform-specific terms and definitions</li>
                  <li><strong>Legal Precedents:</strong> Key regulatory decisions and case law</li>
                  <li><strong>Compliance Patterns:</strong> Common compliance requirements</li>
                  <li><strong>Jurisdiction Guide:</strong> Region-specific regulatory focuses</li>
                  <li><strong>Common Violations:</strong> Frequently seen compliance issues</li>
                  <li><strong>Best Practices:</strong> Recommended compliance approaches</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Tips for Effective Content</h3>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>Use clear, specific terminology relevant to your use case</li>
                  <li>Include jurisdiction-specific requirements and nuances</li>
                  <li>Reference specific laws, regulations, and compliance standards</li>
                  <li>Update regularly as regulations change</li>
                  <li>Keep content concise but comprehensive</li>
                </ul>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Preview Dialog */}
        <Dialog open={showPreview} onOpenChange={setShowPreview}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Search className="w-5 h-5" />
                Enhanced Prompt Preview
              </DialogTitle>
              <DialogDescription>
                See how your knowledge base content enhances AI analysis
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="bg-blue-50 p-4 rounded-lg border">
                <h3 className="font-semibold text-blue-900 mb-2">Base Prompt (without knowledge base)</h3>
                <p className="text-blue-800 text-sm font-mono">
                  Analyze this TikTok feature for regulatory compliance.<br/>
                  Feature: Live Shopping Integration<br/>
                  Description: Real-time commerce during live streams<br/>
                  Provide compliance analysis focusing on major jurisdictions.
                </p>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg border">
                <h3 className="font-semibold text-green-900 mb-2">Enhanced Prompt (with your knowledge base)</h3>
                <div className="text-green-800 text-sm font-mono whitespace-pre-wrap">
                  <p>Analyze this TikTok feature for regulatory compliance.</p>
                  <p>Feature: Live Shopping Integration</p>
                  <p>Description: Real-time commerce during live streams</p>
                  <p>Provide compliance analysis focusing on major jurisdictions.</p>
                  <br/>
                  <p className="font-semibold">Additional Knowledge Base Context:</p>
                  <div className="bg-green-100 p-2 rounded mt-2 max-h-40 overflow-y-auto">
                    {content || "Your knowledge base content will appear here..."}
                  </div>
                  <br/>
                  <p>Use this context to provide more accurate and TikTok-specific analysis.</p>
                </div>
              </div>
              
              <div className="bg-amber-50 p-4 rounded-lg border">
                <h3 className="font-semibold text-amber-900 mb-2 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Enhancement Benefits
                </h3>
                <ul className="text-amber-800 text-sm space-y-1">
                  <li>• <strong>Domain Expertise:</strong> TikTok-specific terminology and context</li>
                  <li>• <strong>Regulatory Awareness:</strong> Jurisdiction-specific requirements</li>
                  <li>• <strong>Historical Context:</strong> Past compliance decisions and precedents</li>
                  <li>• <strong>Best Practices:</strong> Proven compliance approaches</li>
                  <li>• <strong>Risk Mitigation:</strong> Common pitfalls and violations to avoid</li>
                </ul>
              </div>
            </div>
          </DialogContent>
        </Dialog>
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