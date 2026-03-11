'use client'

import React from 'react'
import { Dataset } from '@/lib/api'
import { ChevronRight } from 'lucide-react'

interface DatasetCardProps {
  dataset: Dataset
  isSelected: boolean
  onSelect: (dataset: Dataset) => void
}

export default function DatasetCard({ dataset, isSelected, onSelect }: DatasetCardProps) {
  const getQualityColor = (score: number | null) => {
    if (!score) return 'bg-bg-secondary'
    if (score >= 90) return 'bg-accent-green/10'
    if (score >= 70) return 'bg-accent-blue/10'
    if (score >= 50) return 'bg-accent-orange/10'
    return 'bg-accent-red/10'
  }

  const getQualityTextColor = (score: number | null) => {
    if (!score) return 'text-text-secondary'
    if (score >= 90) return 'text-accent-green'
    if (score >= 70) return 'text-accent-blue'
    if (score >= 50) return 'text-accent-orange'
    return 'text-accent-red'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-accent-green/10 text-accent-green'
      case 'processing':
        return 'bg-accent-blue/10 text-accent-blue'
      case 'failed':
        return 'bg-accent-red/10 text-accent-red'
      default:
        return 'bg-bg-secondary text-text-secondary'
    }
  }

  return (
    <button
      onClick={() => onSelect(dataset)}
      className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
        isSelected
          ? 'border-accent-blue bg-accent-blue/5'
          : 'border-border-light bg-bg-secondary hover:border-border-light hover:bg-bg-tertiary'
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-text-primary truncate">{dataset.name}</h3>
          <p className="text-xs text-text-tertiary">{dataset.table_name}</p>
        </div>
        {isSelected && <ChevronRight className="w-5 h-5 text-accent-blue flex-shrink-0 ml-2" />}
      </div>

      <div className="space-y-2">
        {/* Quality Score */}
        {dataset.data_quality_score !== null && (
          <div className="flex items-center justify-between">
            <p className="text-xs text-text-tertiary">Quality</p>
            <p className={`text-xs font-semibold ${getQualityTextColor(dataset.data_quality_score)}`}>
              {dataset.data_quality_score.toFixed(1)}%
            </p>
          </div>
        )}

        {/* Row Count */}
        {dataset.row_count !== null && (
          <div className="flex items-center justify-between">
            <p className="text-xs text-text-tertiary">Rows</p>
            <p className="text-xs font-semibold text-text-primary">{dataset.row_count.toLocaleString()}</p>
          </div>
        )}

        {/* Column Count */}
        {dataset.column_count !== null && (
          <div className="flex items-center justify-between">
            <p className="text-xs text-text-tertiary">Columns</p>
            <p className="text-xs font-semibold text-text-primary">{dataset.column_count}</p>
          </div>
        )}

        {/* Status */}
        <div className="flex items-center justify-between pt-2 border-t border-border-light">
          <p className="text-xs text-text-tertiary">Status</p>
          <span className={`text-xs font-medium px-2 py-1 rounded capitalize ${getStatusColor(dataset.etl_status)}`}>
            {dataset.etl_status}
          </span>
        </div>
      </div>
    </button>
  )
}
