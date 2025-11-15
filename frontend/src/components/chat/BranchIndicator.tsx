'use client';

import { useEffect, useState } from 'react';
import { GitBranch, ChevronRight } from 'lucide-react';
import { apiService } from '../../services/api';
import { useRouter } from 'next/navigation';

interface BranchIndicatorProps {
  conversationId: string;
  metadata?: Record<string, any>;
}

export default function BranchIndicator({
  conversationId,
  metadata,
}: BranchIndicatorProps) {
  const router = useRouter();
  const [branches, setBranches] = useState<any[]>([]);
  const [showBranches, setShowBranches] = useState(false);

  useEffect(() => {
    loadBranches();
  }, [conversationId]);

  const loadBranches = async () => {
    try {
      const branchList = await apiService.listBranches(conversationId);
      setBranches(branchList);
    } catch (error) {
      console.error('Failed to load branches:', error);
    }
  };

  const hasBranches = branches.length > 0;
  const isBranch = metadata?.branched_from;

  if (!hasBranches && !isBranch) {
    return null;
  }

  return (
    <div className="space-y-2">
      {/* Show if this is a branch */}
      {isBranch && (
        <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <GitBranch className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span className="text-sm text-blue-900 dark:text-blue-100">
            Branched from{' '}
            <button
              onClick={() => router.push(`/chat/${metadata.branched_from}`)}
              className="font-medium hover:underline"
            >
              original conversation
            </button>
          </span>
        </div>
      )}

      {/* Show child branches */}
      {hasBranches && (
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <button
            onClick={() => setShowBranches(!showBranches)}
            className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors"
          >
            <div className="flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {branches.length} {branches.length === 1 ? 'Branch' : 'Branches'}
              </span>
            </div>
            <ChevronRight
              className={`w-4 h-4 transition-transform ${
                showBranches ? 'rotate-90' : ''
              }`}
            />
          </button>

          {showBranches && (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {branches.map((branch) => (
                <button
                  key={branch.conversation_id}
                  onClick={() => router.push(`/chat/${branch.conversation_id}`)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {branch.title}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Created {new Date(branch.created_at).toLocaleDateString()}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
