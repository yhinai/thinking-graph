'use client'

import React, { useState, useEffect, useMemo, useRef } from 'react'
import { Grid, RotateCcw, ZoomIn, ZoomOut, Download, Filter, Eye, EyeOff } from 'lucide-react'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { Badge } from '../ui/badge'
import { Slider } from '../ui/slider'
import { ScrollArea } from '../ui/scroll-area'

// Types
interface MatrixCell {
  row: string
  col: string
  value: number
  type: string
  metadata?: Record<string, any>
}

interface MatrixData {
  cells: MatrixCell[]
  rowLabels: string[]
  colLabels: string[]
  maxValue: number
  minValue: number
}

interface MatrixViewProps {
  data: {
    nodes: any[]
    links: any[]
  }
  width?: number
  height?: number
  onNodeSelect?: (nodeId: string) => void
}

// Matrix Controls Component
const MatrixControls: React.FC<{
  onResetView: () => void
  onZoom: (factor: number) => void
  onDownload: () => void
  onFilterByType: (type: string | null) => void
  onThresholdChange: (threshold: number) => void
  nodeTypes: string[]
  selectedType: string | null
  threshold: number
  showLabels: boolean
  onToggleLabels: () => void
  colorScheme: string
  onColorSchemeChange: (scheme: string) => void
}> = ({ 
  onResetView,
  onZoom,
  onDownload,
  onFilterByType,
  onThresholdChange,
  nodeTypes,
  selectedType,
  threshold,
  showLabels,
  onToggleLabels,
  colorScheme,
  onColorSchemeChange
}) => {
  const colorSchemes = [
    { id: 'heat', name: 'Heat Map' },
    { id: 'blues', name: 'Blue Scale' },
    { id: 'greens', name: 'Green Scale' },
    { id: 'viridis', name: 'Viridis' }
  ]

  return (
    <div className="matrix-controls flex items-center gap-4 p-4 bg-white border-b flex-wrap">
      <div className="flex items-center gap-2">
        <Grid className="w-4 h-4" />
        <span className="text-sm font-medium">Matrix View:</span>
      </div>
      
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onResetView}
        >
          <RotateCcw className="w-4 h-4 mr-1" />
          Reset
        </Button>
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

      <div className="flex items-center gap-2">
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

      <div className="flex items-center gap-2">
        <span className="text-sm">Threshold:</span>
        <div className="w-24">
          <Slider
            value={[threshold]}
            onValueChange={([value]) => onThresholdChange(value)}
            min={0}
            max={1}
            step={0.1}
            className="w-full"
          />
        </div>
        <span className="text-xs text-gray-500">{threshold.toFixed(1)}</span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm">Colors:</span>
        <select
          value={colorScheme}
          onChange={(e) => onColorSchemeChange(e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        >
          {colorSchemes.map(scheme => (
            <option key={scheme.id} value={scheme.id}>{scheme.name}</option>
          ))}
        </select>
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={onToggleLabels}
      >
        {showLabels ? <EyeOff className="w-4 h-4 mr-1" /> : <Eye className="w-4 h-4 mr-1" />}
        Labels
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={onDownload}
        className="ml-auto"
      >
        <Download className="w-4 h-4 mr-1" />
        Export
      </Button>
    </div>
  )
}

// Matrix Canvas Component
const MatrixCanvas: React.FC<{
  matrixData: MatrixData
  width: number
  height: number
  threshold: number
  showLabels: boolean
  colorScheme: string
  onCellClick?: (cell: MatrixCell) => void
  onCellHover?: (cell: MatrixCell | null) => void
}> = ({ 
  matrixData, 
  width, 
  height, 
  threshold, 
  showLabels, 
  colorScheme,
  onCellClick,
  onCellHover
}) => {
  const canvasRef = useRef<HTMLDivElement>(null)
  const [hoveredCell, setHoveredCell] = useState<MatrixCell | null>(null)

  const { rowLabels, colLabels, cells, maxValue } = matrixData
  
  // Calculate cell dimensions
  const labelWidth = showLabels ? 120 : 40
  const labelHeight = showLabels ? 30 : 20
  const matrixWidth = width - labelWidth - 40
  const matrixHeight = height - labelHeight - 40
  const cellWidth = Math.max(8, matrixWidth / colLabels.length)
  const cellHeight = Math.max(8, matrixHeight / rowLabels.length)

  // Color scheme functions
  const getColor = (value: number, scheme: string): string => {
    if (value < threshold) return 'transparent'
    
    const intensity = value / maxValue
    
    switch (scheme) {
      case 'heat':
        return `rgba(255, ${Math.floor(255 * (1 - intensity))}, 0, ${0.3 + 0.7 * intensity})`
      case 'blues':
        return `rgba(0, ${Math.floor(100 + 155 * intensity)}, 255, ${0.3 + 0.7 * intensity})`
      case 'greens':
        return `rgba(0, ${Math.floor(100 + 155 * intensity)}, 0, ${0.3 + 0.7 * intensity})`
      case 'viridis':
        const r = Math.floor(68 + 187 * intensity)
        const g = Math.floor(1 + 254 * intensity)
        const b = Math.floor(84 + 171 * (1 - intensity))
        return `rgba(${r}, ${g}, ${b}, ${0.3 + 0.7 * intensity})`
      default:
        return `rgba(59, 130, 246, ${0.3 + 0.7 * intensity})`
    }
  }

  const getBorderColor = (value: number): string => {
    return value >= threshold ? 'border-gray-300' : 'border-gray-100'
  }

  return (
    <div 
      ref={canvasRef} 
      className="matrix-canvas relative bg-white overflow-auto"
      style={{ width, height }}
    >
      <div className="absolute inset-0 p-4">
        {/* Column headers */}
        {showLabels && (
          <div 
            className="absolute top-4 flex"
            style={{ left: labelWidth + 4 }}
          >
            {colLabels.map((label, index) => (
              <div
                key={`col-${index}`}
                className="text-xs text-gray-600 transform -rotate-45 origin-bottom-left"
                style={{ 
                  width: cellWidth,
                  height: labelHeight,
                  lineHeight: `${labelHeight}px`,
                  paddingLeft: 4
                }}
                title={label}
              >
                {label.length > 15 ? `${label.slice(0, 15)}...` : label}
              </div>
            ))}
          </div>
        )}

        {/* Row headers */}
        {showLabels && (
          <div 
            className="absolute left-4 flex flex-col"
            style={{ top: labelHeight + 4 }}
          >
            {rowLabels.map((label, index) => (
              <div
                key={`row-${index}`}
                className="text-xs text-gray-600 text-right pr-2 truncate"
                style={{ 
                  width: labelWidth - 8,
                  height: cellHeight,
                  lineHeight: `${cellHeight}px`
                }}
                title={label}
              >
                {label.length > 20 ? `${label.slice(0, 20)}...` : label}
              </div>
            ))}
          </div>
        )}

        {/* Matrix grid */}
        <div 
          className="absolute grid gap-px bg-gray-200"
          style={{
            left: labelWidth + 4,
            top: labelHeight + 4,
            gridTemplateColumns: `repeat(${colLabels.length}, ${cellWidth}px)`,
            gridTemplateRows: `repeat(${rowLabels.length}, ${cellHeight}px)`
          }}
        >
          {rowLabels.map((rowLabel, rowIndex) =>
            colLabels.map((colLabel, colIndex) => {
              const cell = cells.find(c => c.row === rowLabel && c.col === colLabel)
              const value = cell?.value || 0
              const color = getColor(value, colorScheme)
              const borderColor = getBorderColor(value)

              return (
                <div
                  key={`${rowIndex}-${colIndex}`}
                  className={`border cursor-pointer transition-all duration-200 hover:ring-2 hover:ring-blue-400 ${borderColor}`}
                  style={{
                    backgroundColor: color,
                    width: cellWidth,
                    height: cellHeight
                  }}
                  onClick={() => cell && onCellClick?.(cell)}
                  onMouseEnter={() => {
                    setHoveredCell(cell || null)
                    onCellHover?.(cell || null)
                  }}
                  onMouseLeave={() => {
                    setHoveredCell(null)
                    onCellHover?.(null)
                  }}
                  title={cell ? `${rowLabel} → ${colLabel}: ${value.toFixed(3)}` : 'No connection'}
                />
              )
            })
          )}
        </div>

        {/* Tooltip */}
        {hoveredCell && (
          <div className="absolute z-10 bg-black text-white text-xs px-2 py-1 rounded pointer-events-none">
            <div className="font-medium">{hoveredCell.row} → {hoveredCell.col}</div>
            <div>Value: {hoveredCell.value.toFixed(3)}</div>
            <div>Type: {hoveredCell.type}</div>
          </div>
        )}
      </div>
    </div>
  )
}

// Matrix Legend Component
const MatrixLegend: React.FC<{
  maxValue: number
  minValue: number
  threshold: number
  colorScheme: string
  totalConnections: number
  visibleConnections: number
}> = ({ maxValue, minValue, threshold, colorScheme, totalConnections, visibleConnections }) => {
  const legendSteps = 10
  const getColor = (value: number): string => {
    const intensity = value / maxValue
    
    switch (colorScheme) {
      case 'heat':
        return `rgba(255, ${Math.floor(255 * (1 - intensity))}, 0, ${0.3 + 0.7 * intensity})`
      case 'blues':
        return `rgba(0, ${Math.floor(100 + 155 * intensity)}, 255, ${0.3 + 0.7 * intensity})`
      case 'greens':
        return `rgba(0, ${Math.floor(100 + 155 * intensity)}, 0, ${0.3 + 0.7 * intensity})`
      case 'viridis':
        const r = Math.floor(68 + 187 * intensity)
        const g = Math.floor(1 + 254 * intensity)
        const b = Math.floor(84 + 171 * (1 - intensity))
        return `rgba(${r}, ${g}, ${b}, ${0.3 + 0.7 * intensity})`
      default:
        return `rgba(59, 130, 246, ${0.3 + 0.7 * intensity})`
    }
  }

  return (
    <Card className="matrix-legend p-4 m-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium">Matrix Legend</h3>
        <div className="text-xs text-gray-600">
          {visibleConnections} / {totalConnections} connections shown
        </div>
      </div>
      
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs text-gray-600">Weak</span>
        <div className="flex">
          {Array.from({ length: legendSteps }, (_, i) => {
            const value = (i / (legendSteps - 1)) * maxValue
            return (
              <div
                key={i}
                className="w-6 h-4 border border-gray-300"
                style={{ backgroundColor: getColor(value) }}
                title={value.toFixed(3)}
              />
            )
          })}
        </div>
        <span className="text-xs text-gray-600">Strong</span>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs">
        <div>
          <div className="font-medium">Range</div>
          <div className="text-gray-600">{minValue.toFixed(3)} - {maxValue.toFixed(3)}</div>
        </div>
        <div>
          <div className="font-medium">Threshold</div>
          <div className="text-gray-600">{threshold.toFixed(1)}</div>
        </div>
      </div>
    </Card>
  )
}

// Main Matrix View Component
export const MatrixView: React.FC<MatrixViewProps> = ({
  data,
  width = 800,
  height = 600,
  onNodeSelect
}) => {
  const [matrixData, setMatrixData] = useState<MatrixData | null>(null)
  const [threshold, setThreshold] = useState(0.1)
  const [selectedType, setSelectedType] = useState<string | null>(null)
  const [showLabels, setShowLabels] = useState(true)
  const [colorScheme, setColorScheme] = useState('heat')
  const [zoomLevel, setZoomLevel] = useState(1)

  // Convert graph data to matrix format
  const buildMatrix = (graphData: { nodes: any[]; links: any[] }): MatrixData => {
    const nodes = graphData.nodes.filter(node => 
      !selectedType || node.type === selectedType
    )
    
    if (!nodes.length) {
      return {
        cells: [],
        rowLabels: [],
        colLabels: [],
        maxValue: 0,
        minValue: 0
      }
    }

    // Create adjacency matrix
    const nodeIds = nodes.map(node => node.id)
    const nodeNames = nodes.map(node => node.name || node.id)
    const cells: MatrixCell[] = []
    
    // Initialize matrix with zeros
    nodeIds.forEach(rowId => {
      nodeIds.forEach(colId => {
        cells.push({
          row: rowId,
          col: colId,
          value: 0,
          type: 'none'
        })
      })
    })

    // Fill matrix with link data
    let maxValue = 0
    let minValue = Number.MAX_VALUE

    graphData.links.forEach(link => {
      const sourceIndex = nodeIds.indexOf(link.source)
      const targetIndex = nodeIds.indexOf(link.target)
      
      if (sourceIndex !== -1 && targetIndex !== -1) {
        const value = link.value || link.strength || 1
        
        // Update source -> target
        const cell1 = cells.find(c => c.row === link.source && c.col === link.target)
        if (cell1) {
          cell1.value = value
          cell1.type = link.type || 'connection'
          cell1.metadata = { link }
        }

        // For undirected graphs, also update target -> source
        const cell2 = cells.find(c => c.row === link.target && c.col === link.source)
        if (cell2 && cell2.value === 0) {
          cell2.value = value
          cell2.type = link.type || 'connection'
          cell2.metadata = { link }
        }

        maxValue = Math.max(maxValue, value)
        if (value > 0) {
          minValue = Math.min(minValue, value)
        }
      }
    })

    if (minValue === Number.MAX_VALUE) minValue = 0

    return {
      cells,
      rowLabels: nodeNames,
      colLabels: nodeNames,
      maxValue,
      minValue
    }
  }

  // Get node types for filtering
  const nodeTypes = useMemo(() => {
    if (!data.nodes) return []
    const types = new Set(data.nodes.map(node => node.type || 'Unknown'))
    return Array.from(types).sort()
  }, [data])

  // Rebuild matrix when data or filters change
  useEffect(() => {
    const matrix = buildMatrix(data)
    setMatrixData(matrix)
  }, [data, selectedType])

  // Filter cells by threshold
  const filteredMatrix = useMemo(() => {
    if (!matrixData) return null
    
    const visibleCells = matrixData.cells.filter(cell => cell.value >= threshold)
    
    return {
      ...matrixData,
      cells: visibleCells
    }
  }, [matrixData, threshold])

  const handleCellClick = (cell: MatrixCell) => {
    // Navigate to the connection or show details
    if (cell.metadata?.link) {
      onNodeSelect?.(cell.row)
    }
  }

  const handleZoom = (factor: number) => {
    setZoomLevel(prev => Math.max(0.5, Math.min(3, prev * factor)))
  }

  const handleResetView = () => {
    setThreshold(0.1)
    setSelectedType(null)
    setZoomLevel(1)
    setShowLabels(true)
  }

  const handleDownload = () => {
    // Export matrix data as CSV
    if (!matrixData) return
    
    const csv = [
      ['Source', 'Target', 'Value', 'Type'].join(','),
      ...matrixData.cells
        .filter(cell => cell.value > 0)
        .map(cell => [cell.row, cell.col, cell.value, cell.type].join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'knowledge-graph-matrix.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  if (!matrixData || !matrixData.rowLabels.length) {
    return (
      <div className="matrix-view flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <Grid className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">No Matrix Data</h3>
          <p className="text-sm text-gray-500">
            No nodes or connections available for matrix visualization.
          </p>
        </div>
      </div>
    )
  }

  const visibleConnections = filteredMatrix?.cells.filter(c => c.value > 0).length || 0
  const totalConnections = matrixData.cells.filter(c => c.value > 0).length

  return (
    <div className="matrix-view w-full h-full flex flex-col bg-white">
      <MatrixControls
        onResetView={handleResetView}
        onZoom={handleZoom}
        onDownload={handleDownload}
        onFilterByType={setSelectedType}
        onThresholdChange={setThreshold}
        nodeTypes={nodeTypes}
        selectedType={selectedType}
        threshold={threshold}
        showLabels={showLabels}
        onToggleLabels={() => setShowLabels(!showLabels)}
        colorScheme={colorScheme}
        onColorSchemeChange={setColorScheme}
      />
      
      <div className="flex-1 flex">
        <div className="flex-1">
          <ScrollArea className="h-full">
            <MatrixCanvas
              matrixData={filteredMatrix || matrixData}
              width={width * zoomLevel}
              height={(height - 100) * zoomLevel}
              threshold={threshold}
              showLabels={showLabels}
              colorScheme={colorScheme}
              onCellClick={handleCellClick}
            />
          </ScrollArea>
        </div>
      </div>
      
      <MatrixLegend
        maxValue={matrixData.maxValue}
        minValue={matrixData.minValue}
        threshold={threshold}
        colorScheme={colorScheme}
        totalConnections={totalConnections}
        visibleConnections={visibleConnections}
      />
    </div>
  )
}

export default MatrixView