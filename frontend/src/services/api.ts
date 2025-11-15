/**
 * API service for backend communication
 */

import axios, { AxiosInstance } from 'axios';
import {
  User,
  Conversation,
  Message,
  ChatRequest,
  Model,
  AuthTokens,
  LoginCredentials,
  RegisterData,
} from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.client.interceptors.request.use((config) => {
      const token = this.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // If 401 and not already retried, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
              const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
                refresh_token: refreshToken,
              });

              const { access_token, refresh_token: newRefreshToken } = response.data;
              this.setTokens(access_token, newRefreshToken);

              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Token management
  private getAccessToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('access_token');
    }
    return null;
  }

  private getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('refresh_token');
    }
    return null;
  }

  public setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
    }
  }

  public clearTokens(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  // Authentication
  async register(data: RegisterData): Promise<AuthTokens> {
    const response = await this.client.post<AuthTokens>('/auth/register', data);
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }

  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await this.client.post<AuthTokens>('/auth/login', credentials);
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }

  async logout(): Promise<void> {
    this.clearTokens();
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  // Chat
  async chatCompletion(request: ChatRequest): Promise<Response> {
    const token = this.getAccessToken();

    const response = await fetch(`${API_URL}/api/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;
  }

  async streamChatCompletion(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): Promise<void> {
    const response = await this.chatCompletion({ ...request, stream: true });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No reader available');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          onComplete();
          break;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);

            if (data === '[DONE]') {
              continue;
            }

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.delta?.content;

              if (content) {
                onChunk(content);
              }
            } catch (e) {
              // Ignore JSON parse errors
            }
          }
        }
      }
    } catch (error) {
      onError(error as Error);
    }
  }

  async getModels(): Promise<{ models: Model[] }> {
    const response = await this.client.get<{ models: Model[] }>('/chat/models');
    return response.data;
  }

  // Conversations
  async createConversation(data: {
    title: string;
    model: string;
    workspace_id?: string;
  }): Promise<Conversation> {
    const response = await this.client.post<Conversation>('/conversations/', data);
    return response.data;
  }

  async getConversations(params?: {
    skip?: number;
    limit?: number;
    workspace_id?: string;
  }): Promise<Conversation[]> {
    const response = await this.client.get<Conversation[]>('/conversations/', { params });
    return response.data;
  }

  async getConversation(id: string): Promise<Conversation> {
    const response = await this.client.get<Conversation>(`/conversations/${id}`);
    return response.data;
  }

  async updateConversation(
    id: string,
    data: { title?: string; metadata?: Record<string, any> }
  ): Promise<Conversation> {
    const response = await this.client.patch<Conversation>(`/conversations/${id}`, data);
    return response.data;
  }

  async deleteConversation(id: string): Promise<void> {
    await this.client.delete(`/conversations/${id}`);
  }

  async getMessages(conversationId: string): Promise<Message[]> {
    const response = await this.client.get<Message[]>(
      `/conversations/${conversationId}/messages`
    );
    return response.data;
  }

  async addMessageFeedback(
    conversationId: string,
    messageId: string,
    feedback: number
  ): Promise<void> {
    await this.client.post(
      `/conversations/${conversationId}/messages/${messageId}/feedback?feedback=${feedback}`
    );
  }

  async searchConversations(query: string, limit = 20): Promise<Conversation[]> {
    const response = await this.client.get<Conversation[]>('/conversations/search', {
      params: { q: query, limit },
    });
    return response.data;
  }

  // Branching and Threading
  async branchConversation(
    conversationId: string,
    data: { title?: string; include_future_messages?: boolean }
  ): Promise<Conversation> {
    const response = await this.client.post<Conversation>(
      `/branches/conversations/${conversationId}/branch`,
      data
    );
    return response.data;
  }

  async branchFromMessage(
    conversationId: string,
    messageId: string,
    data: { new_content?: string; model?: string; temperature?: number }
  ): Promise<Conversation> {
    const response = await this.client.post<Conversation>(
      `/branches/conversations/${conversationId}/messages/${messageId}/branch`,
      data
    );
    return response.data;
  }

  async getBranchTree(conversationId: string): Promise<any> {
    const response = await this.client.get(`/branches/conversations/${conversationId}/tree`);
    return response.data;
  }

  async listBranches(conversationId: string): Promise<any[]> {
    const response = await this.client.get(
      `/branches/conversations/${conversationId}/branches`
    );
    return response.data;
  }

  async regenerateMessage(
    messageId: string,
    data: {
      model?: string;
      temperature?: number;
      max_tokens?: number;
      keep_original?: boolean;
    }
  ): Promise<Conversation> {
    const response = await this.client.post<Conversation>(
      `/branches/messages/${messageId}/regenerate`,
      data
    );
    return response.data;
  }

  async editMessage(
    messageId: string,
    data: {
      content: string;
      regenerate_response?: boolean;
      create_branch?: boolean;
    }
  ): Promise<Conversation> {
    const response = await this.client.post<Conversation>(
      `/branches/messages/${messageId}/edit`,
      data
    );
    return response.data;
  }
}

export const apiService = new APIService();
