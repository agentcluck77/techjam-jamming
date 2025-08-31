'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Eye, EyeOff, Key, Settings } from 'lucide-react'
import { toast } from 'sonner'
import { useApiKeyStore, useWorkflowStore } from '@/lib/stores'

export type ApiKeyType = 'anthropic' | 'openai' | 'google'

interface ApiKeys {
  anthropic?: string
  openai?: string  
  google?: string
}

interface ApiKeyManagerProps {
  children?: React.ReactNode
}

export default function ApiKeyManager({ children }: ApiKeyManagerProps) {
  const { apiKeys, setApiKeys, hasValidApiKeys } = useApiKeyStore()
  const { setApiKeys: setWorkflowApiKeys } = useWorkflowStore()
  const [showKeys, setShowKeys] = useState<Record<ApiKeyType, boolean>>({
    anthropic: false,
    openai: false,
    google: false
  })
  const [open, setOpen] = useState(false)

  // Load API keys from localStorage on mount
  useEffect(() => {
    const savedKeys = {
      anthropic: localStorage.getItem('anthropic_api_key') || '',
      openai: localStorage.getItem('openai_api_key') || '',
      google: localStorage.getItem('google_api_key') || ''
    }
    setApiKeys(savedKeys)
    // CRITICAL FIX: Also set in workflow store for document analysis
    setWorkflowApiKeys(savedKeys)
  }, [])

  const handleKeyChange = (keyType: ApiKeyType, value: string) => {
    const updatedKeys = { ...apiKeys, [keyType]: value }
    setApiKeys(updatedKeys)
    // CRITICAL FIX: Also update workflow store for document analysis
    setWorkflowApiKeys(updatedKeys)
    
    // Save to localStorage
    if (value) {
      localStorage.setItem(`${keyType}_api_key`, value)
    } else {
      localStorage.removeItem(`${keyType}_api_key`)
    }
  }

  const toggleShowKey = (keyType: ApiKeyType) => {
    setShowKeys(prev => ({ ...prev, [keyType]: !prev[keyType] }))
  }

  const clearKey = (keyType: ApiKeyType) => {
    handleKeyChange(keyType, '')
    toast.success(`${keyType} API key cleared`)
  }

  const hasAnyKeys = hasValidApiKeys()

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button 
            variant="outline" 
            size="sm" 
            className={hasAnyKeys ? "border-green-500" : "border-orange-500"}
          >
            <Key className="h-4 w-4 mr-2" />
            {hasAnyKeys ? "API Keys Set" : "Set API Keys"}
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API Key Configuration
          </DialogTitle>
          <DialogDescription>
            Enter your AI provider API keys. Keys are stored locally in your browser and sent securely to the backend.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
        <Tabs defaultValue="anthropic" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="anthropic">
              <span className="flex items-center gap-2">
                Anthropic
                {apiKeys.anthropic && (
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                )}
              </span>
            </TabsTrigger>
            <TabsTrigger value="openai">
              <span className="flex items-center gap-2">
                OpenAI
                {apiKeys.openai && (
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                )}
              </span>
            </TabsTrigger>
            <TabsTrigger value="google">
              <span className="flex items-center gap-2">
                Google
                {apiKeys.google && (
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                )}
              </span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="anthropic" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="anthropic-key">Anthropic API Key</Label>
              <div className="flex gap-2">
                <Input
                  id="anthropic-key"
                  type={showKeys.anthropic ? "text" : "password"}
                  placeholder="sk-ant-api03-..."
                  value={apiKeys.anthropic || ''}
                  onChange={(e) => handleKeyChange('anthropic', e.target.value)}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => toggleShowKey('anthropic')}
                >
                  {showKeys.anthropic ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => clearKey('anthropic')}
                >
                  Clear
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Get your key from <a href="https://console.anthropic.com" target="_blank" rel="noopener noreferrer" className="underline">console.anthropic.com</a>
              </p>
            </div>
          </TabsContent>

          <TabsContent value="openai" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="openai-key">OpenAI API Key</Label>
              <div className="flex gap-2">
                <Input
                  id="openai-key"
                  type={showKeys.openai ? "text" : "password"}
                  placeholder="sk-..."
                  value={apiKeys.openai || ''}
                  onChange={(e) => handleKeyChange('openai', e.target.value)}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => toggleShowKey('openai')}
                >
                  {showKeys.openai ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => clearKey('openai')}
                >
                  Clear
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Get your key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="underline">platform.openai.com</a>
              </p>
            </div>
          </TabsContent>

          <TabsContent value="google" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="google-key">Google AI API Key</Label>
              <div className="flex gap-2">
                <Input
                  id="google-key"
                  type={showKeys.google ? "text" : "password"}
                  placeholder="AIza..."
                  value={apiKeys.google || ''}
                  onChange={(e) => handleKeyChange('google', e.target.value)}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => toggleShowKey('google')}
                >
                  {showKeys.google ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => clearKey('google')}
                >
                  Clear
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Get your key from <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="underline">aistudio.google.com</a>
              </p>
            </div>
          </TabsContent>
        </Tabs>

        {!hasAnyKeys && (
          <div className="mt-4 p-3 border border-orange-200 rounded-md bg-orange-50">
            <p className="text-sm text-orange-800">
              At least one API key is required for AI analysis. The system will try providers in order of availability.
            </p>
          </div>
        )}
        </div>
      </DialogContent>
    </Dialog>
  )
}