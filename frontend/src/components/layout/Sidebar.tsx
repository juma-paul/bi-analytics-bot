'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useAppStore } from '@/store/app'
import { api } from '@/lib/api'
import { Menu, X, Upload, Database, MessageSquare, Settings, Plus } from 'lucide-react'

export default function Sidebar() {
  const {
    sidebarOpen,
    toggleSidebar,
    datasets,
    setDatasets,
    currentDatasetId,
    setCurrentDataset,
    isLoadingDatasets,
    setIsLoadingDatasets,
  } = useAppStore()

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    setIsLoadingDatasets(true)
    try {
      const result = await api.listDatasets()
      setDatasets(result.datasets)

      // Auto-select first dataset if available and none selected
      if (result.datasets.length > 0 && !currentDatasetId) {
        setCurrentDataset(result.datasets[0].id, result.datasets[0])
      }
    } catch (error) {
      console.error('Failed to load datasets:', error)
    } finally {
      setIsLoadingDatasets(false)
    }
  }

  const handleSelectDataset = (datasetId: string) => {
    const dataset = datasets.find((d) => d.id === datasetId)
    if (dataset) {
      setCurrentDataset(datasetId, dataset)
    }
  }

  return (
    <>
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-bg-secondary border-r border-border-light transform transition-transform duration-300 lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-light">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent-blue flex items-center justify-center">
              <Database className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-text-primary">Analytics</h1>
              <p className="text-xs text-text-tertiary">AI BI Platform</p>
            </div>
          </div>
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-2 hover:bg-bg-hover rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          <Link href="/" onClick={() => sidebarOpen && toggleSidebar()}>
            <div className="flex items-center gap-3 px-4 py-3 rounded-lg text-text-primary hover:bg-bg-hover transition-colors cursor-pointer group">
              <MessageSquare className="w-5 h-5 text-accent-blue" />
              <span className="font-medium">Chat</span>
            </div>
          </Link>

          <Link href="/explore" onClick={() => sidebarOpen && toggleSidebar()}>
            <div className="flex items-center gap-3 px-4 py-3 rounded-lg text-text-primary hover:bg-bg-hover transition-colors cursor-pointer">
              <Database className="w-5 h-5 text-accent-blue" />
              <span className="font-medium">Data Explorer</span>
            </div>
          </Link>

          <Link href="/upload" onClick={() => sidebarOpen && toggleSidebar()}>
            <div className="flex items-center gap-3 px-4 py-3 rounded-lg text-text-primary hover:bg-bg-hover transition-colors cursor-pointer">
              <Upload className="w-5 h-5 text-accent-blue" />
              <span className="font-medium">Upload Dataset</span>
            </div>
          </Link>
        </nav>

        {/* Datasets Section */}
        <div className="px-4 py-6 border-t border-border-light">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary">Datasets</h2>
            <button className="p-1 hover:bg-bg-hover rounded transition-colors" title="Add dataset">
              <Plus className="w-4 h-4 text-accent-blue" />
            </button>
          </div>

          {isLoadingDatasets ? (
            <div className="flex items-center justify-center py-4">
              <div className="spinner"></div>
            </div>
          ) : datasets.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {datasets.map((dataset) => (
                <button
                  key={dataset.id}
                  onClick={() => handleSelectDataset(dataset.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-all duration-200 ${
                    currentDatasetId === dataset.id
                      ? 'bg-accent-blue text-white'
                      : 'bg-bg-primary text-text-primary hover:bg-bg-hover'
                  }`}
                >
                  <p className="text-sm font-medium truncate">{dataset.name}</p>
                  <p
                    className={`text-xs ${
                      currentDatasetId === dataset.id ? 'text-blue-100' : 'text-text-tertiary'
                    }`}
                  >
                    {dataset.row_count ? `${dataset.row_count.toLocaleString()} rows` : 'Loading...'}
                  </p>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <p className="text-sm text-text-tertiary mb-3">No datasets yet</p>
              <Link href="/upload">
                <button className="btn btn-primary btn-sm w-full">Upload Dataset</button>
              </Link>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border-light bg-bg-secondary">
          <Link href="/settings">
            <button className="w-full flex items-center gap-3 px-4 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors">
              <Settings className="w-5 h-5" />
              <span className="text-sm font-medium">Settings</span>
            </button>
          </Link>
        </div>
      </aside>

      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={toggleSidebar}
        ></div>
      )}
    </>
  )
}
