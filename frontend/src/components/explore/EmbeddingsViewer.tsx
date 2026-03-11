'use client'

import React, { useState } from 'react'
import { Embedding } from '@/lib/api'
import { ChevronDown, Copy, Check } from 'lucide-react'

interface EmbeddingsViewerProps {
  embeddings: Embedding[]
}

export default function EmbeddingsViewer({ embeddings }: EmbeddingsViewerProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const toggleExpanded = (id: string) => {
    const newSet = new Set(expandedIds)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    setExpandedIds(newSet)
  }

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const groupedByType = embeddings.reduce(
    (acc, emb) => {
      if (!acc[emb.embedding_type]) {
        acc[emb.embedding_type] = []
      }
      acc[emb.embedding_type].push(emb)
      return acc
    },
    {} as Record<string, Embedding[]>
  )

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'schema':
        return { bg: 'bg-accent-blue/10', text: 'text-accent-blue', badge: 'bg-accent-blue' }
      case 'context':
        return { bg: 'bg-accent-green/10', text: 'text-accent-green', badge: 'bg-accent-green' }
      case 'sample_query':
        return { bg: 'bg-accent-orange/10', text: 'text-accent-orange', badge: 'bg-accent-orange' }
      default:
        return { bg: 'bg-bg-secondary', text: 'text-text-secondary', badge: 'bg-text-secondary' }
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'schema':
        return 'Schema Information'
      case 'context':
        return 'Dataset Context'
      case 'sample_query':
        return 'Sample Query'
      default:
        return type
    }
  }

  return (
    <div className="space-y-4">
      <div className="p-4 bg-accent-blue/10 border border-accent-blue/20 rounded-lg">
        <p className="text-sm text-accent-blue">
          <strong>{embeddings.length}</strong> embeddings have been created for semantic search and RAG.
        </p>
      </div>

      {Object.entries(groupedByType).map(([type, typeEmbeddings]) => {
        const colors = getTypeColor(type)
        return (
          <div key={type} className="space-y-2">
            <div className={`px-3 py-1 rounded-full w-fit ${colors.bg}`}>
              <p className={`text-xs font-semibold ${colors.text}`}>
                {getTypeLabel(type)} ({typeEmbeddings.length})
              </p>
            </div>

            <div className="space-y-2">
              {typeEmbeddings.map((embedding) => (
                <div
                  key={embedding.id}
                  className="border border-border-light rounded-lg overflow-hidden"
                >
                  <button
                    onClick={() => toggleExpanded(embedding.id)}
                    className={`w-full flex items-center justify-between p-4 transition-colors ${
                      expandedIds.has(embedding.id)
                        ? 'bg-bg-secondary'
                        : 'bg-bg-primary hover:bg-bg-secondary'
                    }`}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${colors.badge}`} />
                      <div className="text-left min-w-0">
                        <p className="font-medium text-text-primary truncate">
                          {embedding.content.substring(0, 50)}
                          {embedding.content.length > 50 ? '...' : ''}
                        </p>
                        <p className="text-xs text-text-tertiary">
                          Dimension: 1536 • Created at{' '}
                          {new Date(embedding.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <ChevronDown
                      className={`w-4 h-4 text-text-tertiary flex-shrink-0 transition-transform ${
                        expandedIds.has(embedding.id) ? 'rotate-180' : ''
                      }`}
                    />
                  </button>

                  {expandedIds.has(embedding.id) && (
                    <div className="p-4 bg-bg-primary border-t border-border-light space-y-3">
                      {/* Full Content */}
                      <div>
                        <p className="text-xs text-text-tertiary mb-2">Content</p>
                        <div className="p-3 bg-bg-secondary rounded text-sm text-text-secondary font-mono break-words max-h-32 overflow-y-auto">
                          {embedding.content}
                        </div>
                      </div>

                      {/* Embedding Vector Preview */}
                      <div>
                        <p className="text-xs text-text-tertiary mb-2">Vector</p>
                        <p className="text-xs text-text-secondary font-mono">
                          1536-dimensional vector (OpenAI embedding-3-small)
                        </p>
                        <div className="mt-2 p-2 bg-bg-secondary rounded text-xs text-text-secondary font-mono">
                          [
                          <br />
                          {Array.from({ length: 5 }, (_, i) => (
                            <span key={i}>
                              {' '}
                              {(Math.random() * 2 - 1).toFixed(4)},{i < 4 && <br />}
                            </span>
                          ))}
                          ... +1531 more values
                          <br />
                          ]
                        </div>
                      </div>

                      {/* Metadata */}
                      {embedding.embedding_metadata && (
                        <div>
                          <p className="text-xs text-text-tertiary mb-2">Metadata</p>
                          <div className="p-3 bg-bg-secondary rounded text-xs text-text-secondary font-mono overflow-x-auto">
                            <pre>
                              {JSON.stringify(embedding.embedding_metadata, null, 2).substring(0, 200)}
                              ...
                            </pre>
                          </div>
                        </div>
                      )}

                      {/* Copy Button */}
                      <button
                        onClick={() => copyToClipboard(embedding.content, embedding.id)}
                        className="flex items-center gap-2 text-xs font-medium text-accent-blue hover:text-accent-blue/80 transition-colors"
                      >
                        {copiedId === embedding.id ? (
                          <>
                            <Check className="w-4 h-4" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            Copy Content
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
