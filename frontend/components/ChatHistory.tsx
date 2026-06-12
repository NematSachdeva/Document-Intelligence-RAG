import React from 'react'
import { MessageCircle, Copy, Check } from 'lucide-react'

export interface ChatMessage {
  id: string
  type: 'question' | 'answer'
  content: string
  citations?: Array<{
    source_id: number
    page_number: number
    chunk_id: string
  }>
  timestamp: Date
}

interface ChatHistoryProps {
  messages: ChatMessage[]
  isLoading: boolean
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages, isLoading }) => {
  const [copiedId, setCopiedId] = React.useState<string | null>(null)

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="text-center py-8 text-gray-500">
        <MessageCircle className="mx-auto h-12 w-12 mb-3 text-gray-400" />
        <p>No messages yet. Ask a question to get started!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.type === 'question' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
              message.type === 'question'
                ? 'bg-blue-500 text-white rounded-br-none'
                : 'bg-gray-100 text-gray-900 rounded-bl-none'
            }`}
          >
            <p className="text-sm">{message.content}</p>
            {message.type === 'answer' && message.citations && message.citations.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-300">
                <p className="text-xs font-semibold text-gray-600 mb-1">Sources:</p>
                <div className="space-y-1">
                  {message.citations.map((citation, idx) => (
                    <p key={idx} className="text-xs text-gray-600">
                      • Source {citation.source_id} (Page {citation.page_number})
                    </p>
                  ))}
                </div>
              </div>
            )}
            {message.type === 'answer' && (
              <button
                onClick={() => copyToClipboard(message.content, message.id)}
                className="mt-2 text-xs opacity-70 hover:opacity-100 transition-opacity flex items-center gap-1"
              >
                {copiedId === message.id ? (
                  <>
                    <Check className="h-3 w-3" /> Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3" /> Copy
                  </>
                )}
              </button>
            )}
            <p className="text-xs opacity-70 mt-1">
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>
        </div>
      ))}
      {isLoading && (
        <div className="flex justify-start">
          <div className="bg-gray-100 text-gray-900 px-4 py-3 rounded-lg rounded-bl-none">
            <div className="flex space-x-2">
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
