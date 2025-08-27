"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Send, Bot, User, Sparkles, AlertCircle, Plus, Trash2, ChevronLeft, ChevronRight, Brain } from "lucide-react"
import { apiService } from "@/lib/api"

interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
  sessionId?: string
}

interface EnhancedChatInterfaceProps {
  onGraphUpdate?: () => void
}

export function EnhancedChatInterface({ onGraphUpdate }: EnhancedChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "Hello! I'm VisBrain, your AI assistant. I help explore knowledge through conversations and build visual knowledge graphs. What would you like to learn about?",
      role: "assistant",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>()
  const [chatCollapsed, setChatCollapsed] = useState(false)

  // Check backend connection on component mount
  React.useEffect(() => {
    const checkConnection = async () => {
      try {
        await apiService.healthCheck()
        setIsConnected(true)
      } catch {
        setIsConnected(false)
      }
    }
    checkConnection()
  }, [])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = input
    setInput("")
    setIsLoading(true)

    try {
      // Always try to send to backend first, regardless of isConnected status
      try {
        const result = await apiService.sendChatMessage(currentInput, currentSessionId)
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: result.response,
          role: "assistant",
          timestamp: new Date(),
          sessionId: result.session_id
        }
        
        setMessages((prev) => [...prev, assistantMessage])
        
        // Update current session ID
        setCurrentSessionId(result.session_id)
        
        // Update connection status on success
        if (!isConnected) {
          setIsConnected(true)
        }
        
        // Trigger graph update since agent thinking was processed
        if (onGraphUpdate) {
          onGraphUpdate()
        }
      } catch (backendError) {
        // Backend failed, update connection status and show fallback
        setIsConnected(false)
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: `I'm currently unable to connect to the AI backend. Error: ${backendError instanceof Error ? backendError.message : 'Unknown error'}. Please check if the Visbrain server is running on port 5001.`,
          role: "assistant",
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, assistantMessage])
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Sorry, I encountered an error processing your request: ${error instanceof Error ? error.message : 'Unknown error'}`,
        role: "assistant",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = () => {
    setMessages([
      {
        id: "1",
        content:
          "🆕 New conversation started! I'm VisBrain, your AI assistant. I help explore knowledge through conversations and build visual knowledge graphs. What would you like to learn about?",
        role: "assistant",
        timestamp: new Date(),
      },
    ])
    setCurrentSessionId(undefined)
    setInput("")
  }

  const handleClearGraph = async () => {
    if (!isConnected) {
      return
    }

    try {
      setIsLoading(true)
      await apiService.clearDatabase()
      
      // Add confirmation message
      const confirmationMessage: Message = {
        id: Date.now().toString(),
        content: "Knowledge graph has been cleared successfully! All previous conversations and entities have been removed from the database.",
        role: "assistant",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, confirmationMessage])
      
      // Trigger graph update
      if (onGraphUpdate) {
        onGraphUpdate()
      }
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: `Failed to clear knowledge graph: ${error instanceof Error ? error.message : 'Unknown error'}`,
        role: "assistant",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={`transition-all duration-500 ease-out ${chatCollapsed ? 'w-16' : 'w-96'} relative`}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.08] via-white/[0.05] to-white/[0.02] backdrop-blur-3xl border-r border-white/20 shadow-2xl shadow-black/50"></div>
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-purple-500/10"></div>
      <div className="relative z-10 h-full flex flex-col">
        {/* Glass Header */}
        <div className="p-4 relative">
          <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-xl border-b border-white/20 shadow-lg"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between">
              <div className={`flex items-center gap-3 ${chatCollapsed ? 'justify-center' : ''}`}>
                <div className="relative group">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-purple-600 rounded-2xl blur-md opacity-75 group-hover:opacity-100 transition-opacity"></div>
                  <div className="relative w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 backdrop-blur-xl border border-white/30 shadow-2xl flex items-center justify-center">
                    <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-2xl"></div>
                    <Sparkles className="w-6 h-6 text-white animate-pulse relative z-10" />
                  </div>
                  <div className="absolute -top-1 -right-1 w-5 h-5 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full border-2 border-white/50 backdrop-blur-sm shadow-lg animate-pulse"></div>
                </div>
                
                {!chatCollapsed && (
                  <div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent drop-shadow-lg">
                      VisBrain AI
                    </h1>
                    <p className="text-sm text-white/80 font-medium">Knowledge Assistant</p>
                  </div>
                )}
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setChatCollapsed(!chatCollapsed)}
                className="bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg"
              >
                {chatCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
              </Button>
            </div>
            
            {!chatCollapsed && (
              <>
                <div className="mt-6 relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-blue-500/20 rounded-xl backdrop-blur-sm"></div>
                  <div className="relative p-3 border border-white/20 rounded-xl bg-white/5">
                    <div className="flex items-center gap-3 text-sm">
                      <div className="relative">
                        <div className="w-3 h-3 bg-gradient-to-r from-emerald-400 to-green-500 rounded-full animate-pulse shadow-lg"></div>
                        <div className="absolute inset-0 bg-emerald-400 rounded-full animate-ping opacity-20"></div>
                      </div>
                      <span className="text-white/90 font-medium">{isConnected ? 'Connected' : 'Offline'}</span>
                      <span className="text-white/60">•</span>
                      <span className="text-white/70">{messages.length} Messages</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 mt-4">
                  <Button
                    onClick={handleNewChat}
                    variant="secondary"
                    size="sm"
                    className="flex items-center gap-2 text-xs font-medium bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg flex-1"
                  >
                    <Plus className="w-3 h-3" />
                    New Chat
                  </Button>
                  <Button
                    onClick={handleClearGraph}
                    variant="secondary"
                    size="sm"
                    disabled={!isConnected || isLoading}
                    className="flex items-center gap-2 text-xs font-medium bg-white/10 hover:bg-red-500/20 backdrop-blur-sm border border-white/20 shadow-lg disabled:opacity-50"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>

        {!chatCollapsed && (
          <>
            {/* Glass Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 relative">
              <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/[0.02] to-transparent"></div>
              <div className="relative z-10">
                {messages.map((message) => (
                  <div key={message.id} className={`flex gap-3 mb-6 ${message.role === "user" ? 'flex-row-reverse' : ''}`}>
                    <div className="relative group">
                      <div className={`w-10 h-10 rounded-2xl backdrop-blur-xl border border-white/30 shadow-2xl flex items-center justify-center relative overflow-hidden ${
                        message.role === "user" 
                          ? 'bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20' 
                          : 'bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-indigo-500/20'
                      }`}>
                        <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent"></div>
                        {message.role === "user" ? (
                          <User className="w-5 h-5 text-white relative z-10" />
                        ) : (
                          <Brain className="w-5 h-5 text-white relative z-10" />
                        )}
                      </div>
                    </div>
                    <div className={`max-w-[80%] ${message.role === "user" ? 'items-end' : 'items-start'} flex flex-col`}>
                      <div className="relative group">
                        <div className={`p-4 rounded-2xl backdrop-blur-xl border shadow-2xl relative overflow-hidden ${
                          message.role === "user" 
                            ? 'bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 border-blue-300/30 text-white' 
                            : 'bg-gradient-to-br from-white/10 via-white/5 to-white/10 border-white/20 text-white'
                        }`}>
                          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent"></div>
                          <p className="text-sm leading-relaxed relative z-10 whitespace-pre-wrap">{message.content}</p>
                        </div>
                      </div>
                      <span className="text-xs text-white/60 mt-2 font-medium">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-indigo-500/20 backdrop-blur-xl border border-white/30 shadow-2xl flex items-center justify-center relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent"></div>
                      <Brain className="w-5 h-5 text-white relative z-10" />
                    </div>
                    <div className="bg-gradient-to-br from-white/10 via-white/5 to-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-4 shadow-2xl relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent"></div>
                      <div className="flex gap-2 relative z-10">
                        <div className="w-2 h-2 bg-white/80 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-white/80 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-white/80 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Enhanced Glass Input Area */}
            <div className="p-4 relative">
              <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-2xl border-t border-white/20 shadow-2xl"></div>
              <div className="relative z-10">
                <div className="relative group">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-3xl blur-sm group-hover:blur-none transition-all duration-300"></div>
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about your knowledge graph..."
                    className="relative w-full p-5 pr-16 text-sm bg-gradient-to-br from-white/10 via-white/5 to-white/10 backdrop-blur-2xl border border-white/30 rounded-3xl placeholder:text-white/60 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400/50 transition-all duration-300 shadow-2xl text-white"
                    rows={3}
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    className="absolute bottom-4 right-4 w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl shadow-2xl hover:shadow-blue-500/50 transition-all duration-300 hover:scale-105 active:scale-95 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-xl border border-white/20 group"
                  >
                    <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-2xl"></div>
                    <Send className="w-5 h-5 text-white relative z-10 group-hover:scale-110 transition-transform duration-200" />
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}