import React, { useRef } from 'react'
import { Upload, AlertCircle } from 'lucide-react'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  isLoading: boolean
  error?: string
}

export default function FileUpload({ onFileSelect, isLoading, error }: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        alert('Please select a PDF file')
        return
      }
      onFileSelect(file)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.currentTarget.classList.add('border-blue-500', 'bg-blue-50')
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.currentTarget.classList.remove('border-blue-500', 'bg-blue-50')
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.currentTarget.classList.remove('border-blue-500', 'bg-blue-50')

    const file = e.dataTransfer.files?.[0]
    if (file && file.type === 'application/pdf') {
      onFileSelect(file)
    } else {
      alert('Please drop a PDF file')
    }
  }

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer transition-colors hover:border-blue-500 hover:bg-blue-50"
      >
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700 mb-2">
          {isLoading ? 'Processing PDF...' : 'Drop your PDF here or click to upload'}
        </p>
        <p className="text-sm text-gray-500">
          Supports PDF files up to 50MB
        </p>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          disabled={isLoading}
          className="hidden"
        />
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  )
}
