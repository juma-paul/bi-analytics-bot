'use client'

import React, { useState } from 'react'
import { ChevronDown, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react'

interface ColumnQuality {
  column: string
  type: string
  nulls: string
  unique_values: number
  quality_score: number
  issues?: string[]
}

interface CleaningReport {
  duplicates_removed?: number
  nulls_filled?: Record<string, number>
  outliers_detected?: Record<string, number>
  [key: string]: any
}

interface ETLReport {
  dataset_id: string
  etl_status: string
  summary: {
    original_rows: number
    final_rows: number
    rows_removed: number
    columns: number
    data_quality_score: number
  }
  cleaning_report: CleaningReport
  column_quality: ColumnQuality[]
  transformations: string[]
  execution_time_ms: number
}

interface ETLReportViewProps {
  report: ETLReport
}

export default function ETLReportView({ report }: ETLReportViewProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    summary: true,
    cleaning: true,
    columns: false,
    transformations: false,
  })

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  const getQualityColor = (score: number) => {
    if (score >= 90) return 'text-accent-green'
    if (score >= 70) return 'text-accent-blue'
    if (score >= 50) return 'text-accent-orange'
    return 'text-accent-red'
  }

  const getQualityBgColor = (score: number) => {
    if (score >= 90) return 'bg-accent-green/10'
    if (score >= 70) return 'bg-accent-blue/10'
    if (score >= 50) return 'bg-accent-orange/10'
    return 'bg-accent-red/10'
  }

  return (
    <div className="space-y-4">
      {/* Quality Score Summary */}
      <div className="relative overflow-hidden rounded-lg bg-gradient-to-br from-bg-secondary to-bg-tertiary p-6 border border-border-light">
        <div className="absolute -right-12 -top-12 w-32 h-32 bg-accent-blue/5 rounded-full" />
        <div className="relative flex items-center justify-between">
          <div>
            <p className="text-sm text-text-tertiary mb-1">Overall Data Quality</p>
            <h3 className={`text-4xl font-bold ${getQualityColor(report.summary.data_quality_score)}`}>
              {report.summary.data_quality_score.toFixed(1)}%
            </h3>
          </div>
          <div className="text-right">
            <TrendingUp className={`w-12 h-12 ${getQualityColor(report.summary.data_quality_score)} mb-2`} />
            <p className="text-xs text-text-tertiary">
              {report.summary.final_rows.toLocaleString()} clean rows
            </p>
          </div>
        </div>
      </div>

      {/* Summary Section */}
      <div className="border border-border-light rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('summary')}
          className="w-full flex items-center justify-between p-4 bg-bg-secondary hover:bg-bg-tertiary transition-colors"
        >
          <h4 className="font-semibold text-text-primary">Data Summary</h4>
          <ChevronDown
            className={`w-4 h-4 text-text-tertiary transition-transform ${
              expandedSections.summary ? 'rotate-180' : ''
            }`}
          />
        </button>

        {expandedSections.summary && (
          <div className="p-4 space-y-3 bg-bg-primary">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-text-tertiary mb-1">Original Rows</p>
                <p className="text-lg font-semibold text-text-primary">
                  {report.summary.original_rows.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-1">Clean Rows</p>
                <p className="text-lg font-semibold text-text-primary">
                  {report.summary.final_rows.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-1">Rows Removed</p>
                <p className="text-lg font-semibold text-accent-orange">
                  {report.summary.rows_removed.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-1">Columns</p>
                <p className="text-lg font-semibold text-text-primary">
                  {report.summary.columns}
                </p>
              </div>
            </div>

            <div className="pt-2 border-t border-border-light">
              <p className="text-xs text-text-tertiary mb-2">Data Reduction</p>
              <div className="w-full bg-bg-secondary rounded-full h-2 overflow-hidden">
                <div
                  className="bg-accent-blue h-full transition-all"
                  style={{
                    width: `${((report.summary.rows_removed / report.summary.original_rows) * 100).toFixed(1)}%`,
                  }}
                />
              </div>
              <p className="text-xs text-text-tertiary mt-1">
                {(
                  (report.summary.rows_removed / report.summary.original_rows) *
                  100
                ).toFixed(1)}% of data was cleaned
              </p>
            </div>

            <div className="pt-2 border-t border-border-light">
              <p className="text-xs text-text-tertiary">
                ⏱️ Processed in {report.execution_time_ms}ms
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Cleaning Report Section */}
      <div className="border border-border-light rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('cleaning')}
          className="w-full flex items-center justify-between p-4 bg-bg-secondary hover:bg-bg-tertiary transition-colors"
        >
          <h4 className="font-semibold text-text-primary">Cleaning Operations</h4>
          <ChevronDown
            className={`w-4 h-4 text-text-tertiary transition-transform ${
              expandedSections.cleaning ? 'rotate-180' : ''
            }`}
          />
        </button>

        {expandedSections.cleaning && (
          <div className="p-4 space-y-3 bg-bg-primary">
            {report.cleaning_report.duplicates_removed !== undefined && (
              <div className="flex items-center justify-between p-3 bg-accent-orange/10 rounded-lg border border-accent-orange/20">
                <p className="text-sm text-text-primary">
                  {report.cleaning_report.duplicates_removed} duplicate rows removed
                </p>
                <CheckCircle className="w-4 h-4 text-accent-orange flex-shrink-0" />
              </div>
            )}

            {report.cleaning_report.nulls_filled &&
              Object.keys(report.cleaning_report.nulls_filled).length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-text-primary">Missing Values Handled</p>
                  {Object.entries(report.cleaning_report.nulls_filled).map(([column, count]) => (
                    <div
                      key={column}
                      className="p-2 bg-bg-secondary rounded flex justify-between items-center"
                    >
                      <p className="text-xs text-text-secondary">{column}</p>
                      <span className="text-xs font-medium text-accent-blue">{count} filled</span>
                    </div>
                  ))}
                </div>
              )}

            {report.cleaning_report.outliers_detected &&
              Object.keys(report.cleaning_report.outliers_detected).length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-text-primary">Outliers Detected</p>
                  {Object.entries(report.cleaning_report.outliers_detected).map(([column, count]) => (
                    <div
                      key={column}
                      className="p-2 bg-bg-secondary rounded flex justify-between items-center"
                    >
                      <p className="text-xs text-text-secondary">{column}</p>
                      <span className="text-xs font-medium text-accent-red">{count} detected</span>
                    </div>
                  ))}
                </div>
              )}

            {Object.keys(report.cleaning_report).length === 0 && (
              <p className="text-sm text-text-tertiary">No cleaning operations needed</p>
            )}
          </div>
        )}
      </div>

      {/* Column Quality Section */}
      <div className="border border-border-light rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('columns')}
          className="w-full flex items-center justify-between p-4 bg-bg-secondary hover:bg-bg-tertiary transition-colors"
        >
          <h4 className="font-semibold text-text-primary">Column Quality ({report.column_quality.length})</h4>
          <ChevronDown
            className={`w-4 h-4 text-text-tertiary transition-transform ${
              expandedSections.columns ? 'rotate-180' : ''
            }`}
          />
        </button>

        {expandedSections.columns && (
          <div className="p-4 space-y-3 bg-bg-primary">
            {report.column_quality.map((col, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border ${getQualityBgColor(col.quality_score)} border-border-light`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-medium text-text-primary">{col.column}</p>
                    <p className="text-xs text-text-tertiary">{col.type}</p>
                  </div>
                  <p className={`text-sm font-semibold ${getQualityColor(col.quality_score)}`}>
                    {col.quality_score}%
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 mb-2">
                  <div>
                    <p className="text-xs text-text-tertiary">Unique Values</p>
                    <p className="text-sm font-medium text-text-primary">{col.unique_values}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-tertiary">Missing</p>
                    <p className="text-sm font-medium text-text-primary">{col.nulls}</p>
                  </div>
                </div>

                {col.issues && col.issues.length > 0 && (
                  <div className="space-y-1">
                    {col.issues.map((issue, issueIdx) => (
                      <div key={issueIdx} className="flex gap-2 items-start">
                        <AlertCircle className="w-3 h-3 text-accent-orange flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-text-secondary">{issue}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Transformations Section */}
      <div className="border border-border-light rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('transformations')}
          className="w-full flex items-center justify-between p-4 bg-bg-secondary hover:bg-bg-tertiary transition-colors"
        >
          <h4 className="font-semibold text-text-primary">Transformations Applied</h4>
          <ChevronDown
            className={`w-4 h-4 text-text-tertiary transition-transform ${
              expandedSections.transformations ? 'rotate-180' : ''
            }`}
          />
        </button>

        {expandedSections.transformations && (
          <div className="p-4 space-y-2 bg-bg-primary">
            {report.transformations.length > 0 ? (
              report.transformations.map((transformation, idx) => (
                <div
                  key={idx}
                  className="flex gap-3 items-start p-3 bg-bg-secondary rounded-lg border border-border-light"
                >
                  <CheckCircle className="w-4 h-4 text-accent-green flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-text-secondary">{transformation}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-text-tertiary">No transformations applied</p>
            )}
          </div>
        )}
      </div>

      {/* Quality Recommendations */}
      {report.summary.data_quality_score < 80 && (
        <div className="p-4 bg-accent-blue/10 border border-accent-blue/20 rounded-lg flex gap-3">
          <AlertCircle className="w-5 h-5 text-accent-blue flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-accent-blue text-sm mb-1">Quality Improvement</p>
            <p className="text-xs text-text-secondary">
              Your data quality score is below 80%. Review the column quality and issues above to improve data
              consistency.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
