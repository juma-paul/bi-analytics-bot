'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { AlertCircle, Loader } from 'lucide-react'

interface ColumnInfo {
  column_name: string
  data_type: string
  nullable: boolean
  unique_count?: number
  null_count?: number
  sample_values?: string[]
}

interface SchemaViewerProps {
  datasetId: string
}

export default function SchemaViewer({ datasetId }: SchemaViewerProps) {
  const [columns, setColumns] = useState<ColumnInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedColumn, setExpandedColumn] = useState<string | null>(null)

  useEffect(() => {
    loadSchema()
  }, [datasetId])

  const loadSchema = async () => {
    try {
      setLoading(true)
      setError(null)
      const schema = await api.getDatasetSchema(datasetId)
      setColumns(schema.columns)
    } catch (err: any) {
      setError(err.message || 'Failed to load schema')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader className="w-6 h-6 text-accent-blue animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-accent-red/10 border border-accent-red/20 rounded-lg flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" />
        <p className="text-sm text-accent-red">{error}</p>
      </div>
    )
  }

  if (columns.length === 0) {
    return <p className="text-text-tertiary">No columns found</p>
  }

  return (
    <div className="space-y-2">
      {columns.map((column) => (
        <div
          key={column.column_name}
          className="border border-border-light rounded-lg overflow-hidden"
        >
          <button
            onClick={() =>
              setExpandedColumn(
                expandedColumn === column.column_name ? null : column.column_name
              )
            }
            className="w-full flex items-center justify-between p-4 bg-bg-secondary hover:bg-bg-tertiary transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-accent-blue" />
              <div className="text-left">
                <p className="font-medium text-text-primary">{column.column_name}</p>
                <p className="text-xs text-text-tertiary">{column.data_type}</p>
              </div>
            </div>
            <span
              className={`text-xs px-2 py-1 rounded ${
                column.nullable
                  ? 'bg-accent-orange/10 text-accent-orange'
                  : 'bg-accent-green/10 text-accent-green'
              }`}
            >
              {column.nullable ? 'Nullable' : 'Required'}
            </span>
          </button>

          {expandedColumn === column.column_name && (
            <div className="p-4 bg-bg-primary border-t border-border-light space-y-3">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-text-tertiary mb-1">Type</p>
                  <p className="text-sm font-medium text-text-primary">{column.data_type}</p>
                </div>
                <div>
                  <p className="text-xs text-text-tertiary mb-1">Nullability</p>
                  <p className="text-sm font-medium text-text-primary">
                    {column.nullable ? 'Nullable' : 'Not Null'}
                  </p>
                </div>
                {column.unique_count !== undefined && (
                  <div>
                    <p className="text-xs text-text-tertiary mb-1">Unique Values</p>
                    <p className="text-sm font-medium text-text-primary">{column.unique_count}</p>
                  </div>
                )}
                {column.null_count !== undefined && (
                  <div>
                    <p className="text-xs text-text-tertiary mb-1">Null Count</p>
                    <p className="text-sm font-medium text-text-primary">{column.null_count}</p>
                  </div>
                )}
              </div>

              {/* Sample Values */}
              {column.sample_values && column.sample_values.length > 0 && (
                <div className="pt-3 border-t border-border-light">
                  <p className="text-xs text-text-tertiary mb-2">Sample Values</p>
                  <div className="space-y-1">
                    {column.sample_values.slice(0, 5).map((value, idx) => (
                      <div
                        key={idx}
                        className="px-2 py-1 bg-bg-secondary rounded text-xs text-text-secondary font-mono break-all"
                      >
                        {value || <span className="text-text-tertiary italic">null</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
