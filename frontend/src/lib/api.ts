/**
 * API Client - Handles all communication with FastAPI backend
 * Answers to your questions:
 * - Dataset switching: YES, use selectDataset()
 * - View existing data: YES, use listDatasets() and getDatasetSchema()
 * - Embeddings: YES, created during ETL via backend
 * - Matching: dataset_id foreign key links embeddings to dataset/tables
 */

import axios, { AxiosInstance, AxiosError } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Types
export interface Dataset {
  id: string
  name: string
  table_name: string
  row_count: number | null
  column_count: number | null
  original_row_count: number | null
  rows_removed: number | null
  data_quality_score: number | null
  etl_status: string
  created_at: string
  updated_at: string
}

export interface DatasetColumn {
  id: string
  dataset_id: string
  column_name: string
  data_type: string
  null_count: number
  null_percentage: number
  unique_count: number
  sample_values: string[]
  quality_issues: string[]
  transformations_applied: string[]
}

export interface Embedding {
  id: string
  dataset_id: string
  content: string
  embedding_type: 'schema' | 'context' | 'sample_query'
  embedding_metadata: Record<string, any>
  created_at: string
}

export interface ETLReport {
  dataset_id: string
  etl_status: string
  summary: {
    original_rows: number
    final_rows: number
    rows_removed: number
    columns: number
    data_quality_score: number
  }
  cleaning_report: Record<string, any>
  column_quality: Record<string, any>[]
  transformations: string[]
  execution_time_ms: number
}

export interface QueryRequest {
  dataset_id: string
  question: string
  session_id?: string
  include_explanation?: boolean
}

export interface QueryResponse {
  query_id: string
  question: string
  generated_sql: string
  sql_explanation?: string
  results: {
    columns: string[]
    rows: any[]
    row_count: number
  }
  visualization?: {
    type: string
    config: Record<string, any>
  }
  insights: string[]
  execution_time_ms: number
  cached: boolean
}

export interface UploadResponse {
  success: boolean
  dataset_id: string
  dataset: Dataset
  etl_report: ETLReport
}

// API Client Class
class APIClient {
  private client: AxiosInstance

  constructor(baseURL: string = API_URL) {
    this.client = axios.create({
      baseURL,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.message)
        return Promise.reject(error)
      }
    )
  }

  // Health check
  async health(): Promise<{ status: string; service: string }> {
    const response = await this.client.get('/health')
    return response.data
  }

  // === DATASET ENDPOINTS ===

  /**
   * Upload CSV file and run ETL pipeline
   * Creates dataset, runs validation, cleaning, transformation, profiling
   * Generates embeddings for RAG system
   */
  async uploadDataset(file: File, datasetName?: string): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (datasetName) formData.append('dataset_name', datasetName)

    const response = await this.client.post('/api/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  /**
   * List all datasets
   * Allows user to switch between datasets and avoid uploading duplicates
   */
  async listDatasets(): Promise<{ datasets: Dataset[]; total: number }> {
    const response = await this.client.get('/api/datasets')
    return response.data
  }

  /**
   * Get dataset details including columns and quality metrics
   * Shows data structure, types, quality scores
   */
  async getDataset(datasetId: string): Promise<Dataset> {
    const response = await this.client.get(`/api/datasets/${datasetId}`)
    return response.data.dataset
  }

  /**
   * Get dataset schema - column information
   * Shows all columns, data types, quality issues
   */
  async getDatasetSchema(datasetId: string): Promise<{ columns: DatasetColumn[] }> {
    const response = await this.client.get(`/api/datasets/${datasetId}/schema`)
    return response.data
  }

  /**
   * Get detailed quality report from ETL
   * Shows data quality metrics, transformations applied, issues found
   */
  async getQualityReport(datasetId: string): Promise<{ report: Record<string, any> }> {
    const response = await this.client.get(`/api/datasets/${datasetId}/quality-report`)
    return response.data
  }

  /**
   * Get ETL execution logs
   * Shows each stage: validation, cleaning, transformation, profiling, loading
   */
  async getETLLogs(datasetId: string): Promise<{ logs: Array<Record<string, any>> }> {
    const response = await this.client.get(`/api/datasets/${datasetId}/etl-logs`)
    return response.data
  }

  /**
   * Get data preview - first 10 rows of dataset
   * Used for data explorer to show sample data
   */
  async getDatasetPreview(
    datasetId: string,
    limit: number = 10
  ): Promise<{ columns: string[]; rows: any[] }> {
    const response = await this.client.get(`/api/datasets/${datasetId}/preview`, {
      params: { limit },
    })
    return response.data
  }

  /**
   * Delete dataset and all associated data
   * Removes: tables, embeddings, query cache, logs
   */
  async deleteDataset(datasetId: string): Promise<{ success: boolean }> {
    const response = await this.client.delete(`/api/datasets/${datasetId}`)
    return response.data
  }

  // === EMBEDDING ENDPOINTS ===

  /**
   * Get embeddings for a dataset
   * Returns vector embeddings created during ETL
   * Types: 'schema' (table structure), 'context' (business context), 'sample_query'
   * These enable RAG (semantic search) for better SQL generation
   */
  async getEmbeddings(datasetId: string): Promise<{ embeddings: Embedding[] }> {
    const response = await this.client.get(`/api/datasets/${datasetId}/embeddings`)
    return response.data
  }

  /**
   * Get embedding details
   * Shows: content, embedding_type, metadata
   * Used to understand what context was captured for RAG
   */
  async getEmbeddingDetails(embeddingId: string): Promise<Embedding> {
    const response = await this.client.get(`/api/embeddings/${embeddingId}`)
    return response.data
  }

  // === QUERY ENDPOINTS ===

  /**
   * Execute natural language query on dataset
   * 1. Retrieves embedding context via RAG
   * 2. Generates SQL using LLM
   * 3. Executes SQL (with caching)
   * 4. Recommends chart type
   * 5. Generates insights
   */
  async executeQuery(request: QueryRequest): Promise<QueryResponse> {
    const response = await this.client.post('/api/query', request)
    return response.data
  }

  /**
   * Get query history for a dataset
   * Shows previous queries to understand data exploration
   */
  async getQueryHistory(
    datasetId: string,
    limit: number = 50
  ): Promise<{ queries: Array<Record<string, any>> }> {
    const response = await this.client.get(`/api/query/history`, {
      params: { dataset_id: datasetId, limit },
    })
    return response.data
  }

  /**
   * Explain SQL query in natural language
   * Helps users understand generated SQL
   */
  async explainSQL(sql: string, datasetId: string): Promise<{ explanation: string }> {
    const response = await this.client.post(`/api/query/explain`, { sql, dataset_id: datasetId })
    return response.data
  }
}

// Export singleton instance
export const api = new APIClient()

export default api
