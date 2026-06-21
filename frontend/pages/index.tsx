import React, { useState, useEffect, useRef } from 'react'
import { FileText, Download, AlertCircle, MessageCircle, BarChart3, Send, RotateCcw, Loader } from 'lucide-react'
import FileUpload from '../components/FileUpload'
import MarkdownRenderer from '../components/MarkdownRenderer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../components/ui/accordion'
import { Badge } from '../components/ui/badge'
import { uploadPDF, askQuestion, listDocuments, healthCheck, UploadResponse, SummaryResponse, Citation, Document } from '../lib/api'

interface ChatMessage {
  id: string
  type: 'question' | 'answer' | 'error'
  content: string
  citations?: Citation[]
  timestamp: Date
}

interface AnalysisReport {
  dashboard: string
  snapshot: string
  coverage: string
  financial_limits: string
  waiting_periods: string
  exclusions: string
  claim_restrictions: string
  important_clauses: string
  recommendation: string
}

export default function Home() {
  const [currentDocument, setCurrentDocument] = useState<UploadResponse | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisReport | null>(null)
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [apiError, setApiError] = useState<string>('')
  const [activeTab, setActiveTab] = useState('overview')
  const [inputValue, setInputValue] = useState('')
  const [lastFailedQuestion, setLastFailedQuestion] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isAnswering, setIsAnswering] = useState(false)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        console.log('[Health Check] Starting...')
        const response = await healthCheck()
        console.log('[Health Check] Response:', response)
        setApiError('')
        loadDocuments()
      } catch (err) {
        console.log('[Health Check] Failed:', err)
        // Don't set persistent error here - only show error if API requests actually fail
        // This prevents false positives during startup
      }
    }
    
    // Small delay to allow backend to start
    const timer = setTimeout(checkHealth, 1000)
    return () => clearTimeout(timer)
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
    setIsGeneratingReport(true)

    try {
      const response = await uploadPDF(file)
      if (response.success) {
        setCurrentDocument(response)
        setSummary(response.summary)
        setAnalysis(response.analysis)
        setChatMessages([])
        setLastFailedQuestion(null)
        setActiveTab('overview')
        // Clear any API errors if upload succeeds
        setApiError('')
        await loadDocuments()
      } else {
        setError('Failed to upload PDF')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error uploading PDF. Please try again.')
      // Only set API error if it's a connection error
      if (err.message === 'Network Error' || err.code === 'ECONNREFUSED') {
        setApiError('Cannot connect to backend API. Make sure the server is running.')
      }
    } finally {
      setIsLoading(false)
      setIsGeneratingReport(false)
    }
  }

  const handleAskQuestion = async (question: string) => {
    if (!currentDocument) return

    // Clear previous error
    setError('')
    setLastFailedQuestion(null)

    // Show user question immediately
    const questionId = `q-${Date.now()}`
    setChatMessages((prev) => [
      ...prev,
      {
        id: questionId,
        type: 'question',
        content: question,
        timestamp: new Date()
      }
    ])

    setIsAnswering(true)

    try {
      const response = await askQuestion(currentDocument.document_id, question)
      
      if (response.success) {
        // Add assistant response to chat
        setChatMessages((prev) => [
          ...prev,
          {
            id: `a-${Date.now()}`,
            type: 'answer',
            content: response.answer,
            citations: response.citations,
            timestamp: new Date()
          }
        ])
      } else {
        // Add error message to chat
        setChatMessages((prev) => [
          ...prev,
          {
            id: `e-${Date.now()}`,
            type: 'error',
            content: 'Failed to get an answer. Please try again.',
            timestamp: new Date()
          }
        ])
        setLastFailedQuestion(question)
        setError('API Error: Failed to process question')
      }
    } catch (err: any) {
      // Add error message to chat
      const errorMessage = err.response?.data?.detail || 'Error processing question. Please try again.'
      setChatMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          type: 'error',
          content: errorMessage,
          timestamp: new Date()
        }
      ])
      setLastFailedQuestion(question)
      setError(`API Error: ${errorMessage}`)
    } finally {
      setIsAnswering(false)
      setInputValue('')
    }
  }

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const handleGenerateReport = async () => {
    if (!currentDocument) return

    setIsLoading(true)
    try {
      // Get the analysis PDF from backend (already generated and cached during upload)
      const response = await fetch('http://localhost:8000/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: currentDocument.document_id })
      })

      if (response.ok) {
        const blob = await response.blob()
        
        // Download the PDF
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${currentDocument.filename.replace('.pdf', '')}_Analysis_Report.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } else {
        const errorData = await response.json().catch(() => ({}))
        setError(errorData.detail || 'Failed to generate report')
      }
    } catch (err: any) {
      console.error('Report generation error:', err)
      setError('Error generating report: ' + (err.message || 'Unknown error'))
    } finally {
      setIsLoading(false)
    }
  }

  // Landing Page
  if (!currentDocument) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <div className="flex justify-center mb-6">
              <div className="rounded-full bg-blue-600 p-4">
                <FileText className="h-12 w-12 text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold text-white mb-4">Insurance Document Intelligence</h1>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Upload your insurance policy PDF to get instant AI-powered analysis, interactive Q&A, and comprehensive insights
            </p>
          </div>

          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl mx-auto mb-12">
            <FileUpload onFileSelect={handleFileUpload} isLoading={isLoading} error={error} />
          </div>

          {documents.length > 0 && (
            <div className="max-w-4xl mx-auto">
              <h2 className="text-white text-2xl font-bold mb-6">Recent Documents</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {documents.map((doc) => (
                  <div key={doc.document_id} className="bg-slate-800 rounded-lg p-4 hover:bg-slate-700 transition cursor-pointer"
                    onClick={() => {
                      setCurrentDocument({
                        document_id: doc.document_id,
                        filename: doc.filename,
                        pages: doc.pages,
                        chunks: doc.chunks,
                        summary: {
                          summary: '',
                          key_points: [],
                          main_topics: [],
                          success: false
                        },
                        analysis: {
                          dashboard: '',
                          snapshot: '',
                          coverage: '',
                          financial_limits: '',
                          waiting_periods: '',
                          exclusions: '',
                          claim_restrictions: '',
                          important_clauses: '',
                          recommendation: ''
                        },
                        success: true
                      })
                      setActiveTab('overview')
                    }}>
                    <p className="text-white font-semibold flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      {doc.filename}
                    </p>
                    <p className="text-slate-400 text-sm mt-2">{doc.pages} pages • {doc.chunks} chunks</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Dashboard
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-600 p-2">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Insurance Analysis Platform</h1>
                <p className="text-sm text-slate-500">{currentDocument.filename}</p>
              </div>
            </div>
            <button
              onClick={() => setCurrentDocument(null)}
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition font-medium"
            >
              Upload New
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {apiError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-900">Backend Connection Error</p>
              <p className="text-sm text-red-700 mt-1">{apiError}</p>
            </div>
            <button
              onClick={() => setApiError('')}
              className="text-red-600 hover:text-red-800 font-medium text-sm"
            >
              Dismiss
            </button>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">{error}</p>
          </div>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-3 mb-6">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageCircle className="h-4 w-4" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="report" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Report
            </TabsTrigger>
          </TabsList>

          {/* OVERVIEW TAB */}
          <TabsContent value="overview" className="space-y-6">
            {/* Policy Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">Pages</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-slate-900">{currentDocument.pages}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">Chunks</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-slate-900">{currentDocument.chunks}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge variant="default">Active</Badge>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-600">Format</CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge variant="secondary">PDF</Badge>
                </CardContent>
              </Card>
            </div>

            {/* Summary Section */}
            {summary && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <Card>
                    <CardHeader>
                      <CardTitle>Policy Summary</CardTitle>
                      <CardDescription>AI-generated overview of your policy</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-700 leading-relaxed">{summary.summary}</p>
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Key Points</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {summary.key_points && summary.key_points.slice(0, 5).map((point: string, i: number) => (
                        <li key={i} className="flex gap-2 text-sm">
                          <span className="text-blue-600 font-bold flex-shrink-0">✓</span>
                          <span className="text-slate-700">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Main Topics */}
            {summary && (
              <Card>
                <CardHeader>
                  <CardTitle>Coverage Topics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {summary.main_topics && summary.main_topics.map((topic: string, i: number) => (
                      <Badge key={i} variant="outline">{topic}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* CHAT TAB */}
          <TabsContent value="chat" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Interactive Q&A</CardTitle>
                <CardDescription>Ask questions about your insurance policy</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Chat Messages Container */}
                <div className="bg-slate-50 rounded-lg border border-slate-200 p-4 min-h-96 max-h-96 overflow-y-auto space-y-4">
                  {chatMessages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500">
                      <MessageCircle className="h-12 w-12 mb-2 opacity-30" />
                      <p>No questions asked yet</p>
                      <p className="text-sm">Start by asking a question about the policy</p>
                    </div>
                  ) : (
                    <>
                      {chatMessages.map((msg: ChatMessage) => (
                        <div key={msg.id} className={`flex ${msg.type === 'question' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-xs px-4 py-2 rounded-lg ${
                            msg.type === 'question'
                              ? 'bg-blue-600 text-white rounded-br-none'
                              : msg.type === 'answer'
                              ? 'bg-white border border-slate-200 text-slate-900 rounded-bl-none'
                              : 'bg-red-50 border border-red-200 text-red-900 rounded-bl-none'
                          }`}>
                            <p className="text-sm">{msg.content}</p>
                            {msg.type === 'answer' && msg.citations && msg.citations.length > 0 && (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {msg.citations.map((c: Citation, j: number) => (
                                  <Badge key={j} variant="secondary" className="text-xs cursor-pointer hover:bg-slate-300">
                                    {c.page_number ? `Page ${c.page_number}` : 'Source'}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {isAnswering && (
                        <div className="flex justify-start">
                          <div className="max-w-xs px-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-900 rounded-bl-none flex items-center gap-2">
                            <Loader className="h-4 w-4 animate-spin text-blue-600" />
                            <p className="text-sm">Generating answer...</p>
                          </div>
                        </div>
                      )}
                      <div ref={messagesEndRef} />
                    </>
                  )}
                </div>

                {/* Chat Input */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && inputValue.trim() && !isAnswering) {
                        handleAskQuestion(inputValue)
                      }
                    }}
                    placeholder="Ask a question about the policy..."
                    disabled={isAnswering}
                    className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100"
                  />
                  <button
                    onClick={() => {
                      if (inputValue.trim()) {
                        handleAskQuestion(inputValue)
                      }
                    }}
                    disabled={isAnswering || !inputValue.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-400 transition flex items-center gap-2 font-medium"
                  >
                    <Send className="h-4 w-4" />
                    Send
                  </button>
                </div>

                {/* Retry Button - Show only if there was a failed question */}
                {lastFailedQuestion && (
                  <button
                    onClick={() => handleAskQuestion(lastFailedQuestion)}
                    disabled={isAnswering}
                    className="w-full px-4 py-2 border border-yellow-300 bg-yellow-50 text-yellow-900 rounded-lg hover:bg-yellow-100 transition font-medium flex items-center justify-center gap-2"
                  >
                    <RotateCcw className="h-4 w-4" />
                    Retry: "{lastFailedQuestion}"
                  </button>
                )}

                {/* Suggested Questions */}
                <div className="pt-4 border-t border-slate-200">
                  <p className="text-xs font-semibold text-slate-600 mb-3 uppercase">Suggested Questions</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {[
                      'What is covered?',
                      'What are the waiting periods?',
                      'What is excluded?',
                      'How do I claim?'
                    ].map((q: string, i: number) => (
                      <button
                        key={i}
                        onClick={() => handleAskQuestion(q)}
                        disabled={isAnswering}
                        className="text-left text-xs p-2 rounded border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 transition disabled:opacity-50 font-medium"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* REPORT TAB */}
          <TabsContent value="report" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Insurance Analysis Report</CardTitle>
                    <CardDescription>Professional policy analysis - fact-based and consultant-quality</CardDescription>
                  </div>
                  <button
                    onClick={handleGenerateReport}
                    disabled={isGeneratingReport || !analysis}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-400 transition font-medium"
                  >
                    <Download className="h-4 w-4" />
                    {isGeneratingReport ? 'Generating...' : 'Download PDF'}
                  </button>
                </div>
              </CardHeader>
              <CardContent>
                {isGeneratingReport ? (
                  // Loading skeleton
                  <div className="space-y-4">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className="bg-slate-200 animate-pulse rounded-lg h-12" />
                    ))}
                  </div>
                ) : analysis ? (
                  // Display actual analysis sections with markdown rendering
                  <div className="space-y-6">
                    {analysis.dashboard && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h3 className="font-semibold text-blue-900 mb-3">Executive Dashboard</h3>
                        <MarkdownRenderer content={analysis.dashboard} className="text-sm" />
                      </div>
                    )}

                    <Accordion type="single" collapsible className="w-full">
                      {analysis.snapshot && (
                        <AccordionItem value="snapshot">
                          <AccordionTrigger className="text-base font-semibold">Policy Snapshot</AccordionTrigger>
                          <AccordionContent>
                            <MarkdownRenderer content={analysis.snapshot} />
                          </AccordionContent>
                        </AccordionItem>
                      )}

                      {analysis.coverage && (
                        <AccordionItem value="coverage">
                          <AccordionTrigger className="text-base font-semibold">Coverage Analysis</AccordionTrigger>
                          <AccordionContent>
                            <MarkdownRenderer content={analysis.coverage} />
                          </AccordionContent>
                        </AccordionItem>
                      )}

                      {analysis.financial_limits && (
                        <AccordionItem value="limits">
                          <AccordionTrigger className="text-base font-semibold">Financial Caps & Sub-Limits</AccordionTrigger>
                          <AccordionContent>
                            <MarkdownRenderer content={analysis.financial_limits} />
                          </AccordionContent>
                        </AccordionItem>
                      )}

                      {analysis.waiting_periods && (
                        <AccordionItem value="waiting">
                          <AccordionTrigger className="text-base font-semibold">Waiting Periods</AccordionTrigger>
                          <AccordionContent>
                            <MarkdownRenderer content={analysis.waiting_periods} />
                          </AccordionContent>
                        </AccordionItem>
                      )}

                      {analysis.exclusions && (
                        <AccordionItem value="exclusions">
                          <AccordionTrigger className="text-base font-semibold">Exclusions</AccordionTrigger>
                          <AccordionContent>
                            <MarkdownRenderer content={analysis.exclusions} />
                          </AccordionContent>
                        </AccordionItem>
                      )}

                      {analysis.claim_restrictions && (
                        <AccordionItem value="claims">
                          <AccordionTrigger className="text-base font-semibold">Claim Restrictions</AccordionTrigger>
                          <AccordionContent>
                            <MarkdownRenderer content={analysis.claim_restrictions} />
                          </AccordionContent>
                        </AccordionItem>
                      )}

                      {analysis.important_clauses && (
                        <AccordionItem value="clauses">
                          <AccordionTrigger className="text-base font-semibold">Key Clauses</AccordionTrigger>
                          <AccordionContent>
                            <MarkdownRenderer content={analysis.important_clauses} />
                          </AccordionContent>
                        </AccordionItem>
                      )}

                      {analysis.recommendation && (
                        <AccordionItem value="recommendation">
                          <AccordionTrigger className="text-base font-semibold">Final Recommendation</AccordionTrigger>
                          <AccordionContent>
                            <MarkdownRenderer content={analysis.recommendation} />
                          </AccordionContent>
                        </AccordionItem>
                      )}
                    </Accordion>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <FileText className="h-12 w-12 mx-auto text-slate-300 mb-4" />
                    <p className="text-slate-600 font-medium">No analysis available</p>
                    <p className="text-slate-500 text-sm">Upload a document to generate an insurance analysis report</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
