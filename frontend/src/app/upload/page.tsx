'use client'

import React, { useState, useRef } from 'react'
import { Upload, AlertCircle, CheckCircle } from 'lucide-react'
import { api, ETLReport } from '@/lib/api'
import { useAppStore } from '@/store/app'
import ETLReportView from '@/components/upload/ETLReportView'

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [datasetName, setDatasetName] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [etlReport, setEtlReport] = useState<ETLReport | null>(null)
  const [uploadedDatasetId, setUploadedDatasetId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { setDatasets, setCurrentDataset } = useAppStore()

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = e.dataTransfer.files
    if (droppedFiles.length > 0) {
      const f = droppedFiles[0]
      if (f.name.endsWith('.csv')) {
        setFile(f)
        setDatasetName(f.name.replace('.csv', ''))
      } else {
        setError('Only CSV files are supported')
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const f = e.target.files[0]
      setFile(f)
      setDatasetName(f.name.replace('.csv', ''))
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('No file selected')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const response = await api.uploadDataset(file, datasetName)

      setEtlReport(response.etl_report)
      setUploadedDatasetId(response.dataset_id)

      // Refresh datasets list
      const result = await api.listDatasets()
      setDatasets(result.datasets)
      setCurrentDataset(response.dataset_id, response.dataset)

      setFile(null)
      setDatasetName('')
    } catch (err: any) {
      setError(err.message || 'Failed to upload dataset')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-text-primary mb-2">Upload Dataset</h1>
        <p className="text-text-secondary">
          Upload a CSV file to start exploring and querying your data with AI
        </p>
      </div>

      {!etlReport ? (
        <>
          {/* File Upload */}
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200 ${
              isDragging
                ? 'border-accent-blue bg-accent-blue_light'
                : 'border-border-light hover:border-accent-blue hover:bg-bg-secondary'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
            />

            <Upload className="w-12 h-12 mx-auto mb-4 text-accent-blue" />
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              Drop your CSV file here
            </h3>
            <p className="text-text-secondary mb-4">or click to select from your computer</p>
            <p className="text-xs text-text-tertiary">
              Maximum file size: 50MB • Supported format: CSV
            </p>
          </div>

          {/* File Info */}
          {file && (
            <div className="card card-md">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Dataset Name
                  </label>
                  <input
                    type="text"
                    value={datasetName}
                    onChange={(e) => setDatasetName(e.target.value)}
                    className="input"
                    placeholder="e.g., Sales Data 2024"
                  />
                </div>

                <div className="p-4 bg-bg-secondary rounded-lg space-y-2">
                  <p className="text-sm font-medium text-text-primary">📄 {file.name}</p>
                  <p className="text-xs text-text-tertiary">
                    Size: {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setFile(null)
                      setDatasetName('')
                      setError(null)
                    }}
                    className="btn btn-secondary flex-1"
                    disabled={isUploading}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleUpload}
                    disabled={isUploading}
                    className="btn btn-primary flex-1"
                  >
                    {isUploading ? (
                      <>
                        <div className="spinner"></div>
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        Upload Dataset
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="p-4 bg-accent-red/10 border border-accent-red/20 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" />
              <p className="text-sm text-accent-red">{error}</p>
            </div>
          )}

          {/* Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { title: 'Smart Type Detection', desc: 'Automatically detects data types and formats' },
              { title: 'Data Cleaning', desc: 'Removes duplicates, handles missing values' },
              {
                title: 'Quality Scoring',
                desc: 'Generates data quality metrics and recommendations',
              },
              {
                title: 'Vector Embeddings',
                desc: 'Creates embeddings for semantic search and AI queries',
              },
            ].map((feature) => (
              <div key={feature.title} className="p-4 bg-bg-secondary rounded-lg">
                <h4 className="font-semibold text-text-primary text-sm mb-1">{feature.title}</h4>
                <p className="text-xs text-text-secondary">{feature.desc}</p>
              </div>
            ))}
          </div>
        </>
      ) : (
        <>
          {/* ETL Report */}
          <div className="flex items-center gap-3 p-4 bg-accent-green/10 border border-accent-green/20 rounded-lg">
            <CheckCircle className="w-5 h-5 text-accent-green flex-shrink-0" />
            <div>
              <p className="font-semibold text-accent-green">Dataset uploaded successfully!</p>
              <p className="text-sm text-text-secondary">Your data is ready for analysis</p>
            </div>
          </div>

          <ETLReportView report={etlReport} />

          {/* Continue Button */}
          <a href="/">
            <button className="btn btn-primary w-full">Start Asking Questions</button>
          </a>
        </>
      )}
    </div>
  )
}
