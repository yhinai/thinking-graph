'use client'

import React, { useState, useEffect } from 'react'
import { X, ChevronDown, ChevronRight, User, Brain, Wrench, MapPin, Clock, Link, Activity, TrendingUp } from 'lucide-react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Card } from './ui/card'
import { ScrollArea } from './ui/scroll-area'

// Types
interface NodeDetailsData {
  id: string
  name: string
  type: string
  labels: string[]
  confidence: number
  definition?: string
  properties: Record<string, any>
  connections: ConnectionDetails[]
  connection_count: number
  related_conversations: ConversationSnippet[]
  conversation_count: number
  metadata: {
    retrieval_timestamp: string
    total_relationships: number
    has_definition: boolean
    node_centrality: number
  }
  created_at?: string
  last_updated?: string
}

interface ConnectionDetails {
  id: string
  name: string
  type: string
  relationship_type: string
  strength: number
  direction?: string
}

interface ConversationSnippet {
  session_id: string
  reasoning_strategy: string
  domain: string
  timestamp: string
  thought_content: string
  thought_type: string
  thought_confidence: number
}

interface NodeStatistics {
  node_id: string
  total_connections: number
  mention_count: number
  average_confidence: number
  relationship_types: Record<string, number>
  connected_node_types: Record<string, number>
  centrality_score: number
  activity_score: number
}

interface TimelineEntry {
  session_id: string
  strategy: string
  domain: string
  timestamp: string
  thoughts: Array<{
    content: string
    type: string
    confidence: number
  }>
}

interface NodeDetailsPanelProps {
  nodeId: string | null
  isOpen: boolean
  onClose: () => void
  onExpand?: () => void
}

// Component for expandable sections
interface ExpandableSectionProps {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
  defaultExpanded?: boolean
  badge?: string | number
}

const ExpandableSection: React.FC<ExpandableSectionProps> = ({ 
  title, 
  icon, 
  children, 
  defaultExpanded = false,
  badge
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <div className="border rounded-lg mb-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium">{title}</span>
          {badge !== undefined && (
            <Badge variant="secondary" className="ml-2">
              {badge}
            </Badge>
          )}
        </div>
        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>
      {isExpanded && (
        <div className="p-3 pt-0 border-t">
          {children}
        </div>
      )}
    </div>
  )
}

// Component for node type icons
const getNodeTypeIcon = (type: string, size = 16) => {
  switch (type.toLowerCase()) {
    case 'entity':
      return <Brain size={size} />
    case 'person':
      return <User size={size} />
    case 'tool':
      return <Wrench size={size} />
    case 'location':
      return <MapPin size={size} />
    case 'session':
      return <Activity size={size} />
    case 'thought':
      return <Brain size={size} />
    default:
      return <Link size={size} />
  }
}

// Component for confidence indicator
const ConfidenceIndicator: React.FC<{ confidence: number }> = ({ confidence }) => {
  const getColor = (conf: number) => {
    if (conf >= 0.8) return 'bg-green-500'
    if (conf >= 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="flex items-center gap-2">
      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getColor(confidence) }} />
      <span className="text-sm text-gray-600">
        {Math.round(confidence * 100)}% confidence
      </span>
    </div>
  )
}

// Main component
export const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({
  nodeId,
  isOpen,
  onClose,
  onExpand
}) => {
  const [nodeData, setNodeData] = useState<NodeDetailsData | null>(null)
  const [statistics, setStatistics] = useState<NodeStatistics | null>(null)
  const [timeline, setTimeline] = useState<TimelineEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'details' | 'timeline' | 'stats'>('details')

  // Fetch node details
  const fetchNodeDetails = async (id: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/node/${id}/details`)
      if (!response.ok) {
        throw new Error(`Failed to fetch node details: ${response.status}`)
      }
      
      const data = await response.json()
      setNodeData(data)
      
      // Fetch additional data in parallel
      const [statsResponse, timelineResponse] = await Promise.all([
        fetch(`/api/node/${id}/statistics`),
        fetch(`/api/node/${id}/timeline`)
      ])
      
      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        setStatistics(statsData)
      }
      
      if (timelineResponse.ok) {
        const timelineData = await timelineResponse.json()
        setTimeline(timelineData.timeline || [])
      }
      
    } catch (err) {
      console.error('Failed to fetch node details:', err)
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  // Effect to fetch data when nodeId changes
  useEffect(() => {
    if (nodeId && isOpen) {
      fetchNodeDetails(nodeId)
    }
  }, [nodeId, isOpen])

  // Reset state when panel closes
  useEffect(() => {
    if (!isOpen) {
      setNodeData(null)
      setStatistics(null)
      setTimeline([])
      setError(null)
    }
  }, [isOpen])

  if (!isOpen || !nodeId) {
    return null
  }

  return (
    <div className="fixed right-4 top-4 bottom-4 w-96 bg-white shadow-2xl rounded-lg border z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          {nodeData && getNodeTypeIcon(nodeData.type, 20)}
          <h2 className="font-semibold text-lg truncate">
            {nodeData?.name || 'Node Details'}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {onExpand && (
            <Button variant="ghost" size="sm" onClick={onExpand}>
              <TrendingUp size={16} />
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X size={16} />
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        {[
          { key: 'details', label: 'Details' },
          { key: 'timeline', label: 'Timeline' },
          { key: 'stats', label: 'Statistics' }
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-4">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        )}

        {error && (
          <div className="text-red-600 text-sm p-4 bg-red-50 rounded">
            {error}
          </div>
        )}

        {nodeData && !isLoading && (
          <>
            {activeTab === 'details' && (
              <div className="space-y-4">
                {/* Basic Info */}
                <Card className="p-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{nodeData.type}</Badge>
                      {nodeData.labels.filter(l => l !== nodeData.type).map(label => (
                        <Badge key={label} variant="secondary">{label}</Badge>
                      ))}
                    </div>
                    <ConfidenceIndicator confidence={nodeData.confidence} />
                    {nodeData.created_at && (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Clock size={14} />
                        Created: {new Date(nodeData.created_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </Card>

                {/* Definition */}
                {nodeData.definition && (
                  <ExpandableSection
                    title="Definition"
                    icon={<Brain size={16} />}
                    defaultExpanded={true}
                  >
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {nodeData.definition}
                    </p>
                  </ExpandableSection>
                )}

                {/* Connections */}
                <ExpandableSection
                  title="Connections"
                  icon={<Link size={16} />}
                  badge={nodeData.connection_count}
                >
                  <div className="space-y-2">
                    {nodeData.connections.slice(0, 5).map((conn, index) => (
                      <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                        {getNodeTypeIcon(conn.type, 14)}
                        <span className="text-sm font-medium truncate flex-1">
                          {conn.name}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {conn.relationship_type}
                        </Badge>
                        <div className="w-12 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${conn.strength * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                    {nodeData.connection_count > 5 && (
                      <p className="text-xs text-gray-500 text-center">
                        +{nodeData.connection_count - 5} more connections
                      </p>
                    )}
                  </div>
                </ExpandableSection>

                {/* Related Conversations */}
                <ExpandableSection
                  title="Related Conversations"
                  icon={<Activity size={16} />}
                  badge={nodeData.conversation_count}
                >
                  <div className="space-y-3">
                    {nodeData.related_conversations.slice(0, 3).map((conv, index) => (
                      <div key={index} className="border rounded p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline">{conv.reasoning_strategy}</Badge>
                          <Badge variant="secondary">{conv.domain}</Badge>
                          <span className="text-xs text-gray-500 ml-auto">
                            {new Date(conv.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                        {conv.thought_content && (
                          <p className="text-sm text-gray-700 line-clamp-2">
                            {conv.thought_content}
                          </p>
                        )}
                      </div>
                    ))}
                    {nodeData.conversation_count > 3 && (
                      <p className="text-xs text-gray-500 text-center">
                        +{nodeData.conversation_count - 3} more conversations
                      </p>
                    )}
                  </div>
                </ExpandableSection>
              </div>
            )}

            {activeTab === 'timeline' && (
              <div className="space-y-3">
                {timeline.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">
                    No timeline data available
                  </p>
                ) : (
                  timeline.map((entry, index) => (
                    <div key={index} className="border rounded p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline">{entry.strategy}</Badge>
                        <Badge variant="secondary">{entry.domain}</Badge>
                        <span className="text-xs text-gray-500 ml-auto">
                          {new Date(entry.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="space-y-1">
                        {entry.thoughts.slice(0, 2).map((thought, tidx) => (
                          <p key={tidx} className="text-sm text-gray-700 line-clamp-2">
                            <Badge variant="ghost" className="text-xs mr-2">
                              {thought.type}
                            </Badge>
                            {thought.content}
                          </p>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {activeTab === 'stats' && statistics && (
              <div className="space-y-4">
                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <Card className="p-3 text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {statistics.total_connections}
                    </div>
                    <div className="text-xs text-gray-600">Connections</div>
                  </Card>
                  <Card className="p-3 text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {statistics.mention_count}
                    </div>
                    <div className="text-xs text-gray-600">Mentions</div>
                  </Card>
                  <Card className="p-3 text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {Math.round(statistics.average_confidence * 100)}%
                    </div>
                    <div className="text-xs text-gray-600">Avg Confidence</div>
                  </Card>
                  <Card className="p-3 text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {Math.round(statistics.activity_score * 10) / 10}
                    </div>
                    <div className="text-xs text-gray-600">Activity Score</div>
                  </Card>
                </div>

                {/* Relationship Types */}
                {Object.keys(statistics.relationship_types).length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Relationship Types</h4>
                    <div className="space-y-1">
                      {Object.entries(statistics.relationship_types).map(([type, count]) => (
                        <div key={type} className="flex justify-between items-center">
                          <span className="text-sm">{type}</span>
                          <Badge variant="secondary">{count}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Connected Node Types */}
                {Object.keys(statistics.connected_node_types).length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Connected Node Types</h4>
                    <div className="space-y-1">
                      {Object.entries(statistics.connected_node_types).map(([type, count]) => (
                        <div key={type} className="flex justify-between items-center">
                          <div className="flex items-center gap-2">
                            {getNodeTypeIcon(type, 14)}
                            <span className="text-sm">{type}</span>
                          </div>
                          <Badge variant="secondary">{count}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </ScrollArea>
    </div>
  )
}

export default NodeDetailsPanel