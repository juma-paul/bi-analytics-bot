/**
 * Global state management using Zustand
 * Handles: datasets, current dataset, chat history, UI state
 */

import { create } from 'zustand'
import { Dataset, QueryResponse } from '@/lib/api'

export interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  query?: QueryResponse
  timestamp: Date
}

export interface AppState {
  // Datasets
  datasets: Dataset[]
  currentDatasetId: string | null
  currentDataset: Dataset | null
  isLoadingDatasets: boolean

  // Chat
  messages: Message[]
  isLoadingQuery: boolean
  error: string | null

  // UI
  sidebarOpen: boolean
  showDataExplorer: boolean

  // Actions
  setDatasets: (datasets: Dataset[]) => void
  setCurrentDataset: (datasetId: string, dataset: Dataset) => void
  addMessage: (message: Message) => void
  clearMessages: () => void
  setIsLoadingQuery: (loading: boolean) => void
  setError: (error: string | null) => void
  toggleSidebar: () => void
  toggleDataExplorer: () => void
  setIsLoadingDatasets: (loading: boolean) => void
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  datasets: [],
  currentDatasetId: null,
  currentDataset: null,
  isLoadingDatasets: false,
  messages: [],
  isLoadingQuery: false,
  error: null,
  sidebarOpen: true,
  showDataExplorer: false,

  // Actions
  setDatasets: (datasets) => set({ datasets }),
  setCurrentDataset: (datasetId, dataset) =>
    set({ currentDatasetId: datasetId, currentDataset: dataset }),
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  clearMessages: () => set({ messages: [] }),
  setIsLoadingQuery: (loading) => set({ isLoadingQuery: loading }),
  setError: (error) => set({ error }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleDataExplorer: () =>
    set((state) => ({
      showDataExplorer: !state.showDataExplorer,
    })),
  setIsLoadingDatasets: (loading) => set({ isLoadingDatasets: loading }),
}))
