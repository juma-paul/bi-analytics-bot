'use client'

import React, { useState } from 'react'
import { QueryResponse } from '@/lib/api'
import { ChevronDown, Code } from 'lucide-react'
import DataTable from '@/components/visualization/DataTable'
import ChartRenderer from '@/components/visualization/ChartRenderer'

interface QueryResultsProps {
  query: QueryResponse
}

export default function QueryResults({ query }: QueryResultsProps) {
  const [showSQL, setShowSQL] = useState(false)
  const [showDetails, setShowDetails] = useState(true)

  return (
    <div className="mt-6 space-y-4">
      {/* SQL Query */}
      <div className="bg-black/5 rounded-lg p-4 space-y-2">
        <button
          onClick={() => setShowSQL(!showSQL)}
          className="flex items-center gap-2 text-sm font-medium text-text-primary hover:text-accent-blue transition-colors"
        >
          <Code className="w-4 h-4" />
          Generated SQL
          <ChevronDown className={`w-4 h-4 transition-transform ${showSQL ? 'rotate-180' : ''}`} />
        </button>

        {showSQL && (
          <div className="bg-white rounded p-3 font-mono text-xs text-text-secondary overflow-x-auto">
            <pre>{query.generated_sql}</pre>
          </div>
        )}

        {query.sql_explanation && (
          <p className="text-xs text-text-secondary italic">{query.sql_explanation}</p>
        )}
      </div>

      {/* Visualization */}
      {query.visualization && (
        <div className="bg-bg-primary border border-border-light rounded-lg p-4">
          <ChartRenderer visualization={query.visualization} data={query.results} />
        </div>
      )}

      {/* Data Table */}
      <div className="bg-bg-primary border border-border-light rounded-lg p-4">
        <DataTable
          columns={query.results.columns}
          rows={query.results.rows}
          rowCount={query.results.row_count}
        />
      </div>

      {/* Insights */}
      {query.insights.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-text-primary">Key Insights</h4>
          <div className="space-y-2">
            {query.insights.map((insight, idx) => (
              <div key={idx} className="p-3 bg-accent-blue/10 border border-accent-blue/20 rounded-lg">
                <p className="text-sm text-text-primary">{insight}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="text-xs text-text-tertiary space-y-1">
        <p>
          ⏱️ Execution time: {query.execution_time_ms}ms
          {query.cached && ' (cached)'}
        </p>
        <p>📊 Results: {query.results.row_count} rows × {query.results.columns.length} columns</p>
      </div>
    </div>
  )
}
