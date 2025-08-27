"use client"

import { useState, useEffect, useMemo, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  Network, 
  Maximize2, 
  Settings, 
  Download, 
  RefreshCw, 
  Layers3, 
  Zap, 
  AlertCircle,
  Circle,
  GitBranch,
  Users,
  Layers,
  Box,
  Grid,
  Clock,
  RotateCcw,
  Share2,
  Eye,
  EyeOff,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Minimize2
} from "lucide-react"
import { ForceGraph3D } from "./force-graph-3d"
import { apiService, GraphData, GraphNode } from "@/lib/api"

export function EnhancedKnowledgeGraphView() {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'unknown'>('unknown')
  const [selectedNode, setSelectedNode] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState('3d-force')
  const [showControls, setShowControls] = useState(true)
  const [controlsExpanded, setControlsExpanded] = useState(true)
  const [statsExpanded, setStatsExpanded] = useState(true)
  const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null)
  const [isMobile, setIsMobile] = useState(false)
  const graphContainerRef = useRef<HTMLDivElement>(null)

  // Handle container resize for responsive design using ResizeObserver
  useEffect(() => {
    const updateDimensions = () => {
      if (typeof window !== 'undefined') {
        const mobile = window.innerWidth < 768
        setIsMobile(mobile)
        
        // On mobile, auto-collapse panels to save space
        if (mobile && showControls) {
          setControlsExpanded(false)
          setStatsExpanded(false)
        }
      }
      
      // Update dimensions based on container size
      if (graphContainerRef.current) {
        const rect = graphContainerRef.current.getBoundingClientRect()
        setDimensions({
          width: Math.max(rect.width, 300), // Minimum width for usability
          height: Math.max(rect.height, 200) // Minimum height for usability
        })
      }
    }

    // Initial measurement with a small delay to ensure container is laid out
    const timeoutId = setTimeout(updateDimensions, 100)

    // Set up ResizeObserver for container size changes
    let resizeObserver: ResizeObserver | null = null
    if (graphContainerRef.current && 'ResizeObserver' in window) {
      resizeObserver = new ResizeObserver(updateDimensions)
      resizeObserver.observe(graphContainerRef.current)
    }

    // Fallback to window resize listener
    window.addEventListener('resize', updateDimensions)
    
    return () => {
      clearTimeout(timeoutId)
      if (resizeObserver) {
        resizeObserver.disconnect()
      }
      window.removeEventListener('resize', updateDimensions)
    }
  }, [showControls])

  // Check backend status
  useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        await apiService.healthCheck()
        setBackendStatus('connected')
      } catch {
        setBackendStatus('disconnected')
      }
    }
    
    checkBackendStatus()
    const interval = setInterval(checkBackendStatus, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  // Load graph data
  const loadGraphData = async () => {
    if (backendStatus !== 'connected') return
    
    setIsLoading(true)
    setError(null)
    try {
      const data = await apiService.getGraphData()
      setGraphData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph data')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (backendStatus === 'connected') {
      loadGraphData()
    }
  }, [backendStatus])

  const handleNodeClick = (node: GraphNode) => {
    console.log('Node clicked:', node)
    // TODO: Implement node detail view
  }

  const handleRefresh = () => {
    loadGraphData()
  }

  const nodeTypeStats = useMemo(() => {
    const stats: Record<string, number> = {}
    graphData.nodes.forEach(node => {
      stats[node.type] = (stats[node.type] || 0) + 1
    })
    return stats
  }, [graphData])

  const getStatusBadge = () => {
    switch (backendStatus) {
      case 'connected':
        return (
          <Badge variant="secondary" className="bg-green-100 text-green-700 border-green-200">
            <Zap className="w-3 h-3 mr-1" />
            Connected
          </Badge>
        )
      case 'disconnected':
        return (
          <Badge variant="secondary" className="bg-red-100 text-red-700 border-red-200">
            <AlertCircle className="w-3 h-3 mr-1" />
            Backend Offline
          </Badge>
        )
      default:
        return (
          <Badge variant="secondary" className="bg-gray-100 text-gray-700 border-gray-200">
            <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
            Checking...
          </Badge>
        )
    }
  }

  return (
    <div className="flex-1 flex flex-col relative">
      {/* Glass Top Header */}
      <div className="p-4 relative">
        <div className="absolute inset-0 bg-gradient-to-r from-white/10 via-white/5 to-white/10 backdrop-blur-3xl border-b border-white/20 shadow-2xl"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-pink-500/5"></div>
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-xl border border-white/30 flex items-center justify-center shadow-lg">
                <Circle className="w-4 h-4 sm:w-5 sm:h-5 text-purple-300" />
            </div>
              <h2 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent">
                Knowledge Graph
              </h2>
              <span className="hidden sm:inline text-sm text-white/70 font-medium">Interactive 3D visualization space</span>
            </div>
          </div>

          <div className="flex items-center gap-1 sm:gap-3">
            <Button variant="ghost" size="sm" className="hidden sm:flex bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            <Button variant="ghost" size="sm" className="hidden md:flex bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg">
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
            <Button variant="ghost" size="sm" className="hidden sm:flex bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setShowControls(!showControls)}
              className="bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg"
            >
              {showControls ? <EyeOff className="w-4 h-4 sm:mr-2" /> : <Eye className="w-4 h-4 sm:mr-2" />}
              <span className="hidden sm:inline">{showControls ? 'Hide' : 'Show'} Controls</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Enhanced Glass Graph Controls */}
      {showControls && (
        <div className={`absolute ${isMobile ? (controlsExpanded || statsExpanded ? 'top-24 left-2 right-2' : 'top-24 left-2') : 'top-24 left-2 sm:left-4 lg:left-6'} z-50 transform-gpu transition-all duration-300`}>
          <div className="relative group isolate">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
            <div className={`relative bg-gradient-to-br from-white/10 via-white/5 to-white/10 backdrop-blur-3xl rounded-3xl border border-white/20 shadow-2xl transition-all duration-300 ${isMobile ? ((controlsExpanded || statsExpanded) ? 'w-full' : 'w-16') : controlsExpanded ? 'w-72 sm:w-80 lg:min-w-[320px]' : 'w-16'} max-w-[90vw] will-change-transform overflow-hidden`}>
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent rounded-3xl"></div>
              <div className="relative z-10">
                <div className={`flex items-center justify-between ${controlsExpanded ? 'p-4 sm:p-6' : 'p-4'}`}>
                  <h3 className={`text-white font-bold flex items-center gap-3 text-lg transition-all duration-300 ${controlsExpanded ? 'opacity-100' : 'opacity-0 w-0 overflow-hidden'}`}>
                    <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-blue-400/20 to-purple-400/20 backdrop-blur-xl border border-white/30 flex items-center justify-center">
                      <Settings className="w-4 h-4 text-white" />
                    </div>
                    Graph Controls
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setControlsExpanded(!controlsExpanded)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        setControlsExpanded(!controlsExpanded)
                      }
                    }}
                    className={`bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg transition-all duration-300 ${controlsExpanded ? '' : 'w-8 h-8 p-0 rounded-xl hover:scale-110'}`}
                    title={controlsExpanded ? 'Collapse controls' : 'Expand controls'}
                    aria-label={controlsExpanded ? 'Collapse graph controls panel' : 'Expand graph controls panel'}
                  >
                    {controlsExpanded ? (
                      <ChevronLeft className="w-4 h-4" />
                    ) : (
                      <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-blue-400/20 to-purple-400/20 backdrop-blur-xl border border-white/30 flex items-center justify-center">
                        <Settings className="w-4 h-4 text-white" />
                      </div>
                    )}
                  </Button>
                </div>
                
                {/* Collapsible Content */}
                <div className={`transition-all duration-300 overflow-hidden ${controlsExpanded ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0'}`}>
                  {/* Enhanced View Mode Selector */}
                  <div className="space-y-4 mb-6 sm:mb-8">
                    <label className="text-white/80 text-sm font-medium">View Mode</label>
                    <div className={`grid ${isMobile ? 'grid-cols-2 gap-2' : 'grid-cols-2 gap-3'}`}>
                      {[
                        { id: '3d-force', name: '3D Force', icon: <Box className="w-4 h-4" /> },
                        { id: 'timeline', name: 'Timeline', icon: <Clock className="w-4 h-4" /> },
                        { id: 'hierarchy', name: 'Tree', icon: <GitBranch className="w-4 h-4" /> },
                        { id: 'matrix', name: 'Matrix', icon: <Grid className="w-4 h-4" /> }
                      ].map(mode => (
                        <button
                          key={mode.id}
                          onClick={() => setViewMode(mode.id)}
                          className={`relative group flex items-center ${isMobile ? 'gap-2 p-2' : 'gap-3 p-3'} rounded-xl text-sm transition-all duration-300 overflow-hidden ${
                            viewMode === mode.id 
                              ? 'bg-gradient-to-br from-blue-500/30 to-purple-500/30 text-white border-2 border-blue-400/50 shadow-lg shadow-blue-500/25' 
                              : 'bg-gradient-to-br from-white/5 to-white/10 text-white/80 hover:text-white hover:bg-white/20 border border-white/20'
                          }`}
                        >
                          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent"></div>
                          <div className="relative z-10 flex items-center gap-3">
                            {mode.icon}
                            {mode.name}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Enhanced Node Types Filter */}
                  <div className="space-y-4 mb-8">
                    <label className="text-white/80 text-sm font-medium">Node Types</label>
                    <div className="space-y-3">
                      {Object.entries(nodeTypeStats).map(([type, count]) => (
                        <label key={type} className="flex items-center gap-4 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all duration-200 cursor-pointer group border border-white/10">
                          <input type="checkbox" className="w-4 h-4 rounded-md bg-white/10 border-white/30 text-blue-500 focus:ring-blue-400/50 focus:ring-2" defaultChecked />
                          <div className="w-4 h-4 rounded-full shadow-lg bg-blue-500"></div>
                          <span className="flex-1 text-white/90 font-medium capitalize">{type}</span>
                          <span className="text-white/60 text-sm bg-white/10 px-2 py-1 rounded-lg">({count})</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Enhanced Quick Actions */}
                  <div className="grid grid-cols-2 gap-3 pb-2">
                    <Button variant="secondary" size="sm" className="bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg">
                      <RotateCcw className="w-4 h-4 mr-2" />
                      Reset
                    </Button>
                    <Button variant="secondary" size="sm" className="bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg">
                      <Maximize2 className="w-4 h-4 mr-2" />
                      Focus
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Glass Graph Stats */}
      {showControls && (
        <div className={`absolute ${isMobile ? (controlsExpanded || statsExpanded ? 'top-80 left-2 right-2' : 'top-24 right-2') : 'top-24 right-2 sm:right-4 lg:right-6'} z-50 transform-gpu transition-all duration-300`}>
          <div className="relative group isolate">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
            <div className={`relative bg-gradient-to-br from-white/10 via-white/5 to-white/10 backdrop-blur-3xl rounded-3xl border border-white/20 shadow-2xl transition-all duration-300 ${isMobile ? ((controlsExpanded || statsExpanded) ? 'w-full' : 'w-16') : statsExpanded ? 'w-80 sm:w-88 lg:min-w-[360px]' : 'w-16'} max-w-[90vw] will-change-transform overflow-hidden`}>
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent rounded-3xl"></div>
              <div className="relative z-10">
                <div className={`flex items-center justify-between ${statsExpanded ? 'p-4 sm:p-6' : 'p-4'}`}>
                  <h3 className={`text-white font-bold flex items-center gap-3 text-lg transition-all duration-300 ${statsExpanded ? 'opacity-100' : 'opacity-0 w-0 overflow-hidden'}`}>
                    <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-purple-400/20 to-pink-400/20 backdrop-blur-xl border border-white/30 flex items-center justify-center">
                      <Circle className="w-4 h-4 text-white" />
                    </div>
                    Graph Analytics
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setStatsExpanded(!statsExpanded)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        setStatsExpanded(!statsExpanded)
                      }
                    }}
                    className={`bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg transition-all duration-300 ${statsExpanded ? '' : 'w-8 h-8 p-0 rounded-xl hover:scale-110'}`}
                    title={statsExpanded ? 'Collapse analytics' : 'Expand analytics'}
                    aria-label={statsExpanded ? 'Collapse graph analytics panel' : 'Expand graph analytics panel'}
                  >
                    {statsExpanded ? (
                      <ChevronRight className="w-4 h-4" />
                    ) : (
                      <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-purple-400/20 to-pink-400/20 backdrop-blur-xl border border-white/30 flex items-center justify-center">
                        <Circle className="w-4 h-4 text-white" />
                      </div>
                    )}
                  </Button>
                </div>
                
                {/* Collapsible Stats Content */}
                <div className={`transition-all duration-300 overflow-hidden ${statsExpanded ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0'}`}>
                  <div className="grid grid-cols-2 gap-4 pb-2">
                    <div className="relative group">
                      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-2xl blur-sm group-hover:blur-none transition-all duration-300"></div>
                      <div className="relative bg-gradient-to-br from-white/10 via-white/5 to-white/10 backdrop-blur-2xl rounded-2xl p-5 border border-white/20 shadow-2xl overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent"></div>
                        <div className="relative z-10">
                          <div className="flex items-center justify-between mb-3">
                            <div>
                              <p className="text-white/80 text-sm font-medium">Nodes</p>
                              <p className="text-white text-2xl font-bold mt-1">{graphData.nodes.length}</p>
                            </div>
                            <div className="text-white/80 bg-white/10 p-2 rounded-xl backdrop-blur-sm">
                              <Circle className="w-5 h-5" />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="relative group">
                      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-2xl blur-sm group-hover:blur-none transition-all duration-300"></div>
                      <div className="relative bg-gradient-to-br from-white/10 via-white/5 to-white/10 backdrop-blur-2xl rounded-2xl p-5 border border-white/20 shadow-2xl overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent"></div>
                        <div className="relative z-10">
                          <div className="flex items-center justify-between mb-3">
                            <div>
                              <p className="text-white/80 text-sm font-medium">Connections</p>
                              <p className="text-white text-2xl font-bold mt-1">{graphData.links.length}</p>
                            </div>
                            <div className="text-white/80 bg-white/10 p-2 rounded-xl backdrop-blur-sm">
                              <GitBranch className="w-5 h-5" />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced 3D Glass Graph Visualization */}
      <div className="flex-1 relative overflow-hidden isolate">
        {/* Background layers - lowest z-index */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900/80 via-indigo-900/60 to-purple-900/80 z-0"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,rgba(120,119,198,0.15),transparent_60%)] z-0"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_70%,rgba(147,51,234,0.15),transparent_60%)] z-0"></div>
        
        {/* Status overlays - above graph but below controls */}
        {backendStatus === 'disconnected' && (
          <div className="absolute inset-0 flex items-center justify-center z-20">
            <div className="relative group isolate">
              <div className="absolute inset-0 bg-gradient-to-br from-red-500/20 to-pink-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
              <div className="relative bg-gradient-to-br from-white/10 via-white/5 to-white/10 backdrop-blur-3xl rounded-3xl border border-red-500/30 shadow-2xl p-8 max-w-md text-center will-change-transform">
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent rounded-3xl"></div>
                <div className="relative z-10">
                  <AlertCircle className="w-16 h-16 mx-auto mb-4 text-red-400" />
                  <h3 className="text-lg font-semibold text-white mb-2">Backend Disconnected</h3>
                  <p className="text-white/70 mb-4">
                Please start the thinking-graph backend server to view the knowledge graph.
              </p>
                  <p className="text-sm text-white/60">
                    Run: <code className="bg-white/10 px-2 py-1 rounded text-white/80">python app.py</code> in the thinking-graph directory
              </p>
                </div>
              </div>
            </div>
          </div>
        )}

                {backendStatus === 'connected' && graphData.nodes.length === 0 && !isLoading && (
          <div className="absolute inset-0 flex items-center justify-center z-20">
            <div className="relative group isolate">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
              <div className="relative bg-gradient-to-br from-white/10 via-white/5 to-white/10 backdrop-blur-3xl rounded-3xl border border-white/20 shadow-2xl p-8 max-w-md text-center will-change-transform">
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent rounded-3xl"></div>
                <div className="relative z-10">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-xl border border-white/30 flex items-center justify-center shadow-2xl">
                    <Layers3 className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">3D Knowledge Graph</h3>
                  <p className="text-white/70 mb-4">
                    Start chatting to build your knowledge graph. Each conversation will create nodes and relationships
                    visualized in 3D space.
                  </p>
                  <div className="space-y-2 text-sm text-white/60">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full shadow-lg"></div>
                      <span>Nodes: Concepts & Entities</span>
                    </div>
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-2 h-2 bg-purple-400 rounded-full shadow-lg"></div>
                      <span>Edges: Relationships</span>
                    </div>
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-2 h-2 bg-pink-400 rounded-full shadow-lg"></div>
                      <span>Clusters: Topic Groups</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
              </div>
            )}

                {/* 3D Graph Container - low z-index to stay behind controls */}
        <div ref={graphContainerRef} className="absolute inset-0 z-5 w-full h-full">
          {backendStatus === 'connected' && graphData.nodes.length > 0 && dimensions && (
            <div className="w-full h-full isolate">
                <ForceGraph3D
                  data={graphData}
                  width={dimensions.width}
                  height={dimensions.height}
                  onNodeClick={handleNodeClick}
                />
              </div>
            )}
        </div>
        
                {/* Enhanced Glass overlay info - above graph but below controls */}
        <div className="absolute bottom-4 sm:bottom-6 left-1/2 transform -translate-x-1/2 z-30 transform-gpu max-w-[90vw]">
          <div className="relative group isolate">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-2xl blur-lg group-hover:blur-xl transition-all duration-300"></div>
            <div className="relative bg-gradient-to-r from-white/10 via-white/5 to-white/10 backdrop-blur-2xl rounded-2xl px-3 sm:px-6 py-2 sm:py-3 border border-white/20 shadow-2xl will-change-transform">
              <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent rounded-2xl"></div>
              <span className="text-white/90 text-xs sm:text-sm font-medium relative z-10 flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full animate-pulse ${backendStatus === 'connected' ? 'bg-green-400' : 'bg-red-400'}`}></div>
                {backendStatus === 'connected' 
                  ? (isMobile ? 'Ready • Tap to explore' : 'Ready for interaction • Use mouse to explore • Click nodes for details')
                  : 'Backend offline • Start server to interact'
                }
              </span>
            </div>
                </div>
              </div>

        {/* Refresh Button - above graph but below main controls */}
        <div className="absolute top-4 right-4 z-40 transform-gpu">
          <div className="isolate">
          <Button 
              variant="ghost" 
            size="sm" 
              className="bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 shadow-lg will-change-transform"
            onClick={handleRefresh}
            disabled={isLoading || backendStatus !== 'connected'}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
              </div>

        {/* Loading overlay - highest priority */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-100 isolate">
            <div className="text-center space-y-4 will-change-transform">
              <div className="w-12 h-12 border-3 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-cyan-200 text-lg">Loading 3D Knowledge Graph...</p>
              <p className="text-cyan-300 text-sm">
                Rendering {graphData.nodes.length} nodes and {graphData.links.length} connections
                {dimensions && ` • ${Math.round(dimensions.width)}×${Math.round(dimensions.height)}`}
              </p>
            </div>
        </div>
        )}
      </div>
    </div>
  )
}