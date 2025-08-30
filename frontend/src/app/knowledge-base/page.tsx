'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Textarea } from '../../components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog'
import { getKnowledgeBase, updateKnowledgeBase, getSystemPrompt, updateSystemPrompt } from '../../lib/api'
import { Edit, Settings, Search, BookOpen, BarChart3, Brain, MessageSquare } from 'lucide-react'
import MDEditor from '@uiw/react-md-editor'
import '@uiw/react-md-editor/markdown-editor.css'
import '@uiw/react-markdown-preview/markdown.css'

export default function KnowledgeBase() {
  const [activeTab, setActiveTab] = useState<'knowledge' | 'system'>('knowledge')
  
  // Knowledge Base state
  const [content, setContent] = useState('')
  const [originalContent, setOriginalContent] = useState('')
  
  // System Prompt state
  const [systemPrompt, setSystemPrompt] = useState('')
  const [originalSystemPrompt, setOriginalSystemPrompt] = useState('')
  
  // Shared state
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState<string | null>(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [kb, sp] = await Promise.all([
          getKnowledgeBase(),
          getSystemPrompt()
        ])
        
        setContent(kb)
        setOriginalContent(kb)
        setSystemPrompt(sp)
        setOriginalSystemPrompt(sp)
      } catch (error) {
        console.error('Failed to load data:', error)
        // Show error state instead of defaults - force proper configuration
        setContent('')
        setOriginalContent('')
        setSystemPrompt('')
        setOriginalSystemPrompt('')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const handleSave = async () => {
    if (!hasChanges) return
    
    setSaving(true)
    try {
      if (activeTab === 'knowledge') {
        await updateKnowledgeBase(content)
        setOriginalContent(content)
      } else {
        await updateSystemPrompt(systemPrompt)
        setOriginalSystemPrompt(systemPrompt)
      }
      setLastSaved(new Date().toLocaleTimeString())
      setHasChanges(false)
    } catch (error) {
      console.error(`Failed to save ${activeTab}:`, error)
    } finally {
      setSaving(false)
    }
  }

  const handleRevert = () => {
    if (activeTab === 'knowledge') {
      setContent(originalContent)
    } else {
      setSystemPrompt(originalSystemPrompt)
    }
    setHasChanges(false)
  }

  const toggleHelp = () => {
    setShowHelp(!showHelp)
  }

  const togglePreview = () => {
    setShowPreview(!showPreview)
  }


  const handleContentChange = (value: string) => {
    if (activeTab === 'knowledge') {
      setContent(value)
      setHasChanges(value !== originalContent)
    } else {
      setSystemPrompt(value)
      setHasChanges(value !== originalSystemPrompt)
    }
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

  const addSystemPromptTemplate = (template: string) => {
    const templates = {
      expertise: `
## Additional Expertise
- **Emerging Regulations**: Stay current with new social media regulations
- **Industry Standards**: Understanding of platform-specific compliance practices
- **Cross-Border Considerations**: Multi-jurisdictional compliance strategies
`,
      instructions: `
## Analysis Instructions
1. **Feature Assessment**: Evaluate regulatory triggers systematically
2. **Risk Prioritization**: Focus on high-impact compliance requirements first
3. **Practical Solutions**: Provide implementable recommendations
4. **Timeline Consideration**: Account for regulatory deadlines and implementation complexity
`,
      format: `
## Response Format Requirements
- **Executive Summary**: 2-3 sentence overview of compliance status
- **Detailed Analysis**: Jurisdiction-specific requirements and rationale
- **Action Items**: Prioritized implementation steps with timelines
- **Risk Assessment**: Clear 1-5 scale with justification
`,
      considerations: `
## Key Considerations
- **Minor Protection**: Always prioritize user safety, especially for minors
- **Data Minimization**: Recommend minimal data collection approaches
- **Transparency**: Emphasize clear user communication and disclosure
- **Proportionality**: Balance compliance requirements with user experience
`,
      examples: `
## Example Analysis Framework
**Feature**: [Name]
**Trigger Analysis**: [What regulations apply]
**Compliance Gap**: [What needs to be implemented]
**Implementation**: [Specific steps]
**Timeline**: [Realistic timeframe]
`
    }
    
    const newContent = systemPrompt + templates[template as keyof typeof templates]
    handleContentChange(newContent)
  }

  const currentContent = activeTab === 'knowledge' ? content : systemPrompt
  const wordCount = currentContent.split(/\s+/).filter(word => word.length > 0).length
  const charCount = currentContent.length

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
              Agent Configuration
            </h1>
            <p className="text-gray-600 mt-2">
              Customize lawyer agent behavior and knowledge
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

        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-white p-1 rounded-lg border">
          <Button
            variant={activeTab === 'knowledge' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('knowledge')}
            className="flex items-center gap-2"
          >
            <Brain className="w-4 h-4" />
            Knowledge Base
          </Button>
          <Button
            variant={activeTab === 'system' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('system')}
            className="flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            System Prompt
          </Button>
        </div>

        {/* Content Editor */}
        <Card className="bg-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Edit className="w-5 h-5 mr-2" />
                {activeTab === 'knowledge' ? 'Customize Agent Expertise' : 'Configure Agent Instructions'}
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
            <MDEditor
              value={currentContent}
              onChange={(val) => handleContentChange(val || '')}
              height={400}
              preview="edit"
              data-color-mode="light"
              textareaProps={{
                placeholder: activeTab === 'knowledge' 
                  ? "Enter your knowledge base content here..." 
                  : "Enter system prompt instructions here...",
                style: { fontSize: 14, fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace' }
              }}
            />
            
            <div className="flex items-center justify-between text-sm text-gray-500 border-t pt-4">
              <div className="flex items-center gap-4">
                <span>Word count: {wordCount.toLocaleString()}</span>
                <span>Characters: {charCount.toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Content Templates - Only for Knowledge Base */}
        {activeTab === 'knowledge' && (
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
        )}

        {/* System Prompt Templates - Only for System Prompt */}
        {activeTab === 'system' && (
          <Card className="bg-white">
            <CardHeader>
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 mr-2" />
                System Prompt Templates
              </h2>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => addSystemPromptTemplate('expertise')}
                >
                  + Expertise Areas
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => addSystemPromptTemplate('instructions')}
                >
                  + Analysis Instructions
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => addSystemPromptTemplate('format')}
                >
                  + Response Format
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => addSystemPromptTemplate('considerations')}
                >
                  + Key Considerations
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => addSystemPromptTemplate('examples')}
                >
                  + Examples
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Impact Preview */}
        <Card className="bg-white">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Search className="w-5 h-5 mr-2" />
              {activeTab === 'knowledge' ? 'How This Enhances Analysis' : 'How This Guides Agent Behavior'}
            </h2>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 mb-4">
              {activeTab === 'knowledge' 
                ? 'Your knowledge base is automatically included in every compliance analysis to provide TikTok-specific context and improve accuracy.'
                : 'The system prompt defines how the legal agent analyzes features and provides compliance recommendations.'}
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
                    {currentContent || `Your ${activeTab === 'knowledge' ? 'knowledge base' : 'system prompt'} content will appear here...`}
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

## Core Platform Terms
- **ASL** = American Sign Language
- **FYP** = For You Page (personalized recommendation feed)
- **LIVE** = live streaming feature
- **algo** = algorithm (recommendation system)

## Content Features
- **duet** = collaborative video feature allowing response videos
- **stitch** = video response feature for remixing content
- **sound sync** = audio synchronization feature
- **green screen** = background replacement feature
- **beauty filter** = appearance enhancement filter
- **AR effects** = augmented reality effects

## Creator & Commerce
- **Creator Fund** = monetization program for content creators
- **creator marketplace** = brand partnership platform
- **TikTok Shop** = e-commerce integration platform
- **branded content** = sponsored content feature

## Business & Analytics
- **pulse** = analytics dashboard for creators and businesses
- **spark ads** = advertising platform for businesses
- **brand takeover** = full-screen advertisement format
- **top view** = premium ad placement option

## Feature Components
- **jellybean** = individual feature component within the platform
- **hashtag challenge** = trending challenge campaign format`

const defaultSystemPrompt = `You are a TikTok compliance gap analyzer. Your sole purpose is to identify specific compliance gaps in TikTok PRDs, TRDs, and user flow documents.

## Your Process
1. Extract requirements/features from uploaded documents using Requirements MCP
2. Search for relevant regulations using Legal MCP
3. Identify specific compliance gaps
4. Provide clear reasoning for why each gap exists

## Output Format
For each compliance gap identified:

**Gap**: [Specific requirement/feature that creates compliance risk]
**Regulation**: [Specific law/regulation violated - cite Legal MCP source]
**Risk**: [High/Medium/Low]
**Reasoning**: [Why this creates a compliance gap - be specific and concise]
**Required Action**: [What TikTok must implement to close the gap]

## Key Focus Areas
- Minor protection (age verification, parental controls)
- Data privacy (GDPR, CCPA, LGPD)
- Content moderation requirements
- Algorithmic transparency obligations
- User consent and control

## Rules
- Be concise - no verbose explanations
- Only identify actual gaps, not general compliance advice
- Cite specific Legal MCP sources for regulations
- Focus on TikTok-specific implementation requirements
- Skip theoretical or low-impact compliance issues`