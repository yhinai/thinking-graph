'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Search, Filter, X, Loader2, ArrowRight, Hash, Link2, Brain, Users, Wrench, MapPin } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import { Card } from './ui/card'
import { ScrollArea } from './ui/scroll-area'

// Types
interface SearchResult {
  nodes: SearchNode[]
  relationships: SearchRelationship[]
  total_results: number
}

interface SearchNode {
  id: string
  name: string
  type: string
  labels: string[]
  confidence: number
  score: number
  properties: Record<string, any>
  snippet: string
}

interface SearchRelationship {
  id: string
  type: string
  properties: Record<string, any>
  score: number
  start_node: {
    id: string | null
    name: string | null
  }
  end_node: {
    id: string | null
    name: string | null
  }
}

interface SearchSuggestion {
  text: string
  types: string[]
  frequency: number
}

interface GraphSearchProps {
  onSearchResults?: (results: SearchResult) => void
  onNodeSelect?: (nodeId: string) => void
  className?: string
}

// Component for node type icons
const getNodeTypeIcon = (type: string, size = 16) => {
  switch (type.toLowerCase()) {
    case 'entity':
      return <Brain size={size} />
    case 'person':
      return <Users size={size} />
    case 'tool':
      return <Wrench size={size} />
    case 'location':
      return <MapPin size={size} />
    case 'session':
      return <Hash size={size} />
    case 'thought':
      return <Brain size={size} />
    default:
      return <Link2 size={size} />
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
    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getColor(confidence) }} />
  )
}

export const GraphSearch: React.FC<GraphSearchProps> = ({
  onSearchResults,
  onNodeSelect,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null)
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchType, setSearchType] = useState<'all' | 'nodes' | 'relationships'>('all')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Debounced suggestions fetching
  const fetchSuggestions = useCallback(
    async (query: string) => {
      if (query.length < 2) {
        setSuggestions([])
        return
      }

      try {
        const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}&limit=8`)
        if (response.ok) {
          const data = await response.json()
          setSuggestions(data.suggestions || [])
        }
      } catch (error) {
        console.error('Failed to fetch suggestions:', error)
      }
    },
    []
  )

  // Debounce suggestions
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery && showSuggestions) {
        fetchSuggestions(searchQuery)
      } else {
        setSuggestions([])
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [searchQuery, showSuggestions, fetchSuggestions])

  const performSearch = async (query: string = searchQuery) => {
    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    setIsSearching(true)
    setError(null)
    setShowSuggestions(false)

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: query.trim(),
          type: searchType,
          limit: 20
        })
      })

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`)
      }

      const data = await response.json()
      
      if (data.success) {
        setSearchResults(data.results)
        onSearchResults?.(data.results)
      } else {
        throw new Error(data.error || 'Search failed')
      }
    } catch (error) {
      console.error('Search failed:', error)
      setError(error instanceof Error ? error.message : 'Search failed')
      setSearchResults(null)
    } finally {
      setIsSearching(false)
    }
  }

  const handleInputChange = (value: string) => {
    setSearchQuery(value)
    if (value.length > 0) {
      setShowSuggestions(true)
    }
  }

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    setSearchQuery(suggestion.text)
    setShowSuggestions(false)
    performSearch(suggestion.text)
  }

  const clearSearch = () => {
    setSearchQuery('')
    setSearchResults(null)
    setError(null)
    setShowSuggestions(false)
  }

  const handleNodeClick = (nodeId: string) => {
    onNodeSelect?.(nodeId)
  }

  return (
    <div className={`graph-search ${className}`}>
      {/* Search Input Section */}
      <div className="relative mb-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="text"
              placeholder="Search nodes, concepts, or relationships..."
              value={searchQuery}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  performSearch()
                } else if (e.key === 'Escape') {
                  setShowSuggestions(false)
                }
              }}
              onFocus={() => searchQuery.length > 0 && setShowSuggestions(true)}
              className="pl-10 pr-10"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearSearch}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>

          {/* Search Type Filter */}
          <div className="flex items-center gap-1 border rounded-md p-1">
            {(['all', 'nodes', 'relationships'] as const).map((type) => (
              <Button
                key={type}
                variant={searchType === type ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setSearchType(type)}
                className="h-8 px-2 text-xs"
              >
                {type === 'all' ? 'All' : type === 'nodes' ? 'Nodes' : 'Relations'}
              </Button>
            ))}
          </div>

          <Button 
            onClick={() => performSearch()}
            disabled={isSearching || !searchQuery.trim()}
            className="px-4"
          >
            {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
          </Button>
        </div>

        {/* Search Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <Card className="absolute top-full left-0 right-0 z-50 mt-1 p-2">
            <div className="space-y-1">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full flex items-center justify-between p-2 hover:bg-gray-50 rounded text-left"
                >
                  <div className="flex items-center gap-2">
                    <Search className="w-3 h-3 text-gray-400" />
                    <span className="text-sm">{suggestion.text}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {suggestion.types.slice(0, 2).map(type => (
                      <Badge key={type} variant="secondary" className="text-xs">
                        {type}
                      </Badge>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Search Results */}
      {searchResults && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">
              Search Results ({searchResults.total_results})
            </h3>
            {searchResults.total_results > 0 && (
              <Button variant="outline" size="sm" onClick={clearSearch}>
                Clear Results
              </Button>
            )}
          </div>

          {searchResults.total_results === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Search className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>No results found for "{searchQuery}"</p>
              <p className="text-sm">Try different keywords or check your spelling</p>
            </div>
          ) : (
            <ScrollArea className="h-96">
              <div className="space-y-3">
                {/* Node Results */}
                {searchResults.nodes.map((node) => (
                  <Card 
                    key={node.id}
                    className="p-3 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => handleNodeClick(node.id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex items-center gap-2 mt-1">
                        {getNodeTypeIcon(node.type, 18)}
                        <ConfidenceIndicator confidence={node.confidence} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-sm truncate">{node.name}</h4>
                          <Badge variant="outline" className="text-xs">
                            {node.type}
                          </Badge>
                          <div className="text-xs text-gray-500 ml-auto">
                            Score: {Math.round(node.score * 100)}%
                          </div>
                        </div>
                        
                        {node.snippet && (
                          <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                            {node.snippet}
                          </p>
                        )}
                        
                        <div className="flex items-center gap-2">
                          {node.labels.filter(l => l !== node.type).slice(0, 3).map(label => (
                            <Badge key={label} variant="secondary" className="text-xs">
                              {label}
                            </Badge>
                          ))}
                          <ArrowRight className="w-3 h-3 text-gray-400 ml-auto" />
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}

                {/* Relationship Results */}
                {searchResults.relationships.map((rel) => (
                  <Card key={rel.id} className="p-3 bg-blue-50">
                    <div className="flex items-center gap-2">
                      <Link2 className="w-4 h-4 text-blue-600" />
                      <span className="font-medium text-sm">{rel.type}</span>
                      <div className="text-xs text-gray-500 ml-auto">
                        Score: {Math.round(rel.score * 100)}%
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-2 text-sm text-gray-600">
                      <span className="truncate">{rel.start_node.name || 'Unknown'}</span>
                      <ArrowRight className="w-3 h-3" />
                      <span className="truncate">{rel.end_node.name || 'Unknown'}</span>
                    </div>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </div>
      )}
    </div>
  )
}

export default GraphSearch