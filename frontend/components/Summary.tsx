import React from 'react'
import { FileText, BookOpen, Tag } from 'lucide-react'

interface SummaryProps {
  summary: string
  keyPoints: string[]
  mainTopics: string[]
}

export default function Summary({ summary, keyPoints, mainTopics }: SummaryProps) {
  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Summary</h3>
        </div>
        <p className="text-gray-700 leading-relaxed">{summary}</p>
      </div>

      {/* Key Points */}
      {keyPoints.length > 0 && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="h-5 w-5 text-green-600" />
            <h3 className="text-lg font-semibold text-gray-900">Key Points</h3>
          </div>
          <ul className="space-y-2">
            {keyPoints.map((point, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-green-100 text-green-700 text-sm font-medium flex-shrink-0 mt-0.5">
                  {index + 1}
                </span>
                <span className="text-gray-700">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Main Topics */}
      {mainTopics.length > 0 && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center gap-2 mb-3">
            <Tag className="h-5 w-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">Main Topics</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {mainTopics.map((topic, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-700"
              >
                {topic}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
