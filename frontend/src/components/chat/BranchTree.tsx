'use client';

import { useEffect, useState } from 'react';
import { GitBranch, MessageSquare } from 'lucide-react';
import { apiService } from '../../services/api';
import { useRouter } from 'next/navigation';

interface BranchNode {
  conversation_id: string;
  title: string;
  created_at: string;
  message_count: number;
  branches: BranchNode[];
}

interface BranchTreeProps {
  conversationId: string;
  onClose: () => void;
}

export default function BranchTree({ conversationId, onClose }: BranchTreeProps) {
  const router = useRouter();
  const [tree, setTree] = useState<BranchNode | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTree();
  }, [conversationId]);

  const loadTree = async () => {
    try {
      const data = await apiService.getBranchTree(conversationId);
      setTree(data);
    } catch (error) {
      console.error('Failed to load branch tree:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderNode = (node: BranchNode, depth: number = 0) => {
    const isCurrentConversation = node.conversation_id === conversationId;

    return (
      <div key={node.conversation_id} className="space-y-2">
        <button
          onClick={() => {
            router.push(`/chat/${node.conversation_id}`);
            onClose();
          }}
          className={`w-full text-left p-3 rounded-lg transition-colors ${
            isCurrentConversation
              ? 'bg-primary-100 dark:bg-primary-900 border-2 border-primary-500'
              : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 border border-gray-200 dark:border-gray-700'
          }`}
          style={{ marginLeft: `${depth * 20}px` }}
        >
          <div className="flex items-start gap-3">
            <GitBranch
              className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                isCurrentConversation
                  ? 'text-primary-600 dark:text-primary-400'
                  : 'text-gray-500 dark:text-gray-400'
              }`}
            />
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                {node.title}
              </div>
              <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  <MessageSquare className="w-3 h-3" />
                  {node.message_count} messages
                </span>
                <span>{new Date(node.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </button>

        {node.branches.length > 0 && (
          <div className="space-y-2">
            {node.branches.map((branch) => renderNode(branch, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            <h2 className="text-lg font-semibold">Conversation Branches</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-gray-500">Loading branch tree...</div>
            </div>
          ) : tree ? (
            <div className="space-y-2">{renderNode(tree)}</div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No branch data available
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Click on any branch to navigate to that conversation. The current conversation is
            highlighted.
          </p>
        </div>
      </div>
    </div>
  );
}
