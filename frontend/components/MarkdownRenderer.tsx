import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export default function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Tables
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-4">
              <table className="w-full border-collapse border border-slate-300" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-slate-100" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="border border-slate-300 px-3 py-2 text-left font-semibold text-slate-900" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="border border-slate-300 px-3 py-2 text-slate-700" {...props} />
          ),
          tr: ({ node, ...props }) => {
            // Alternate row colors
            const isOdd = (node?.position?.start.line ?? 0) % 2 === 0
            return (
              <tr className={isOdd ? 'bg-white' : 'bg-slate-50'} {...props} />
            )
          },
          // Lists
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-inside my-2 space-y-1 text-slate-700" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-inside my-2 space-y-1 text-slate-700" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="text-slate-700" {...props} />
          ),
          // Headings
          h1: ({ node, ...props }) => (
            <h1 className="text-2xl font-bold my-3 text-slate-900" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-xl font-bold my-3 text-slate-900" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-lg font-bold my-2 text-slate-900" {...props} />
          ),
          // Paragraphs
          p: ({ node, ...props }) => (
            <p className="my-2 text-slate-700 leading-relaxed" {...props} />
          ),
          // Code blocks
          code: (props: any) => {
            const { node, inline, children, ...rest } = props
            if (inline) {
              return (
                <code className="bg-slate-100 px-2 py-1 rounded text-sm font-mono text-red-600" {...rest}>
                  {children}
                </code>
              )
            }
            return (
              <code className="block bg-slate-800 text-slate-100 p-3 rounded-lg my-2 overflow-x-auto font-mono text-sm" {...rest}>
                {children}
              </code>
            )
          },
          pre: ({ node, ...props }) => (
            <pre className="bg-slate-800 text-slate-100 p-3 rounded-lg my-2 overflow-x-auto" {...props} />
          ),
          // Bold/Strong
          strong: ({ node, ...props }) => (
            <strong className="font-bold text-slate-900" {...props} />
          ),
          // Emphasis
          em: ({ node, ...props }) => (
            <em className="italic text-slate-700" {...props} />
          ),
          // Blockquotes
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-4 border-slate-300 pl-4 my-2 italic text-slate-600" {...props} />
          ),
          // Horizontal rule
          hr: ({ node, ...props }) => (
            <hr className="my-4 border-slate-300" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
