'use client';

import { useEffect, useRef } from 'react';
import { Message } from '../../types';
import MessageItem from './MessageItem';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  streamingMessage: string;
}

export default function MessageList({
  messages,
  isStreaming,
  streamingMessage,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-lg">
          <h2 className="text-2xl font-bold mb-4">Welcome to OpenChat</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Start a conversation with AI. Ask questions, get help with code, or explore ideas.
          </p>
          <div className="grid grid-cols-1 gap-3 text-left">
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-sm font-medium mb-1">💡 Try asking:</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                "Explain quantum computing in simple terms"
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-sm font-medium mb-1">🔍 Enable Web Search:</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                "What are the latest developments in AI?"
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-sm font-medium mb-1">📚 Enable RAG:</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                "Search my uploaded documents for information"
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}

        {isStreaming && streamingMessage && (
          <MessageItem
            message={{
              id: 'streaming',
              role: 'assistant',
              content: streamingMessage,
              conversation_id: '',
              prompt_tokens: 0,
              completion_tokens: 0,
              total_tokens: 0,
              estimated_cost: 0,
              metadata: {},
              created_at: new Date().toISOString(),
            }}
            isStreaming={true}
          />
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
