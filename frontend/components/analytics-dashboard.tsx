'use client'

import React, { useState, useEffect } from 'react'
import { TrendingUp, Network, Brain, Layers, Calendar, BarChart, PieChart, Activity, Clock, Users, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from './ui/button'
import { Card } from './ui/card'
import { Badge } from './ui/badge'
import { ScrollArea } from './ui/scroll-area'

// Types
interface KnowledgeMetrics {
  total_nodes: number
  total_connections: number
  total_sessions: number
  knowledge_depth: number
  growth_rate: number
  topic_clusters: TopicCluster[]
  most_connected_concepts: ConceptRanking[]
  session_insights: SessionInsight[]
  growth_data: GrowthDataPoint[]
  time_range: string
  generated_at: string
}

interface TopicCluster {
  name: string
  types: string[]
  connections: number
  related_types: string[]
  definition?: string
  cluster_size: number
}

interface ConceptRanking {
  name: string
  types: string[]
  connections: number
  avg_strength: number
  confidence: number
}

interface SessionInsight {
  session_id: string
  strategy: string
  domain: string
  timestamp: string
  thought_count: number
  thought_types: Record<string, number>
  entities_discussed: number
}

interface GrowthDataPoint {
  date: string
  type: string
  count: number
}

interface AnalyticsDashboardProps {
  className?: string
}

// Metric Card Component
const MetricCard: React.FC<{
  title: string
  value: number | string
  trend?: number
  icon: React.ReactNode
  description?: string
  color?: string
}> = ({ title, value, trend, icon, description, color = 'blue' }) => {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50 border-blue-200',
    green: 'text-green-600 bg-green-50 border-green-200',
    purple: 'text-purple-600 bg-purple-50 border-purple-200',
    orange: 'text-orange-600 bg-orange-50 border-orange-200',
    red: 'text-red-600 bg-red-50 border-red-200'
  }

  return (
    <Card className={`p-4 ${colorClasses[color as keyof typeof colorClasses]} border`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-white shadow-sm">
            {icon}
          </div>
          <div>
            <div className="text-2xl font-bold">{value}</div>
            <div className="text-sm font-medium">{title}</div>
            {description && (
              <div className="text-xs text-gray-600 mt-1">{description}</div>
            )}
          </div>
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-sm ${
            trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-600'
          }`}>
            {trend > 0 ? <ArrowUp className="w-4 h-4" /> : trend < 0 ? <ArrowDown className="w-4 h-4" /> : null}
            {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
    </Card>
  )
}

// Topic Clusters Chart Component
const TopicClustersChart: React.FC<{
  clusters: TopicCluster[]
}> = ({ clusters }) => {
  const maxConnections = Math.max(...clusters.map(c => c.connections), 1)

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-5 h-5 text-purple-600" />
        <h3 className="font-semibold">Top Knowledge Clusters</h3>
      </div>
      
      <div className="space-y-3">
        {clusters.slice(0, 8).map((cluster, index) => (
          <div key={cluster.name} className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-sm font-medium text-purple-600">
              {index + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium text-sm truncate">{cluster.name}</span>
                <Badge variant="outline" className="text-xs">
                  {cluster.connections} connections
                </Badge>
              </div>
              {cluster.definition && (
                <p className="text-xs text-gray-600 line-clamp-1">
                  {cluster.definition.slice(0, 100)}...
                </p>
              )}
              <div className="flex items-center gap-1 mt-1">
                {cluster.types.slice(0, 2).map(type => (
                  <Badge key={type} variant="secondary" className="text-xs">
                    {type}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="w-16">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full"
                  style={{ width: `${(cluster.connections / maxConnections) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

// Growth Chart Component  
const GrowthChart: React.FC<{
  data: GrowthDataPoint[]
  timeRange: string
}> = ({ data, timeRange }) => {
  // Group data by date
  const dailyGrowth = data.reduce((acc, point) => {
    const date = point.date || 'Unknown'
    if (!acc[date]) {
      acc[date] = { date, total: 0, types: {} }
    }
    acc[date].total += point.count
    acc[date].types[point.type] = (acc[date].types[point.type] || 0) + point.count
    return acc
  }, {} as Record<string, { date: string; total: number; types: Record<string, number> }>)

  const chartData = Object.values(dailyGrowth).sort((a, b) => a.date.localeCompare(b.date))
  const maxValue = Math.max(...chartData.map(d => d.total), 1)

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-green-600" />
        <h3 className="font-semibold">Knowledge Growth ({timeRange})</h3>
      </div>
      
      <div className="space-y-2">
        {chartData.slice(-10).map((day, index) => (
          <div key={day.date} className="flex items-center gap-3">
            <div className="w-16 text-xs text-gray-600">
              {day.date === 'Unknown' ? 'Unknown' : new Date(day.date).toLocaleDateString()}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium">{day.total} new nodes</span>
                <div className="flex gap-1">
                  {Object.entries(day.types).slice(0, 3).map(([type, count]) => (
                    <Badge key={type} variant="secondary" className="text-xs">
                      {type}: {count}
                    </Badge>
                  ))}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${(day.total / maxValue) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {chartData.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <BarChart className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>No growth data available</p>
        </div>
      )}
    </Card>
  )
}

// Session Insights Component
const SessionInsights: React.FC<{
  insights: SessionInsight[]
}> = ({ insights }) => {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-blue-600" />
        <h3 className="font-semibold">Recent Sessions</h3>
      </div>
      
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {insights.slice(0, 10).map((session) => (
          <div key={session.session_id} className="border rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {session.strategy}
                </Badge>
                <Badge variant="secondary" className="text-xs">
                  {session.domain}
                </Badge>
              </div>
              <div className="text-xs text-gray-500">
                {session.timestamp ? new Date(session.timestamp).toLocaleDateString() : 'Unknown'}
              </div>
            </div>
            
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-1">
                <Brain className="w-4 h-4 text-gray-400" />
                <span>{session.thought_count} thoughts</span>
              </div>
              <div className="flex items-center gap-1">
                <Network className="w-4 h-4 text-gray-400" />
                <span>{session.entities_discussed} entities</span>
              </div>
            </div>
            
            {Object.keys(session.thought_types).length > 0 && (
              <div className="flex gap-1 mt-2">
                {Object.entries(session.thought_types).slice(0, 3).map(([type, count]) => (
                  <Badge key={type} variant="ghost" className="text-xs">
                    {type}: {count}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {insights.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Users className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>No session data available</p>
        </div>
      )}
    </Card>
  )
}

// Connection Density Component
const ConnectionDensity: React.FC<{
  concepts: ConceptRanking[]
}> = ({ concepts }) => {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <Network className="w-5 h-5 text-orange-600" />
        <h3 className="font-semibold">Highly Connected Concepts</h3>
      </div>
      
      <div className="space-y-2">
        {concepts.slice(0, 8).map((concept, index) => (
          <div key={concept.name} className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center text-xs font-medium text-orange-600">
              {index + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm truncate">{concept.name}</span>
                <Badge variant="outline" className="text-xs">
                  {concept.connections} links
                </Badge>
              </div>
              <div className="flex items-center gap-2 mt-1">
                {concept.types.slice(0, 2).map(type => (
                  <Badge key={type} variant="secondary" className="text-xs">
                    {type}
                  </Badge>
                ))}
                <div className="text-xs text-gray-500">
                  Strength: {(concept.avg_strength * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

// Time Range Selector
const TimeRangeSelector: React.FC<{
  value: string
  onChange: (range: string) => void
}> = ({ value, onChange }) => {
  const ranges = [
    { id: 'day', name: 'Last Day' },
    { id: 'week', name: 'Last Week' },
    { id: 'month', name: 'Last Month' },
    { id: 'all', name: 'All Time' }
  ]

  return (
    <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
      {ranges.map(range => (
        <Button
          key={range.id}
          variant={value === range.id ? 'default' : 'ghost'}
          size="sm"
          onClick={() => onChange(range.id)}
          className={`h-8 px-3 text-xs ${
            value === range.id ? 'bg-white shadow-sm' : ''
          }`}
        >
          {range.name}
        </Button>
      ))}
    </div>
  )
}

// Main Analytics Dashboard Component
export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  className = ''
}) => {
  const [metrics, setMetrics] = useState<KnowledgeMetrics | null>(null)
  const [timeRange, setTimeRange] = useState<string>('week')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAnalytics = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/analytics?range=${timeRange}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch analytics: ${response.status}`)
      }
      
      const data = await response.json()
      if (data.success) {
        setMetrics(data.analytics)
      } else {
        throw new Error(data.error || 'Analytics request failed')
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
      setError(error instanceof Error ? error.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch analytics when component mounts or time range changes
  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  if (isLoading) {
    return (
      <div className={`analytics-dashboard ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading analytics...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`analytics-dashboard ${className}`}>
        <Card className="p-6">
          <div className="text-center">
            <BarChart className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">Analytics Error</h3>
            <p className="text-sm text-gray-500 mb-4">{error}</p>
            <Button onClick={fetchAnalytics} variant="outline">
              Try Again
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  if (!metrics) {
    return null
  }

  return (
    <div className={`analytics-dashboard space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Knowledge Analytics</h2>
          <p className="text-gray-600">
            Insights into your knowledge graph growth and patterns
          </p>
        </div>
        <div className="flex items-center gap-4">
          <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
          <Button onClick={fetchAnalytics} variant="outline">
            <Activity className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Knowledge"
          value={metrics.total_nodes}
          trend={metrics.growth_rate}
          icon={<Brain className="w-6 h-6" />}
          description="Concepts and entities"
          color="blue"
        />
        <MetricCard
          title="Connections"
          value={metrics.total_connections}
          icon={<Network className="w-6 h-6" />}
          description="Relationships mapped"
          color="green"
        />
        <MetricCard
          title="Sessions"
          value={metrics.total_sessions}
          icon={<Users className="w-6 h-6" />}
          description="Thinking sessions"
          color="purple"
        />
        <MetricCard
          title="Knowledge Depth"
          value={metrics.knowledge_depth}
          icon={<Layers className="w-6 h-6" />}
          description="Avg connections per concept"
          color="orange"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GrowthChart 
          data={metrics.growth_data} 
          timeRange={timeRange} 
        />
        <TopicClustersChart 
          clusters={metrics.topic_clusters} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ConnectionDensity 
          concepts={metrics.most_connected_concepts} 
        />
        <SessionInsights 
          insights={metrics.session_insights} 
        />
      </div>

      {/* Footer */}
      <div className="text-center text-sm text-gray-500">
        <Clock className="w-4 h-4 inline mr-1" />
        Generated: {new Date(metrics.generated_at).toLocaleString()}
      </div>
    </div>
  )
}

export default AnalyticsDashboard