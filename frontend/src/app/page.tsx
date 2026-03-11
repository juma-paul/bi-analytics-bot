'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useAppStore } from '@/store/app'
import { api, QueryResponse } from '@/lib/api'
import { Send, AlertCircle } from 'lucide-react'
import ChatMessage from '@/components/chat/ChatMessage'
import QueryResults from '@/components/query/QueryResults'

export default function ChatPage() {
  const {
    currentDataset,
    messages,
    addMessage,
    clearMessages,
    isLoadingQuery,
    setIsLoadingQuery,
    error,
    setError,
  } = useAppStore()

  const [input, setInput] = useState('')
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim()) return
    if (!currentDataset) {
      setError('Please select a dataset first')
      return
    }

    // Add user message
    const userMessage = {
      id: `msg_${Date.now()}`,
      type: 'user' as const,
      content: input,
      timestamp: new Date(),
    }
    addMessage(userMessage)
    setInput('')
    setIsLoadingQuery(true)
    setError(null)

    try {
      const response = await api.executeQuery({
        dataset_id: currentDataset.id,
        question: input,
        session_id: sessionId,
        include_explanation: true,
      })

      // Add assistant message with results
      const assistantMessage = {
        id: `msg_${Date.now()}_response`,
        type: 'assistant' as const,
        content: `Found ${response.results.row_count} results in ${response.execution_time_ms}ms ${
          response.cached ? '(cached)' : ''
        }`,
        query: response,
        timestamp: new Date(),
      }
      addMessage(assistantMessage)
    } catch (err: any) {
      const errorMessage = {
        id: `msg_${Date.now()}_error`,
        type: 'assistant' as const,
        content: `Error: ${err.message || 'Failed to execute query'}`,
        timestamp: new Date(),
      }
      addMessage(errorMessage)
      setError(err.message)
    } finally {
      setIsLoadingQuery(false)
    }
  }

  if (!currentDataset) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-accent-orange mx-auto mb-4" />
          <h2 className="text-2xl font-semibold mb-2">No Dataset Selected</h2>
          <p className="text-text-secondary mb-6">
            Please select or upload a dataset to start asking questions
          </p>
          <a href="/upload">
            <button className="btn btn-primary">Upload Dataset</button>
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      {/* Header */}
      <div className="p-6 border-b border-border-light bg-bg-primary sticky top-0 z-10">
        <h1 className="text-2xl font-semibold text-text-primary mb-1">
          {currentDataset.name}
        </h1>
        <p className="text-sm text-text-secondary">
          {currentDataset.row_count?.toLocaleString()} rows • {currentDataset.column_count} columns •
          Quality: {(currentDataset.data_quality_score || 0).toFixed(1)}%
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center">
            <div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">Start Asking Questions</h2>
              <p className="text-text-secondary mb-6 max-w-sm">
                Ask natural language questions about your {currentDataset.name} dataset. The AI will
                generate SQL, execute it, and show results with visualizations.
              </p>
              <div className="grid grid-cols-1 gap-2 max-w-sm text-left">
                <p className="text-xs text-text-tertiary font-medium">Example questions:</p>
                <button
                  onClick={() => setInput('What are the top 10 entries?')}
                  className="p-3 rounded-lg bg-bg-secondary hover:bg-bg-tertiary transition-colors text-left text-sm text-text-primary"
                >
                  "What are the top 10 entries?"
                </button>
                <button
                  onClick={() => setInput('Show me summary statistics')}
                  className="p-3 rounded-lg bg-bg-secondary hover:bg-bg-tertiary transition-colors text-left text-sm text-text-primary"
                >
                  "Show me summary statistics"
                </button>
              </div>
            </div>
          </div>
        ) : (
          messages.map((message) => <ChatMessage key={message.id} message={message} />)
        )}

        {isLoadingQuery && (
          <div className="flex justify-center py-4">
            <div className="flex items-center gap-3 text-text-secondary">
              <div className="spinner"></div>
              <span className="text-sm">Processing your question...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mx-6 mb-4 p-4 bg-accent-red/10 border border-accent-red/20 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" />
          <p className="text-sm text-accent-red">{error}</p>
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-6 border-t border-border-light bg-bg-primary">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your data..."
            disabled={isLoadingQuery}
            className="input flex-1"
          />
          <button
            type="submit"
            disabled={isLoadingQuery || !input.trim()}
            className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  )
}
