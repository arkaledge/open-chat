'use client';

import { useState } from 'react';
import { Message } from '../../types';
import {
  GitBranch,
  RefreshCw,
  Edit2,
  MoreVertical,
  Copy,
  Check,
} from 'lucide-react';
import { apiService } from '../../services/api';
import { useRouter } from 'next/navigation';

interface MessageActionsProps {
  message: Message;
  conversationId: string;
  onEdit?: () => void;
  onRegenerate?: () => void;
}

export default function MessageActions({
  message,
  conversationId,
  onEdit,
  onRegenerate,
}: MessageActionsProps) {
  const router = useRouter();
  const [showMenu, setShowMenu] = useState(false);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleBranch = async () => {
    setLoading(true);
    try {
      const newConv = await apiService.branchFromMessage(
        conversationId,
        message.id,
        {}
      );
      router.push(`/chat/${newConv.id}`);
    } catch (error) {
      console.error('Failed to branch:', error);
      alert('Failed to create branch');
    } finally {
      setLoading(false);
      setShowMenu(false);
    }
  };

  const handleRegenerate = async () => {
    if (message.role !== 'assistant') return;

    setLoading(true);
    try {
      const result = await apiService.regenerateMessage(message.id, {
        keep_original: true,
      });
      router.push(`/chat/${result.id}`);
      onRegenerate?.();
    } catch (error) {
      console.error('Failed to regenerate:', error);
      alert('Failed to regenerate message');
    } finally {
      setLoading(false);
      setShowMenu(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
        disabled={loading}
      >
        <MoreVertical className="w-4 h-4" />
      </button>

      {showMenu && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />
          <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-20">
            <div className="py-1">
              <button
                onClick={handleBranch}
                disabled={loading}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2 disabled:opacity-50"
              >
                <GitBranch className="w-4 h-4" />
                <span>Branch from here</span>
              </button>

              {message.role === 'assistant' && (
                <button
                  onClick={handleRegenerate}
                  disabled={loading}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2 disabled:opacity-50"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Regenerate</span>
                </button>
              )}

              {message.role === 'user' && (
                <button
                  onClick={onEdit}
                  disabled={loading}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2 disabled:opacity-50"
                >
                  <Edit2 className="w-4 h-4" />
                  <span>Edit message</span>
                </button>
              )}

              <button
                onClick={handleCopy}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Copy text</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
