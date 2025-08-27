"use client"

import { useState, useCallback } from "react"
import { EnhancedChatInterface } from "@/components/enhanced-chat-interface"
import { EnhancedKnowledgeGraphView } from "@/components/enhanced-knowledge-graph-view"

export default function VisBrainPage() {
  const [graphUpdateTrigger, setGraphUpdateTrigger] = useState(0)

  const handleGraphUpdate = useCallback(() => {
    // Trigger a re-render of the knowledge graph component
    setGraphUpdateTrigger(prev => prev + 1)
  }, [])

  return (
    <div className="flex h-screen bg-gradient-to-br from-indigo-950 via-purple-950 to-slate-950 text-white overflow-hidden relative">
      {/* Glass overlay pattern */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-pink-500/5"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(120,119,198,0.1),transparent_50%)]"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(147,51,234,0.1),transparent_50%)]"></div>

      {/* Enhanced Chat Interface */}
      <EnhancedChatInterface onGraphUpdate={handleGraphUpdate} />

      {/* Enhanced Knowledge Graph View */}
      <EnhancedKnowledgeGraphView key={graphUpdateTrigger} />
    </div>
  )
}