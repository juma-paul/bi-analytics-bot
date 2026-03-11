'use client'

import React, { useState, useEffect } from 'react'
import { api, Dataset } from '@/lib/api'
import { useAppStore } from '@/store/app'
import { AlertCircle, Loader } from 'lucide-react'
import DatasetCard from '@/components/explore/DatasetCard'
import DatasetPreview from '@/components/explore/DatasetPreview'

export default function ExplorePage() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { currentDataset } = useAppStore()

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.listDatasets()
      setDatasets(result.datasets)

      // Auto-select current dataset if available
      if (currentDataset) {
        setSelectedDataset(currentDataset)
      } else if (result.datasets.length > 0) {
        setSelectedDataset(result.datasets[0])
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load datasets')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-text-primary mb-2">Data Explorer</h1>
        <p className="text-text-secondary">
          View your uploaded datasets and explore their structure, quality, and statistics
        </p>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-accent-red/10 border border-accent-red/20 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" />
          <p className="text-sm text-accent-red">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader className="w-8 h-8 text-accent-blue animate-spin mx-auto mb-3" />
            <p className="text-text-secondary">Loading datasets...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && datasets.length === 0 && (
        <div className="text-center py-12 bg-bg-secondary rounded-lg border border-border-light">
          <h3 className="text-lg font-semibold text-text-primary mb-2">No datasets yet</h3>
          <p className="text-text-secondary mb-4">Start by uploading your first CSV file</p>
          <a href="/upload">
            <button className="btn btn-primary">Upload Dataset</button>
          </a>
        </div>
      )}

      {/* Main Content */}
      {!loading && datasets.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Datasets List */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-text-primary px-1">Datasets</h2>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {datasets.map((dataset) => (
                <DatasetCard
                  key={dataset.id}
                  dataset={dataset}
                  isSelected={selectedDataset?.id === dataset.id}
                  onSelect={setSelectedDataset}
                />
              ))}
            </div>
          </div>

          {/* Dataset Preview */}
          <div className="lg:col-span-2">
            {selectedDataset ? (
              <DatasetPreview dataset={selectedDataset} onRefresh={loadDatasets} />
            ) : (
              <div className="text-center py-12 bg-bg-secondary rounded-lg border border-border-light">
                <p className="text-text-tertiary">Select a dataset to view details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
