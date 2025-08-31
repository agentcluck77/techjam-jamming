'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { 
  MessageSquare, 
  Plus, 
  Clock, 
  Trash2, 
  Archive, 
  Search,
  MoreVertical,
  Edit
} from 'lucide-react'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu'

interface ChatMessage {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  model_used?: string
}

interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
  messages: ChatMessage[]
  status: 'active' | 'archived'
  model_preference?: string
}

interface ChatListProps {
  onSelectChat: (chat: ChatSession) => void
  onNewChat: () => void
  selectedChatId?: string
  className?: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function ChatList({ onSelectChat, onNewChat, selectedChatId, className }: ChatListProps) {
  const [chats, setChats] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [isNewChatOpen, setIsNewChatOpen] = useState(false)
  const [newChatTitle, setNewChatTitle] = useState('')

  const loadChats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chats/`)
      if (response.ok) {
        const data = await response.json()
        setChats(data.chats)
      }
    } catch (error) {
      console.error('Failed to load chats:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadChats()
  }, [])

  const handleNewChat = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chats/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newChatTitle || undefined
        }),
      })
      
      if (response.ok) {
        const newChat = await response.json()
        setChats(prev => [newChat, ...prev])
        setIsNewChatOpen(false)
        setNewChatTitle('')
        onSelectChat(newChat)
        onNewChat()
      }
    } catch (error) {
      console.error('Failed to create chat:', error)
    }
  }

  const handleDeleteChat = async (chatId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}`, {
        method: 'DELETE',
      })
      
      if (response.ok) {
        setChats(prev => prev.filter(chat => chat.id !== chatId))
      }
    } catch (error) {
      console.error('Failed to delete chat:', error)
    }
  }

  const handleArchiveChat = async (chatId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/archive`, {
        method: 'POST',
      })
      
      if (response.ok) {
        setChats(prev => prev.map(chat => 
          chat.id === chatId ? { ...chat, status: 'archived' as const } : chat
        ))
      }
    } catch (error) {
      console.error('Failed to archive chat:', error)
    }
  }

  const filteredChats = chats.filter(chat => 
    chat.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    chat.messages.some(msg => 
      msg.content.toLowerCase().includes(searchTerm.toLowerCase())
    )
  )

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) {
      return `${diffDays}d ago`
    } else if (diffHours > 0) {
      return `${diffHours}h ago`
    } else {
      return 'Just now'
    }
  }

  const getLastMessage = (chat: ChatSession) => {
    const lastMessage = chat.messages[chat.messages.length - 1]
    if (!lastMessage) return "New chat"
    
    const content = lastMessage.content.length > 50 
      ? lastMessage.content.substring(0, 50) + "..." 
      : lastMessage.content
    
    return lastMessage.type === 'user' ? `You: ${content}` : content
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Legal Chats
          </h2>
          
          <Dialog open={isNewChatOpen} onOpenChange={setIsNewChatOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="h-8 w-8 p-0">
                <Plus className="w-4 h-4" />
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>New Legal Chat</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <Input
                  placeholder="Chat title (optional)"
                  value={newChatTitle}
                  onChange={(e) => setNewChatTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleNewChat()
                    }
                  }}
                />
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => setIsNewChatOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleNewChat}>
                    Create Chat
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
        
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Search chats..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 h-9"
          />
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-100 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : filteredChats.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <MessageSquare className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p>No chats found</p>
            <p className="text-sm">Create your first legal chat to get started</p>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {filteredChats.map((chat) => (
              <Card
                key={chat.id}
                className={cn(
                  "cursor-pointer transition-all hover:shadow-sm border-0",
                  selectedChatId === chat.id 
                    ? "bg-blue-50 border-l-4 border-l-blue-500" 
                    : "hover:bg-gray-50"
                )}
                onClick={() => onSelectChat(chat)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate text-sm">
                        {chat.title}
                      </h3>
                      <p className="text-xs text-gray-500 mt-1 truncate">
                        {getLastMessage(chat)}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <Clock className="w-3 h-3 text-gray-400" />
                        <span className="text-xs text-gray-400">
                          {formatTimeAgo(chat.updated_at)}
                        </span>
                        {chat.status === 'archived' && (
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                            Archived
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 hover:bg-gray-200"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreVertical className="w-3 h-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-40">
                        <DropdownMenuItem onClick={() => handleArchiveChat(chat.id)}>
                          <Archive className="w-4 h-4 mr-2" />
                          Archive
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => handleDeleteChat(chat.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}