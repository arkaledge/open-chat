/**
 * Types for conversation branching and threading
 */

export interface BranchInfo {
  conversation_id: string;
  parent_conversation_id?: string;
  branched_at_message_id?: string;
  branch_depth: number;
  title: string;
  created_at: string;
}

export interface BranchTree {
  conversation_id: string;
  title: string;
  created_at: string;
  message_count: number;
  branches: BranchTree[];
}

export interface BranchCreateRequest {
  title?: string;
  include_future_messages?: boolean;
}

export interface MessageBranchRequest {
  new_content?: string;
  model?: string;
  temperature?: number;
}

export interface RegenerateMessageRequest {
  model?: string;
  temperature?: number;
  max_tokens?: number;
  keep_original?: boolean;
}

export interface MessageEditRequest {
  content: string;
  regenerate_response?: boolean;
  create_branch?: boolean;
}
