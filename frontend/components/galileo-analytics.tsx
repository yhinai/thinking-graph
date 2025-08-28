"use client"

import React, { useState, useEffect } from 'react'
import { Card } from './ui/card'
import { Badge } from './ui/badge'
import { apiService } from '@/lib/api'

interface AnalyticsData {
  total_interactions: number
  total_kg_updates: number
  avg_response_length: number
  avg_reasoning_length: number
  reasoning_quality: {
    avg_coherence: number
    avg_completeness: number
    avg_clarity: number
    avg_relevance: number
    avg_reasoning_steps: number
  }
  galileo_enabled: boolean
  run_name: string
  console_url?: string
}

interface MetricsData {
  response_time_trend: Array<{timestamp: string, value: number}>
  reasoning_quality_trend: Array<{
    timestamp: string
    coherence: number
    completeness: number
    clarity: number
    relevance: number
  }>
  total_interactions: number
  total_kg_updates: number
  galileo_enabled: boolean
}

export function GalileoAnalytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    loadAnalytics()
    const interval = setInterval(loadAnalytics, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadAnalytics = async () => {
    try {
      const [analyticsResponse, metricsResponse] = await Promise.all([
        apiService.getGalileoAnalytics(),
        apiService.getGalileoMetrics()
      ])

      if (analyticsResponse.success) {
        setAnalytics(analyticsResponse.analytics)
      }

      if (metricsResponse.success) {
        setMetrics(metricsResponse.metrics)
      }

      setLoading(false)
    } catch (error) {
      console.error('Failed to load Galileo analytics:', error)
      setLoading(false)
    }
  }

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-500'
    if (score >= 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const formatScore = (score: number) => {
    return (score * 100).toFixed(0) + '%'
  }

  if (loading) {
    return (
      <Card className="p-4 bg-white/5 backdrop-blur-sm border-white/10">
        <div className="animate-pulse">
          <div className="h-4 bg-white/20 rounded w-32 mb-2"></div>
          <div className="h-3 bg-white/10 rounded w-24"></div>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Main Analytics Card */}
      <Card className="p-4 bg-white/5 backdrop-blur-sm border-white/10">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            🔬 Galileo AI Analytics
            {analytics?.galileo_enabled ? (
              <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                Live
              </Badge>
            ) : (
              <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
                Local
              </Badge>
            )}
          </h3>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-white/60 hover:text-white/80 transition-colors"
          >
            {expanded ? '↑' : '↓'}
          </button>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-2xl font-bold text-blue-400">
              {analytics?.total_interactions || 0}
            </div>
            <div className="text-xs text-white/60">Interactions</div>
          </div>
          
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-400">
              {analytics?.total_kg_updates || 0}
            </div>
            <div className="text-xs text-white/60">KG Updates</div>
          </div>
          
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-2xl font-bold text-purple-400">
              {analytics?.avg_response_length?.toFixed(0) || 0}
            </div>
            <div className="text-xs text-white/60">Avg Response Length</div>
          </div>
          
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-2xl font-bold text-orange-400">
              {analytics?.avg_reasoning_length?.toFixed(0) || 0}
            </div>
            <div className="text-xs text-white/60">Avg Reasoning Length</div>
          </div>
        </div>

        {/* Reasoning Quality Scores */}
        {analytics?.reasoning_quality && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-white/80 mb-2">Reasoning Quality</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getQualityColor(analytics.reasoning_quality.avg_coherence)}`}></div>
                <span className="text-xs text-white/70">
                  Coherence: {formatScore(analytics.reasoning_quality.avg_coherence)}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getQualityColor(analytics.reasoning_quality.avg_completeness)}`}></div>
                <span className="text-xs text-white/70">
                  Completeness: {formatScore(analytics.reasoning_quality.avg_completeness)}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getQualityColor(analytics.reasoning_quality.avg_clarity)}`}></div>
                <span className="text-xs text-white/70">
                  Clarity: {formatScore(analytics.reasoning_quality.avg_clarity)}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getQualityColor(analytics.reasoning_quality.avg_relevance)}`}></div>
                <span className="text-xs text-white/70">
                  Relevance: {formatScore(analytics.reasoning_quality.avg_relevance)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Galileo Link */}
        {analytics?.console_url && analytics.galileo_enabled && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-white/60">View in Galileo:</span>
            <a 
              href={analytics.console_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 underline"
            >
              {analytics.run_name}
            </a>
          </div>
        )}
      </Card>

      {/* Expanded Metrics */}
      {expanded && metrics && (
        <Card className="p-4 bg-white/5 backdrop-blur-sm border-white/10">
          <h4 className="text-lg font-semibold text-white mb-4">📊 Detailed Metrics</h4>
          
          {/* Response Time Trend */}
          {metrics.response_time_trend.length > 0 && (
            <div className="mb-6">
              <h5 className="text-sm font-medium text-white/80 mb-2">Response Time Trend</h5>
              <div className="bg-white/5 rounded-lg p-3">
                <div className="flex items-end gap-1 h-16">
                  {metrics.response_time_trend.slice(-10).map((point, index) => (
                    <div
                      key={index}
                      className="bg-blue-400 rounded-t"
                      style={{
                        height: `${Math.min((point.value * 100), 100)}%`,
                        width: '8px'
                      }}
                      title={`${point.value.toFixed(2)}s at ${new Date(point.timestamp).toLocaleTimeString()}`}
                    />
                  ))}
                </div>
                <div className="text-xs text-white/60 mt-1">
                  Last 10 interactions (hover for details)
                </div>
              </div>
            </div>
          )}

          {/* Quality Trend */}
          {metrics.reasoning_quality_trend.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-white/80 mb-2">Reasoning Quality Trend</h5>
              <div className="bg-white/5 rounded-lg p-3">
                <div className="space-y-2">
                  {metrics.reasoning_quality_trend.slice(-5).map((point, index) => (
                    <div key={index} className="flex items-center gap-2 text-xs">
                      <span className="text-white/60 w-20">
                        {new Date(point.timestamp).toLocaleTimeString()}
                      </span>
                      <div className="flex-1 flex gap-1">
                        <div 
                          className="h-2 bg-green-400 rounded"
                          style={{ width: `${point.coherence * 50}px` }}
                          title={`Coherence: ${formatScore(point.coherence)}`}
                        />
                        <div 
                          className="h-2 bg-blue-400 rounded"
                          style={{ width: `${point.completeness * 50}px` }}
                          title={`Completeness: ${formatScore(point.completeness)}`}
                        />
                        <div 
                          className="h-2 bg-purple-400 rounded"
                          style={{ width: `${point.clarity * 50}px` }}
                          title={`Clarity: ${formatScore(point.clarity)}`}
                        />
                        <div 
                          className="h-2 bg-orange-400 rounded"
                          style={{ width: `${point.relevance * 50}px` }}
                          title={`Relevance: ${formatScore(point.relevance)}`}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-white/60 mt-2 flex gap-4">
                  <span><span className="inline-block w-2 h-2 bg-green-400 rounded mr-1"></span>Coherence</span>
                  <span><span className="inline-block w-2 h-2 bg-blue-400 rounded mr-1"></span>Completeness</span>
                  <span><span className="inline-block w-2 h-2 bg-purple-400 rounded mr-1"></span>Clarity</span>
                  <span><span className="inline-block w-2 h-2 bg-orange-400 rounded mr-1"></span>Relevance</span>
                </div>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
