/**
 * TypeScript type definitions for the application
 */

export interface User {
  id: string;
  email: string;
  name: string;
  organization_id: string;
  roles: string[];
  preferences: Record<string, any>;
  status: string;
  created_at: string;
  last_login?: string;
  email_verified: boolean;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'system' | 'user' | 'assistant' | 'function';
  content: string;
  model?: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  metadata: Record<string, any>;
  feedback_score?: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  workspace_id?: string;
  title: string;
  model: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  stream?: boolean;
  conversation_id?: string;
  rag_enabled?: boolean;
  web_search?: boolean;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  name: string;
  password: string;
}
