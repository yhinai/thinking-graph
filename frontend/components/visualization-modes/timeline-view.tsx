'use client'

import React, { useState, useEffect, useMemo, useRef } from 'react'
import { Clock, Calendar, ZoomIn, ZoomOut, Play, Pause, SkipBack, SkipForward } from 'lucide-react'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { Badge } from '../ui/badge'
import { ScrollArea } from '../ui/scroll-area'

// Types
interface TimelineNode {
  id: string
  name: string
  timestamp: Date
  type: string
  sessionId: string
  connections: string[]
  properties: Record<string, any>
}

interface TimelineViewProps {
  data: {
    nodes: any[]
    links: any[]
  }
  width?: number
  height?: number
  onNodeSelect?: (nodeId: string) => void
}

interface DateRange {
  start: Date
  end: Date
}

interface TimelineBand {
  id: string
  label: string
  nodes: TimelineNode[]
  color: string
}

// Timeline Controls Component
const TimelineControls: React.FC<{
  onPeriodSelect: (period: DateRange | null) => void
  onZoom: (factor: number) => void
  onPlayToggle: () => void
  isPlaying: boolean
  timeRange: DateRange | null
}> = ({ onPeriodSelect, onZoom, onPlayToggle, isPlaying, timeRange }) => {
  const [selectedPeriod, setSelectedPeriod] = useState<'day' | 'week' | 'month' | 'all'>('all')

  const handlePeriodChange = (period: 'day' | 'week' | 'month' | 'all') => {
    setSelectedPeriod(period)
    if (period === 'all') {
      onPeriodSelect(null)
      return
    }

    const now = new Date()
    const start = new Date(now)
    
    switch (period) {
      case 'day':
        start.setDate(start.getDate() - 1)
        break
      case 'week':
        start.setDate(start.getDate() - 7)
        break
      case 'month':
        start.setMonth(start.getMonth() - 1)
        break
    }

    onPeriodSelect({ start, end: now })
  }

  return (
    <div className="timeline-controls flex items-center gap-4 p-4 bg-white border-b">
      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4" />
        <span className="text-sm font-medium">Time Period:</span>
      </div>
      
      <div className="flex items-center gap-1">
        {(['day', 'week', 'month', 'all'] as const).map((period) => (
          <Button
            key={period}
            variant={selectedPeriod === period ? 'default' : 'outline'}
            size="sm"
            onClick={() => handlePeriodChange(period)}
          >
            {period.charAt(0).toUpperCase() + period.slice(1)}
          </Button>
        ))}
      </div>

      <div className="flex items-center gap-2 ml-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onZoom(1.2)}
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onZoom(0.8)}
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
      </div>

      <div className="flex items-center gap-2 ml-4">
        <Button
          variant="outline"
          size="sm"
          onClick={onPlayToggle}
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </Button>
        <span className="text-sm text-gray-500">
          {isPlaying ? 'Animating...' : 'Paused'}
        </span>
      </div>

      {timeRange && (
        <div className="text-sm text-gray-600 ml-auto">
          <Calendar className="w-4 h-4 inline mr-1" />
          {timeRange.start.toLocaleDateString()} - {timeRange.end.toLocaleDateString()}
        </div>
      )}
    </div>
  )
}

// Timeline Canvas Component
const TimelineCanvas: React.FC<{
  bands: TimelineBand[]
  selectedPeriod: DateRange | null
  width: number
  height: number
  zoomLevel: number
  currentTime?: Date
  onNodeClick?: (node: TimelineNode) => void
}> = ({ bands, selectedPeriod, width, height, zoomLevel, currentTime, onNodeClick }) => {
  const canvasRef = useRef<HTMLDivElement>(null)
  
  // Calculate time scale
  const timeScale = useMemo(() => {
    if (!bands.length) return { start: new Date(), end: new Date(), range: 0 }
    
    const allNodes = bands.flatMap(b => b.nodes)
    if (!allNodes.length) return { start: new Date(), end: new Date(), range: 0 }
    
    let start = selectedPeriod?.start || new Date(Math.min(...allNodes.map(n => n.timestamp.getTime())))
    let end = selectedPeriod?.end || new Date(Math.max(...allNodes.map(n => n.timestamp.getTime())))
    
    // Add some padding
    const padding = (end.getTime() - start.getTime()) * 0.1
    start = new Date(start.getTime() - padding)
    end = new Date(end.getTime() + padding)
    
    return { start, end, range: end.getTime() - start.getTime() }
  }, [bands, selectedPeriod])

  const getNodePosition = (timestamp: Date): number => {
    if (!timeScale.range) return 0
    const elapsed = timestamp.getTime() - timeScale.start.getTime()
    return (elapsed / timeScale.range) * (width - 100) * zoomLevel + 50
  }

  const bandHeight = Math.max(60, (height - 100) / Math.max(bands.length, 1))

  return (
    <div 
      ref={canvasRef}
      className="timeline-canvas relative bg-gray-50"
      style={{ width, height }}
    >
      {/* Time axis */}
      <div className="absolute top-0 left-0 w-full h-8 bg-white border-b flex items-center">
        {Array.from({ length: 10 }, (_, i) => {
          const timestamp = new Date(
            timeScale.start.getTime() + (timeScale.range * i) / 9
          )
          const x = getNodePosition(timestamp)
          
          return (
            <div
              key={i}
              className="absolute text-xs text-gray-500 transform -translate-x-1/2"
              style={{ left: x }}
            >
              {timestamp.toLocaleDateString()}
            </div>
          )
        })}
      </div>

      {/* Timeline bands */}
      <div className="mt-8">
        {bands.map((band, bandIndex) => (
          <div
            key={band.id}
            className="relative border-b"
            style={{ height: bandHeight }}
          >
            {/* Band label */}
            <div className="absolute left-0 top-0 w-12 h-full flex items-center justify-center bg-white border-r">
              <div className="text-xs font-medium text-gray-700 transform -rotate-90 whitespace-nowrap">
                {band.label}
              </div>
            </div>

            {/* Band timeline */}
            <div className="ml-12 relative h-full">
              {/* Background line */}
              <div 
                className="absolute top-1/2 transform -translate-y-1/2 h-0.5 bg-gray-300"
                style={{ 
                  left: 50, 
                  width: Math.max(0, (width - 100) * zoomLevel) 
                }}
              />

              {/* Nodes */}
              {band.nodes.map((node, nodeIndex) => {
                const x = getNodePosition(node.timestamp)
                const isVisible = x >= 0 && x <= width

                if (!isVisible) return null

                return (
                  <div
                    key={node.id}
                    className="absolute top-1/2 transform -translate-y-1/2 -translate-x-1/2 cursor-pointer group"
                    style={{ left: x }}
                    onClick={() => onNodeClick?.(node)}
                  >
                    <div 
                      className={`
                        w-3 h-3 rounded-full border-2 border-white shadow-lg
                        group-hover:scale-125 transition-transform
                      `}
                      style={{ backgroundColor: band.color }}
                    />
                    
                    {/* Tooltip */}
                    <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                      <div className="bg-black text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                        <div className="font-medium">{node.name.slice(0, 30)}...</div>
                        <div>{node.timestamp.toLocaleString()}</div>
                        <Badge variant="outline" className="mt-1 text-xs">
                          {node.type}
                        </Badge>
                      </div>
                    </div>
                  </div>
                )
              })}

              {/* Current time indicator */}
              {currentTime && (
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
                  style={{ left: getNodePosition(currentTime) }}
                >
                  <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-red-500 rounded-full" />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Timeline Legend Component
const TimelineLegend: React.FC<{
  bands: TimelineBand[]
  totalNodes: number
}> = ({ bands, totalNodes }) => {
  return (
    <Card className="timeline-legend p-4 m-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium">Timeline Legend</h3>
        <Badge variant="secondary">{totalNodes} total nodes</Badge>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {bands.map((band) => (
          <div key={band.id} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: band.color }}
            />
            <div>
              <div className="text-sm font-medium">{band.label}</div>
              <div className="text-xs text-gray-500">{band.nodes.length} nodes</div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

// Main Timeline View Component
export const TimelineView: React.FC<TimelineViewProps> = ({
  data,
  width = 800,
  height = 600,
  onNodeSelect
}) => {
  const [timelineData, setTimelineData] = useState<TimelineNode[]>([])
  const [selectedPeriod, setSelectedPeriod] = useState<DateRange | null>(null)
  const [zoomLevel, setZoomLevel] = useState(1)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState<Date | undefined>()

  // Convert graph data to timeline format
  const convertToTimeline = (graphData: { nodes: any[]; links: any[] }): TimelineNode[] => {
    if (!graphData.nodes) return []

    return graphData.nodes.map(node => ({
      id: node.id,
      name: node.name || 'Unknown',
      timestamp: new Date(node.properties?.timestamp || Date.now()),
      type: node.type || 'Unknown',
      sessionId: node.properties?.session_id || 'default',
      connections: graphData.links
        .filter(link => link.source === node.id || link.target === node.id)
        .map(link => link.source === node.id ? link.target : link.source),
      properties: node.properties || {}
    }))
  }

  // Group timeline data into bands
  const timelineBands = useMemo((): TimelineBand[] => {
    const nodesByType = timelineData.reduce((acc, node) => {
      if (!acc[node.type]) {
        acc[node.type] = []
      }
      acc[node.type].push(node)
      return acc
    }, {} as Record<string, TimelineNode[]>)

    const colors = [
      '#4A90E2', '#357ABD', '#50C878', '#FF6B6B', 
      '#9B59B6', '#F39C12', '#E67E22', '#95A5A6'
    ]

    return Object.entries(nodesByType).map(([type, nodes], index) => ({
      id: type,
      label: type,
      nodes: nodes.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime()),
      color: colors[index % colors.length]
    }))
  }, [timelineData])

  // Convert data when it changes
  useEffect(() => {
    const timeline = convertToTimeline(data)
    setTimelineData(timeline)
  }, [data])

  // Animation logic
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null

    if (isPlaying && timelineData.length > 0) {
      const allTimestamps = timelineData.map(n => n.timestamp.getTime()).sort()
      const start = allTimestamps[0]
      const end = allTimestamps[allTimestamps.length - 1]
      const duration = end - start
      
      let progress = 0
      intervalId = setInterval(() => {
        progress += 0.01 // 1% per step
        if (progress >= 1) {
          progress = 0 // Loop
        }
        
        setCurrentTime(new Date(start + duration * progress))
      }, 100) // Update every 100ms
    }

    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [isPlaying, timelineData])

  const handleZoom = (factor: number) => {
    setZoomLevel(prev => Math.max(0.1, Math.min(5, prev * factor)))
  }

  const handlePlayToggle = () => {
    setIsPlaying(!isPlaying)
  }

  const handleNodeClick = (node: TimelineNode) => {
    onNodeSelect?.(node.id)
  }

  if (!timelineData.length) {
    return (
      <div className="timeline-view flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <Clock className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">No Timeline Data</h3>
          <p className="text-sm text-gray-500">
            No nodes with timestamps found in the knowledge graph.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="timeline-view w-full h-full flex flex-col bg-white">
      <TimelineControls
        onPeriodSelect={setSelectedPeriod}
        onZoom={handleZoom}
        onPlayToggle={handlePlayToggle}
        isPlaying={isPlaying}
        timeRange={selectedPeriod}
      />
      
      <ScrollArea className="flex-1">
        <TimelineCanvas
          bands={timelineBands}
          selectedPeriod={selectedPeriod}
          width={width}
          height={height - 100}
          zoomLevel={zoomLevel}
          currentTime={currentTime}
          onNodeClick={handleNodeClick}
        />
      </ScrollArea>
      
      <TimelineLegend 
        bands={timelineBands}
        totalNodes={timelineData.length}
      />
    </div>
  )
}

export default TimelineView