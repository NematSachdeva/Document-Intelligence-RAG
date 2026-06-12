import React, { useState, useEffect } from 'react'
import { FileText, AlertCircle, Trash2 } from 'lucide-react'
import FileUpload from '../components/FileUpload'
import Summary from '../components/Summary'
import ChatInterface from '../components/ChatInterface'
import { DocumentList } from '../components/DocumentList'
import { ChatHistory, ChatMessage } from '../components/ChatHistory'
import {
  uploadPDF,
  askQuestion,
  listDocuments,
  deleteDocument,
  healthCheck,
  UploadResponse,
  SummaryResponse,
  Citation,
  Document,
} from '../lib/api'

type AppState = 'upload' | 'chat'

export default function Home() {
  const [appState, setAppState] = useState<AppState>('upload')
  const [currentDocument, setCurrentDocument] = useState<UploadResponse | null>(null)
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [apiError, setApiError] = useState<string>('')

  // Check API health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await healthCheck()
        setApiError('')
        loadDocuments()
      } catch (err) {
        setApiError('Cannot connect to backend API. Make sure the server is running.')
      }
    }

    checkHealth()
  }, [])

  const loadDocuments = async () => {
    try {
      const response = await listDocuments()
      setDocuments(response.documents)
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  const handleFileUpload = async (file: File) => {
    setIsLoading(true)
    setError('')

    try {
      const response = await uploadPDF(file)

      if (response.success) {
        setCurrentDocument(response)
        setSelectedDocumentId(response.document_id)
        setSummary(response.summary)
        setChatHistory([])
        setAppState('chat')
        await loadDocuments()
      } else {
        setError('Failed to upload PDF')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error uploading PDF. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectDocument = (documentId: string) => {
    setSelectedDocumentId(documentId)
    setCurrentDocument(null)
    setSummary(null)
    setChatHistory([])
    setAppState('chat')
  }

  const handleAskQuestion = async (question: string): Promise<{ answer: string; citations: Citation[] }> => {
    if (!selectedDocumentId) {
      throw new Error('No document selected')
    }

    try {
      const response = await askQuestion(selectedDocumentId, question)

      if (response.success) {
        // Add to chat history
        const messageId = Math.random().toString(36).substr(2, 9)
        setChatHistory((prev) => [
          ...prev,
          {
            id: messageId + '_q',
            type: 'question',
            content: question,
            timestamp: new Date(),
          },
          {
            id: messageId + '_a',
            type: 'answer',
            content: response.answer,
            citations: response.citations,
            timestamp: new Date(),
          },
        ])

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

  const handleDeleteDocument = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    setIsLoading(true)

    try {
      await deleteDocument(documentId)
      if (selectedDocumentId === documentId) {
        setCurrentDocument(null)
        setSummary(null)
        setChatHistory([])
        setSelectedDocumentId(null)
        setAppState('upload')
      }
      await loadDocuments()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error deleting document')
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewDocument = () => {
    setCurrentDocument(null)
    setSummary(null)
    setChatHistory([])
    setSelectedDocumentId(null)
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
            {selectedDocumentId && currentDocument && (
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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Upload Area */}
            <div className="lg:col-span-2">
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

            {/* Documents Sidebar */}
            <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200 h-fit">
              <DocumentList
                documents={documents}
                selectedDocument={selectedDocumentId}
                onSelectDocument={handleSelectDocument}
                onDeleteDocument={handleDeleteDocument}
                isLoading={isLoading}
              />
            </div>
          </div>
        ) : (
          // Chat State
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Documents Sidebar */}
            <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200 h-fit lg:sticky lg:top-4">
              <DocumentList
                documents={documents}
                selectedDocument={selectedDocumentId}
                onSelectDocument={handleSelectDocument}
                onDeleteDocument={handleDeleteDocument}
                isLoading={isLoading}
              />
            </div>

            {/* Main Chat Area */}
            <div className="lg:col-span-3 space-y-6">
              {/* Chat History */}
              <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200 min-h-96 max-h-96 overflow-y-auto">
                <ChatHistory messages={chatHistory} isLoading={isLoading} />
              </div>

              {/* Chat Input */}
              <ChatInterface
                onSendMessage={handleAskQuestion}
                isLoading={isLoading}
                error={error}
              />

              {/* Summary and Info */}
              <div className="grid grid-cols-1 gap-6">
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
                    onClick={() => selectedDocumentId && handleDeleteDocument(selectedDocumentId)}
                    disabled={isLoading || !selectedDocumentId}
                    className="w-full px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete Document
                  </button>
                </div>
              </div>
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
