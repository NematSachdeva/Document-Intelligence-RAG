import React, { useState, useEffect } from 'react'
import { FileText, Upload, Download, AlertCircle, MessageCircle, BarChart3 } from 'lucide-react'
import FileUpload from '../components/FileUpload'
import ChatInterface from '../components/ChatInterface'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../components/ui/accordion'
import { Badge } from '../components/ui/badge'
import { uploadPDF, askQuestion, listDocuments, healthCheck, UploadResponse, SummaryResponse, Citation, Document } from '../lib/api'

export default function Home() {
  const [currentDocument, setCurrentDocument] = useState<UploadResponse | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [chatHistory, setChatHistory] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [apiError, setApiError] = useState<string>('')
  const [activeTab, setActiveTab] = useState('overview')

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
        setSummary(response.summary)
        setChatHistory([])
        setActiveTab('overview')
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

  const handleAskQuestion = async (question: string) => {
    if (!currentDocument) return

    try {
      const response = await askQuestion(currentDocument.document_id, question)
      if (response.success) {
        setChatHistory((prev) => [
          ...prev,
          { type: 'question', content: question, timestamp: new Date() },
          { type: 'answer', content: response.answer, citations: response.citations, timestamp: new Date() }
        ])
      } else {
        setError('Failed to get answer')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error processing question')
    }
  }

  const handleGenerateReport = async () => {
    if (!currentDocument) return

    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: currentDocument.document_id })
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${currentDocument.filename.replace('.pdf', '')}_Analysis_Report.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } else {
        setError('Failed to generate report')
      }
    } catch (err) {
      setError('Error generating report')
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
                        summary: {},
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
            <div>
              <p className="text-sm font-medium text-red-900">Backend Connection Error</p>
              <p className="text-sm text-red-700 mt-1">{apiError}</p>
            </div>
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
                {/* Chat Messages */}
                <div className="bg-slate-50 rounded-lg border border-slate-200 p-4 min-h-96 max-h-96 overflow-y-auto space-y-4">
                  {chatHistory.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500">
                      <MessageCircle className="h-12 w-12 mb-2 opacity-30" />
                      <p>No questions asked yet</p>
                      <p className="text-sm">Start by asking a question about the policy</p>
                    </div>
                  ) : (
                    chatHistory.map((msg, i) => (
                      <div key={i} className={`flex ${msg.type === 'question' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs px-4 py-2 rounded-lg ${
                          msg.type === 'question'
                            ? 'bg-blue-600 text-white rounded-br-none'
                            : 'bg-white border border-slate-200 text-slate-900 rounded-bl-none'
                        }`}>
                          <p className="text-sm">{msg.content}</p>
                          {msg.type === 'answer' && msg.citations && msg.citations.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {msg.citations.map((c: Citation, j: number) => (
                                <Badge key={j} variant="secondary" className="text-xs cursor-pointer hover:bg-slate-300">
                                  Page {c.page || 'N/A'}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Input */}
                <ChatInterface
                  onSendMessage={handleAskQuestion}
                  isLoading={isLoading}
                  error=""
                />

                {/* Suggested Questions */}
                <div className="pt-4 border-t border-slate-200">
                  <p className="text-xs font-semibold text-slate-600 mb-3 uppercase">Suggested Questions</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {[
                      'What is covered?',
                      'What are the waiting periods?',
                      'What is excluded?',
                      'How do I claim?'
                    ].map((q, i) => (
                      <button
                        key={i}
                        onClick={() => handleAskQuestion(q)}
                        disabled={isLoading}
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
                    <CardDescription>Professional policy analysis with recommendations</CardDescription>
                  </div>
                  <button
                    onClick={handleGenerateReport}
                    disabled={isLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-400 transition font-medium"
                  >
                    <Download className="h-4 w-4" />
                    {isLoading ? 'Generating...' : 'Download PDF'}
                  </button>
                </div>
              </CardHeader>
              <CardContent>
                <Accordion type="single" collapsible className="w-full">
                  <AccordionItem value="snapshot">
                    <AccordionTrigger>Policy Snapshot</AccordionTrigger>
                    <AccordionContent>
                      <p className="text-slate-700">Overview of the insurance policy including name, company, type, and key details.</p>
                      <p className="text-sm text-slate-500 mt-2">Click Download PDF to see the complete information</p>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="coverage">
                    <AccordionTrigger>Coverage Analysis</AccordionTrigger>
                    <AccordionContent>
                      <p className="text-slate-700">Detailed breakdown of all coverages including financial limits and restrictions.</p>
                      <p className="text-sm text-slate-500 mt-2">Click Download PDF to see the complete analysis</p>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="limits">
                    <AccordionTrigger>Financial Caps & Sub-Limits</AccordionTrigger>
                    <AccordionContent>
                      <p className="text-slate-700">Table of all financial limitations including room rent, ICU limits, and disease-specific caps.</p>
                      <p className="text-sm text-slate-500 mt-2">Click Download PDF to see the complete breakdown</p>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="waiting">
                    <AccordionTrigger>Waiting Periods</AccordionTrigger>
                    <AccordionContent>
                      <p className="text-slate-700">Analysis of all waiting periods and their impact on your coverage.</p>
                      <p className="text-sm text-slate-500 mt-2">Click Download PDF to see the complete waiting period analysis</p>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="exclusions">
                    <AccordionTrigger>Exclusions & Risks</AccordionTrigger>
                    <AccordionContent>
                      <p className="text-slate-700">Comprehensive list of all exclusions and high-risk factors flagged for your attention.</p>
                      <p className="text-sm text-slate-500 mt-2">Click Download PDF to see the complete exclusions analysis</p>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="claims">
                    <AccordionTrigger>Claim Restrictions</AccordionTrigger>
                    <AccordionContent>
                      <p className="text-slate-700">Important claim conditions and restrictions that may affect your claim settlement.</p>
                      <p className="text-sm text-slate-500 mt-2">Click Download PDF to see the complete claim analysis</p>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="recommendation">
                    <AccordionTrigger>Final Recommendation</AccordionTrigger>
                    <AccordionContent>
                      <p className="text-slate-700">Professional recommendation including suitable customers, advantages, and disadvantages.</p>
                      <p className="text-sm text-slate-500 mt-2">Click Download PDF to see the complete recommendation</p>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>

                <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-900">
                    <strong>Note:</strong> The comprehensive report is generated on-demand and includes all policy sections with professional analysis. Click Download PDF to generate the full report.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
