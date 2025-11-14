'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Message } from '../../types';
import { User, Bot, ThumbsUp, ThumbsDown, Copy } from 'lucide-react';
import { useState } from 'react';
import 'highlight.js/styles/github-dark.css';

interface MessageItemProps {
  message: Message;
  isStreaming?: boolean;
}

export default function MessageItem({ message, isStreaming = false }: MessageItemProps) {
  const [copied, setCopied] = useState(false);

  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`flex ${
        isUser ? 'justify-end' : 'justify-start'
      } items-start space-x-3`}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}

      <div
        className={`flex-1 max-w-3xl ${
          isUser
            ? 'bg-primary-600 text-white rounded-2xl rounded-tr-sm px-4 py-3'
            : 'bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3'
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                code({ node, inline, className, children, ...props }) {
                  if (inline) {
                    return (
                      <code
                        className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-sm"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  }

                  return (
                    <div className="relative group">
                      <button
                        onClick={handleCopy}
                        className="absolute top-2 right-2 p-2 bg-gray-700 hover:bg-gray-600 rounded text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        {copied ? 'Copied!' : <Copy className="w-3 h-3" />}
                      </button>
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </div>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {!isUser && !isStreaming && (
          <div className="flex items-center space-x-2 mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
            <button
              className="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              title="Good response"
            >
              <ThumbsUp className="w-3 h-3" />
            </button>
            <button
              className="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              title="Bad response"
            >
              <ThumbsDown className="w-3 h-3" />
            </button>
            <button
              onClick={handleCopy}
              className="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              title="Copy"
            >
              <Copy className="w-3 h-3" />
            </button>
            {message.model && (
              <span className="ml-auto text-xs text-gray-500">
                {message.model}
              </span>
            )}
          </div>
        )}

        {isStreaming && (
          <div className="flex items-center space-x-1 mt-2">
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" />
            <div
              className="w-2 h-2 bg-primary-600 rounded-full animate-bounce"
              style={{ animationDelay: '0.1s' }}
            />
            <div
              className="w-2 h-2 bg-primary-600 rounded-full animate-bounce"
              style={{ animationDelay: '0.2s' }}
            />
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  );
}
