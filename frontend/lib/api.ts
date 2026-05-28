import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface UploadResponse {
  document_id: string
  filename: string
  pages: number
  chunks: number
  summary: {
    summary: string
    key_points: string[]
    main_topics: string[]
    success: boolean
  }
  success: boolean
}

export interface Citation {
  source_id: number
  page_number: number
  chunk_id: string
}

export interface AnswerResponse {
  answer: string
  citations: Citation[]
  success: boolean
}

export interface SummaryResponse {
  summary: string
  key_points: string[]
  main_topics: string[]
  success: boolean
}

export interface Document {
  document_id: string
  filename: string
  pages: number
  chunks: number
}

// Upload PDF
export const uploadPDF = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

// Ask question
export const askQuestion = async (
  documentId: string,
  question: string
): Promise<AnswerResponse> => {
  const response = await api.post<AnswerResponse>('/ask', {
    document_id: documentId,
    question,
  })

  return response.data
}

// Get summary
export const getSummary = async (documentId: string): Promise<SummaryResponse> => {
  const response = await api.get<SummaryResponse>(`/summary/${documentId}`)
  return response.data
}

// List documents
export const listDocuments = async (): Promise<{ documents: Document[] }> => {
  const response = await api.get('/documents')
  return response.data
}

// Delete document
export const deleteDocument = async (documentId: string): Promise<{ success: boolean }> => {
  const response = await api.delete(`/documents/${documentId}`)
  return response.data
}

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}
