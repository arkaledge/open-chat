'use client';

import { useEffect, useRef, useState } from 'react';
import { useChatStore } from '../../stores/chatStore';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ModelSelector from './ModelSelector';

export default function ChatInterface() {
  const {
    currentConversation,
    messages,
    isStreaming,
    streamingMessage,
    sendMessage,
    selectedModel,
  } = useChatStore();

  const [input, setInput] = useState('');
  const [ragEnabled, setRagEnabled] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const messageContent = input.trim();
    setInput('');

    await sendMessage(messageContent, {
      ragEnabled,
      webSearch: webSearchEnabled,
    });
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Model Selector Bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200 dark:border-gray-700">
        <ModelSelector />

        <div className="flex items-center space-x-4">
          <label className="flex items-center space-x-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={ragEnabled}
              onChange={(e) => setRagEnabled(e.target.checked)}
              className="rounded text-primary-600 focus:ring-primary-500"
            />
            <span>RAG</span>
          </label>

          <label className="flex items-center space-x-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={webSearchEnabled}
              onChange={(e) => setWebSearchEnabled(e.target.checked)}
              className="rounded text-primary-600 focus:ring-primary-500"
            />
            <span>Web Search</span>
          </label>
        </div>
      </div>

      {/* Messages Area */}
      <MessageList
        messages={messages}
        isStreaming={isStreaming}
        streamingMessage={streamingMessage}
      />

      {/* Input Area */}
      <MessageInput
        value={input}
        onChange={setInput}
        onSend={handleSend}
        disabled={isStreaming}
      />
    </div>
  );
}
