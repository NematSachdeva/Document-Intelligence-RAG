import React, { useState, useEffect } from 'react'
import { FileText, Loader, AlertCircle, Trash2 } from 'lucide-react'
import FileUpload from '../components/FileUpload'
import Summary from '../components/Summary'
import ChatInterface from '../components/ChatInterface'
import {
  uploadPDF,
  askQuestion,
  getSummary,
  listDocuments,
  deleteDocument,
  healthCheck,
  UploadResponse,
  SummaryResponse,
  Citation,
} from '../lib/api'

type AppState = 'upload' | 'chat'

export default function Home() {
  const [appState, setAppState] = useState<AppState>('upload')
  const [currentDocument, setCurrentDocument] = useState<UploadResponse | null>(null)
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [apiError, setApiError] = useState<string>('')

  // Check API health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await healthCheck()
        setApiError('')
      } catch (err) {
        setApiError('Cannot connect to backend API. Make sure the server is running.')
      }
    }

    checkHealth()
  }, [])

  const handleFileUpload = async (file: File) => {
    setIsLoading(true)
    setError('')

    try {
      const response = await uploadPDF(file)

      if (response.success) {
        setCurrentDocument(response)
        setSummary(response.summary)
        setAppState('chat')
      } else {
        setError('Failed to upload PDF')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error uploading PDF. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAskQuestion = async (question: string): Promise<{ answer: string; citations: Citation[] }> => {
    if (!currentDocument) {
      throw new Error('No document loaded')
    }

    try {
      const response = await askQuestion(currentDocument.document_id, question)

      if (response.success) {
        return {
          answer: response.answer,
          citations: response.citations,
        }
      } else {
        throw new Error('Failed to get answer')
      }
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Error processing question')
    }
  }

  const handleDeleteDocument = async () => {
    if (!currentDocument) return

    if (!confirm('Are you sure you want to delete this document?')) return

    setIsLoading(true)

    try {
      await deleteDocument(currentDocument.document_id)
      setCurrentDocument(null)
      setSummary(null)
      setAppState('upload')
      setError('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error deleting document')
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewDocument = () => {
    setCurrentDocument(null)
    setSummary(null)
    setAppState('upload')
    setError('')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">PDF Assistant</h1>
            </div>
            {currentDocument && (
              <div className="text-sm text-gray-600">
                {currentDocument.filename} • {currentDocument.pages} pages
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* API Error Alert */}
        {apiError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-900">Backend Connection Error</p>
              <p className="text-sm text-red-700 mt-1">{apiError}</p>
            </div>
          </div>
        )}

        {appState === 'upload' ? (
          // Upload State
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Upload Your PDF</h2>
              <p className="text-gray-600 mb-8">
                Upload a PDF document to start asking questions and get AI-powered insights.
              </p>

              <FileUpload
                onFileSelect={handleFileUpload}
                isLoading={isLoading}
                error={error}
              />

              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">📄 Extract Text</h3>
                  <p className="text-sm text-gray-600">
                    Automatically extracts text from PDFs with OCR support for scanned documents.
                  </p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">🔍 Semantic Search</h3>
                  <p className="text-sm text-gray-600">
                    Uses AI embeddings to find relevant information in your documents.
                  </p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">💡 Smart Answers</h3>
                  <p className="text-sm text-gray-600">
                    Get accurate answers with citations showing exactly where information came from.
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Chat State
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Chat */}
            <div className="lg:col-span-2">
              <ChatInterface
                onSendMessage={handleAskQuestion}
                isLoading={isLoading}
                error={error}
              />
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Summary */}
              {summary && (
                <Summary
                  summary={summary.summary}
                  keyPoints={summary.key_points}
                  mainTopics={summary.main_topics}
                />
              )}

              {/* Actions */}
              <div className="bg-white rounded-lg p-6 border border-gray-200 space-y-3">
                <button
                  onClick={handleNewDocument}
                  disabled={isLoading}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  Upload New Document
                </button>
                <button
                  onClick={handleDeleteDocument}
                  disabled={isLoading}
                  className="w-full px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Document
                </button>
              </div>

              {/* Document Info */}
              {currentDocument && (
                <div className="bg-white rounded-lg p-6 border border-gray-200">
                  <h3 className="font-semibold text-gray-900 mb-4">Document Info</h3>
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-gray-600">Filename</p>
                      <p className="text-gray-900 font-medium">{currentDocument.filename}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Pages</p>
                      <p className="text-gray-900 font-medium">{currentDocument.pages}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Chunks</p>
                      <p className="text-gray-900 font-medium">{currentDocument.chunks}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-sm text-gray-600">
          <p>PDF Assistant • Powered by AI</p>
        </div>
      </footer>
    </div>
  )
}
