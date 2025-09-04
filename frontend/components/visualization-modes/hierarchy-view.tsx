'use client'

import React, { useState, useEffect, useMemo, useRef } from 'react'
import { GitBranch, ChevronRight, ChevronDown, ExpandIcon, Minimize2, Search, Filter } from 'lucide-react'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { Badge } from '../ui/badge'
import { Input } from '../ui/input'
import { ScrollArea } from '../ui/scroll-area'

// Types
interface HierarchyNode {
  id: string
  name: string
  type: string
  level: number
  children: HierarchyNode[]
  parent?: HierarchyNode
  properties: Record<string, any>
  connectionCount: number
}

interface HierarchyViewProps {
  data: {
    nodes: any[]
    links: any[]
  }
  width?: number
  height?: number
  onNodeSelect?: (nodeId: string) => void
}

// Hierarchy Controls Component
const HierarchyControls: React.FC<{
  onExpandAll: () => void
  onCollapseAll: () => void
  onSearch: (query: string) => void
  onFilterByType: (type: string | null) => void
  searchQuery: string
  nodeTypes: string[]
  selectedType: string | null
}> = ({ 
  onExpandAll, 
  onCollapseAll, 
  onSearch, 
  onFilterByType, 
  searchQuery, 
  nodeTypes,
  selectedType
}) => {
  return (
    <div className="hierarchy-controls flex items-center gap-4 p-4 bg-white border-b">
      <div className="flex items-center gap-2">
        <GitBranch className="w-4 h-4" />
        <span className="text-sm font-medium">Tree View:</span>
      </div>
      
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onExpandAll}
        >
          <ExpandIcon className="w-4 h-4 mr-1" />
          Expand All
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onCollapseAll}
        >
          <Minimize2 className="w-4 h-4 mr-1" />
          Collapse All
        </Button>
      </div>

      <div className="flex items-center gap-2 ml-4">
        <Search className="w-4 h-4" />
        <Input
          placeholder="Search nodes..."
          value={searchQuery}
          onChange={(e) => onSearch(e.target.value)}
          className="w-48"
        />
      </div>

      <div className="flex items-center gap-2 ml-4">
        <Filter className="w-4 h-4" />
        <select
          value={selectedType || ''}
          onChange={(e) => onFilterByType(e.target.value || null)}
          className="px-2 py-1 border rounded text-sm"
        >
          <option value="">All Types</option>
          {nodeTypes.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
      </div>
    </div>
  )
}

// Tree Node Component
const TreeNodeComponent: React.FC<{
  node: HierarchyNode
  expandedNodes: Set<string>
  onNodeToggle: (nodeId: string) => void
  onNodeClick: (node: HierarchyNode) => void
  searchQuery: string
  depth: number
  isHighlighted: boolean
}> = ({ 
  node, 
  expandedNodes, 
  onNodeToggle, 
  onNodeClick, 
  searchQuery,
  depth,
  isHighlighted 
}) => {
  const hasChildren = node.children.length > 0
  const isExpanded = expandedNodes.has(node.id)
  const indent = depth * 20

  const getNodeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'session':
        return '📁'
      case 'thought':
        return '💭'
      case 'entity':
        return '🔗'
      case 'tool':
        return '🔧'
      default:
        return '📄'
    }
  }

  const getNodeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'session':
        return 'bg-blue-100 border-blue-300'
      case 'thought':
        return 'bg-purple-100 border-purple-300'
      case 'entity':
        return 'bg-green-100 border-green-300'
      case 'tool':
        return 'bg-orange-100 border-orange-300'
      default:
        return 'bg-gray-100 border-gray-300'
    }
  }

  return (
    <div className={`tree-node ${isHighlighted ? 'bg-yellow-50' : ''}`}>
      <div
        className={`
          flex items-center gap-2 p-2 hover:bg-gray-50 cursor-pointer rounded
          ${isHighlighted ? 'ring-2 ring-yellow-300' : ''}
        `}
        style={{ paddingLeft: `${indent + 8}px` }}
        onClick={() => onNodeClick(node)}
      >
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onNodeToggle(node.id)
            }}
            className="w-4 h-4 flex items-center justify-center hover:bg-gray-200 rounded"
          >
            {isExpanded ? (
              <ChevronDown className="w-3 h-3" />
            ) : (
              <ChevronRight className="w-3 h-3" />
            )}
          </button>
        )}
        {!hasChildren && <div className="w-4" />}

        <div className={`w-6 h-6 rounded border-2 flex items-center justify-center text-sm ${getNodeColor(node.type)}`}>
          {getNodeIcon(node.type)}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm truncate">
              {node.name}
            </span>
            <Badge variant="outline" className="text-xs">
              {node.type}
            </Badge>
            {node.connectionCount > 0 && (
              <Badge variant="secondary" className="text-xs">
                {node.connectionCount} connections
              </Badge>
            )}
          </div>
          {node.properties.content && (
            <p className="text-xs text-gray-600 truncate mt-1">
              {node.properties.content.slice(0, 80)}...
            </p>
          )}
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div className="tree-children">
          {node.children.map(child => (
            <TreeNodeComponent
              key={child.id}
              node={child}
              expandedNodes={expandedNodes}
              onNodeToggle={onNodeToggle}
              onNodeClick={onNodeClick}
              searchQuery={searchQuery}
              depth={depth + 1}
              isHighlighted={searchQuery ? child.name.toLowerCase().includes(searchQuery.toLowerCase()) : false}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Statistics Panel Component
const HierarchyStats: React.FC<{
  hierarchyData: HierarchyNode | null
  totalNodes: number
  maxDepth: number
}> = ({ hierarchyData, totalNodes, maxDepth }) => {
  const getNodeTypeStats = (node: HierarchyNode | null): Record<string, number> => {
    if (!node) return {}
    
    const stats: Record<string, number> = {}
    const traverse = (n: HierarchyNode) => {
      stats[n.type] = (stats[n.type] || 0) + 1
      n.children.forEach(traverse)
    }
    
    traverse(node)
    return stats
  }

  const typeStats = useMemo(() => getNodeTypeStats(hierarchyData), [hierarchyData])

  return (
    <Card className="hierarchy-stats p-4 m-4">
      <h3 className="text-sm font-medium mb-3">Hierarchy Statistics</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="text-center">
          <div className="text-lg font-bold text-blue-600">{totalNodes}</div>
          <div className="text-xs text-gray-500">Total Nodes</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-green-600">{maxDepth}</div>
          <div className="text-xs text-gray-500">Max Depth</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-purple-600">{Object.keys(typeStats).length}</div>
          <div className="text-xs text-gray-500">Node Types</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-orange-600">
            {hierarchyData ? hierarchyData.children.length : 0}
          </div>
          <div className="text-xs text-gray-500">Root Children</div>
        </div>
      </div>

      <div>
        <h4 className="text-xs font-medium mb-2">Distribution by Type</h4>
        <div className="space-y-1">
          {Object.entries(typeStats).map(([type, count]) => (
            <div key={type} className="flex justify-between text-xs">
              <span>{type}:</span>
              <span className="font-medium">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}

// Main Hierarchy View Component
export const HierarchyView: React.FC<HierarchyViewProps> = ({
  data,
  width = 800,
  height = 600,
  onNodeSelect
}) => {
  const [hierarchyData, setHierarchyData] = useState<HierarchyNode | null>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState<string | null>(null)

  // Convert graph data to hierarchical structure
  const buildHierarchy = (graphData: { nodes: any[]; links: any[] }): HierarchyNode | null => {
    if (!graphData.nodes.length) return null

    const nodeMap = new Map<string, HierarchyNode>()
    const linkMap = new Map<string, string[]>()

    // Create node map
    graphData.nodes.forEach(node => {
      nodeMap.set(node.id, {
        id: node.id,
        name: node.name || 'Unknown',
        type: node.type || 'Unknown',
        level: 0,
        children: [],
        properties: node.properties || {},
        connectionCount: 0
      })
    })

    // Build connection map
    graphData.links.forEach(link => {
      const sourceConnections = linkMap.get(link.source) || []
      sourceConnections.push(link.target)
      linkMap.set(link.source, sourceConnections)

      const targetConnections = linkMap.get(link.target) || []
      targetConnections.push(link.source)
      linkMap.set(link.target, targetConnections)
    })

    // Set connection counts
    nodeMap.forEach((node, id) => {
      node.connectionCount = linkMap.get(id)?.length || 0
    })

    // Find root nodes (Sessions or nodes with most connections)
    const sessions = Array.from(nodeMap.values()).filter(node => node.type === 'Session')
    let roots = sessions.length ? sessions : []
    
    if (!roots.length) {
      // If no sessions, use nodes with highest connection counts as roots
      const sortedByConnections = Array.from(nodeMap.values())
        .sort((a, b) => b.connectionCount - a.connectionCount)
      roots = sortedByConnections.slice(0, Math.min(5, sortedByConnections.length))
    }

    // Build hierarchy from roots
    const visited = new Set<string>()
    
    const buildSubtree = (nodeId: string, level: number, parent?: HierarchyNode): HierarchyNode | null => {
      if (visited.has(nodeId)) return null
      
      const node = nodeMap.get(nodeId)
      if (!node) return null
      
      visited.add(nodeId)
      node.level = level
      node.parent = parent
      
      // Get connected nodes as children
      const connections = linkMap.get(nodeId) || []
      connections.forEach(connectedId => {
        if (!visited.has(connectedId)) {
          const child = buildSubtree(connectedId, level + 1, node)
          if (child) {
            node.children.push(child)
          }
        }
      })
      
      // Sort children by type and connection count
      node.children.sort((a, b) => {
        if (a.type !== b.type) return a.type.localeCompare(b.type)
        return b.connectionCount - a.connectionCount
      })
      
      return node
    }

    // Create virtual root if multiple roots
    if (roots.length === 1) {
      return buildSubtree(roots[0].id, 0)
    } else {
      const virtualRoot: HierarchyNode = {
        id: 'virtual-root',
        name: 'Knowledge Graph',
        type: 'Root',
        level: 0,
        children: [],
        properties: {},
        connectionCount: 0
      }
      
      roots.forEach(root => {
        const subtree = buildSubtree(root.id, 1, virtualRoot)
        if (subtree) {
          virtualRoot.children.push(subtree)
        }
      })
      
      return virtualRoot
    }
  }

  // Get all node types for filtering
  const nodeTypes = useMemo(() => {
    if (!data.nodes) return []
    const types = new Set(data.nodes.map(node => node.type || 'Unknown'))
    return Array.from(types).sort()
  }, [data])

  // Calculate max depth
  const maxDepth = useMemo(() => {
    if (!hierarchyData) return 0
    
    const getMaxDepth = (node: HierarchyNode): number => {
      if (!node.children.length) return node.level
      return Math.max(...node.children.map(getMaxDepth))
    }
    
    return getMaxDepth(hierarchyData)
  }, [hierarchyData])

  // Total node count
  const totalNodes = useMemo(() => {
    if (!hierarchyData) return 0
    
    const countNodes = (node: HierarchyNode): number => {
      return 1 + node.children.reduce((sum, child) => sum + countNodes(child), 0)
    }
    
    return countNodes(hierarchyData)
  }, [hierarchyData])

  // Build hierarchy when data changes
  useEffect(() => {
    const hierarchy = buildHierarchy(data)
    setHierarchyData(hierarchy)
    
    // Auto-expand first few levels
    if (hierarchy) {
      const autoExpand = new Set<string>()
      const addToExpand = (node: HierarchyNode, maxLevel: number) => {
        if (node.level < maxLevel) {
          autoExpand.add(node.id)
          node.children.forEach(child => addToExpand(child, maxLevel))
        }
      }
      addToExpand(hierarchy, 2) // Auto-expand first 2 levels
      setExpandedNodes(autoExpand)
    }
  }, [data])

  // Filter hierarchy based on search and type filter
  const filteredHierarchy = useMemo(() => {
    if (!hierarchyData || (!searchQuery && !selectedType)) return hierarchyData

    const filterNode = (node: HierarchyNode): HierarchyNode | null => {
      const matchesSearch = !searchQuery || node.name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesType = !selectedType || node.type === selectedType
      
      const filteredChildren = node.children
        .map(filterNode)
        .filter((child): child is HierarchyNode => child !== null)
      
      // Include node if it matches filters OR has matching children
      if (matchesSearch && matchesType) {
        return { ...node, children: filteredChildren }
      } else if (filteredChildren.length > 0) {
        return { ...node, children: filteredChildren }
      }
      
      return null
    }

    return filterNode(hierarchyData)
  }, [hierarchyData, searchQuery, selectedType])

  const handleNodeToggle = (nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId)
      } else {
        newSet.add(nodeId)
      }
      return newSet
    })
  }

  const handleExpandAll = () => {
    if (!hierarchyData) return
    
    const allNodeIds = new Set<string>()
    const traverse = (node: HierarchyNode) => {
      allNodeIds.add(node.id)
      node.children.forEach(traverse)
    }
    traverse(hierarchyData)
    
    setExpandedNodes(allNodeIds)
  }

  const handleCollapseAll = () => {
    setExpandedNodes(new Set())
  }

  const handleNodeClick = (node: HierarchyNode) => {
    if (node.id !== 'virtual-root') {
      onNodeSelect?.(node.id)
    }
  }

  if (!hierarchyData) {
    return (
      <div className="hierarchy-view flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <GitBranch className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">No Hierarchy Data</h3>
          <p className="text-sm text-gray-500">
            Unable to build a hierarchical view from the current graph data.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="hierarchy-view w-full h-full flex flex-col bg-white">
      <HierarchyControls
        onExpandAll={handleExpandAll}
        onCollapseAll={handleCollapseAll}
        onSearch={setSearchQuery}
        onFilterByType={setSelectedType}
        searchQuery={searchQuery}
        nodeTypes={nodeTypes}
        selectedType={selectedType}
      />
      
      <div className="flex-1 flex">
        <ScrollArea className="flex-1 p-4" style={{ height: height - 150 }}>
          {filteredHierarchy && (
            <TreeNodeComponent
              node={filteredHierarchy}
              expandedNodes={expandedNodes}
              onNodeToggle={handleNodeToggle}
              onNodeClick={handleNodeClick}
              searchQuery={searchQuery}
              depth={0}
              isHighlighted={false}
            />
          )}
        </ScrollArea>
        
        <div className="w-80 border-l bg-gray-50">
          <HierarchyStats
            hierarchyData={hierarchyData}
            totalNodes={totalNodes}
            maxDepth={maxDepth}
          />
        </div>
      </div>
    </div>
  )
}

export default HierarchyView