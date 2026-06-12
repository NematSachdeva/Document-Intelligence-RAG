import React from 'react'
import { Trash2, FileText } from 'lucide-react'
import { Document } from '@/lib/api'

interface DocumentListProps {
  documents: Document[]
  selectedDocument: string | null
  onSelectDocument: (documentId: string) => void
  onDeleteDocument: (documentId: string) => void
  isLoading: boolean
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  selectedDocument,
  onSelectDocument,
  onDeleteDocument,
  isLoading,
}) => {
  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <FileText className="mx-auto h-12 w-12 mb-3 text-gray-400" />
        <p>No documents uploaded yet</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Your Documents</h3>
      {documents.map((doc) => (
        <div
          key={doc.document_id}
          className={`p-3 rounded-lg cursor-pointer transition-all ${
            selectedDocument === doc.document_id
              ? 'bg-blue-100 border-2 border-blue-500'
              : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'
          }`}
          onClick={() => onSelectDocument(doc.document_id)}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="font-medium text-gray-900 truncate">{doc.filename}</p>
              <p className="text-xs text-gray-500 mt-1">
                {doc.pages} {doc.pages === 1 ? 'page' : 'pages'} • {doc.chunks} chunks
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDeleteDocument(doc.document_id)
              }}
              className="ml-2 p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
              title="Delete document"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
