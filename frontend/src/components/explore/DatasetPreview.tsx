'use client'

import React, { useState, useEffect } from 'react'
import { api, Dataset, Embedding } from '@/lib/api'
import { AlertCircle, Loader, Trash2, Download } from 'lucide-react'
import DataTable from '@/components/visualization/DataTable'
import SchemaViewer from '@/components/explore/SchemaViewer'
import EmbeddingsViewer from '@/components/explore/EmbeddingsViewer'

interface DatasetPreviewProps {
  dataset: Dataset
  onRefresh: () => void
}

type TabType = 'schema' | 'preview' | 'embeddings'

export default function DatasetPreview({ dataset, onRefresh }: DatasetPreviewProps) {
  const [activeTab, setActiveTab] = useState<TabType>('schema')
  const [embeddings, setEmbeddings] = useState<Embedding[]>([])
  const [loadingEmbeddings, setLoadingEmbeddings] = useState(false)
  const [embeddingsError, setEmbeddingsError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (activeTab === 'embeddings') {
      loadEmbeddings()
    }
  }, [activeTab])

  const loadEmbeddings = async () => {
    try {
      setLoadingEmbeddings(true)
      setEmbeddingsError(null)
      const result = await api.getEmbeddings(dataset.id)
      setEmbeddings(result.embeddings)
    } catch (err: any) {
      setEmbeddingsError(err.message || 'Failed to load embeddings')
    } finally {
      setLoadingEmbeddings(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete "${dataset.name}"? This cannot be undone.`)) {
      return
    }

    try {
      setDeleting(true)
      await api.deleteDataset(dataset.id)
      onRefresh()
    } catch (err: any) {
      alert(`Failed to delete dataset: ${err.message}`)
      setDeleting(false)
    }
  }

  const tabs: Array<{ id: TabType; label: string; count?: number }> = [
    { id: 'schema', label: 'Schema', count: dataset.column_count || 0 },
    { id: 'preview', label: 'Preview' },
    { id: 'embeddings', label: 'Embeddings', count: embeddings.length },
  ]

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold text-text-primary mb-1">{dataset.name}</h2>
          <p className="text-sm text-text-tertiary">{dataset.table_name}</p>
        </div>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="btn btn-secondary flex items-center gap-2"
        >
          <Trash2 className="w-4 h-4" />
          {deleting ? 'Deleting...' : 'Delete'}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        <div className="p-3 bg-bg-secondary rounded-lg">
          <p className="text-xs text-text-tertiary mb-1">Rows</p>
          <p className="text-lg font-semibold text-text-primary">
            {dataset.row_count?.toLocaleString() || '—'}
          </p>
        </div>
        <div className="p-3 bg-bg-secondary rounded-lg">
          <p className="text-xs text-text-tertiary mb-1">Columns</p>
          <p className="text-lg font-semibold text-text-primary">{dataset.column_count || '—'}</p>
        </div>
        <div className="p-3 bg-bg-secondary rounded-lg">
          <p className="text-xs text-text-tertiary mb-1">Quality</p>
          <p className="text-lg font-semibold text-accent-blue">
            {dataset.data_quality_score?.toFixed(1) || '—'}%
          </p>
        </div>
        <div className="p-3 bg-bg-secondary rounded-lg">
          <p className="text-xs text-text-tertiary mb-1">Status</p>
          <p className="text-lg font-semibold text-accent-green capitalize">{dataset.etl_status}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border-light flex gap-0">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-accent-blue text-accent-blue'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span className="ml-2 text-xs bg-bg-secondary rounded-full px-2 py-0.5">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-bg-primary rounded-lg border border-border-light p-4">
        {/* Schema Tab */}
        {activeTab === 'schema' && <SchemaViewer datasetId={dataset.id} />}

        {/* Preview Tab */}
        {activeTab === 'preview' && (
          <div className="space-y-4">
            <p className="text-sm text-text-secondary">Data preview showing first 10 rows</p>
            <DataTableWrapper datasetId={dataset.id} />
          </div>
        )}

        {/* Embeddings Tab */}
        {activeTab === 'embeddings' && (
          <>
            {loadingEmbeddings ? (
              <div className="flex items-center justify-center py-8">
                <Loader className="w-6 h-6 text-accent-blue animate-spin" />
              </div>
            ) : embeddingsError ? (
              <div className="p-4 bg-accent-red/10 border border-accent-red/20 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" />
                <p className="text-sm text-accent-red">{embeddingsError}</p>
              </div>
            ) : embeddings.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-text-tertiary">No embeddings created yet</p>
              </div>
            ) : (
              <EmbeddingsViewer embeddings={embeddings} />
            )}
          </>
        )}
      </div>
    </div>
  )
}

// Helper component to load and display data preview
function DataTableWrapper({ datasetId }: { datasetId: string }) {
  const [data, setData] = useState<{ columns: string[]; rows: any[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [datasetId])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.getDatasetPreview(datasetId)
      setData(result)
    } catch (err: any) {
      setError(err.message || 'Failed to load data preview')
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

  if (!data || data.rows.length === 0) {
    return <p className="text-text-tertiary">No data to display</p>
  }

  return <DataTable columns={data.columns} rows={data.rows} rowCount={data.rows.length} />
}
