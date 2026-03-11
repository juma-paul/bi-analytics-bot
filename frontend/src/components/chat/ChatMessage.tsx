'use client'

import React from 'react'
import { Message } from '@/store/app'
import { format } from 'date-fns'
import { Copy, Check } from 'lucide-react'
import { useState } from 'react'
import QueryResults from '@/components/query/QueryResults'

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.type === 'user'

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div
        className={`max-w-2xl ${
          isUser
            ? 'bg-accent-blue text-white rounded-3xl rounded-tr-lg'
            : 'bg-bg-secondary text-text-primary rounded-3xl rounded-tl-lg'
        } px-4 py-3`}
      >
        <p className="text-sm">{message.content}</p>
        <p
          className={`text-xs mt-2 ${
            isUser ? 'text-blue-100' : 'text-text-tertiary'
          }`}
        >
          {format(message.timestamp, 'HH:mm')}
        </p>

        {/* Query Results */}
        {message.query && <QueryResults query={message.query} />}
      </div>
    </div>
  )
}
