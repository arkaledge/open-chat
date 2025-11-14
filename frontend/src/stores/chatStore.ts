/**
 * Zustand store for chat state
 */

import { create } from 'zustand';
import { Conversation, Message, Model } from '../types';
import { apiService } from '../services/api';

interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingMessage: string;
  models: Model[];
  selectedModel: string;
  error: string | null;

  // Actions
  fetchConversations: () => Promise<void>;
  fetchConversation: (id: string) => Promise<void>;
  createConversation: (title: string, model: string) => Promise<Conversation>;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (content: string, options?: { ragEnabled?: boolean; webSearch?: boolean }) => Promise<void>;
  setCurrentConversation: (conversation: Conversation | null) => void;
  setSelectedModel: (model: string) => void;
  fetchModels: () => Promise<void>;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingMessage: '',
  models: [],
  selectedModel: 'gpt-4o',
  error: null,

  fetchConversations: async () => {
    set({ isLoading: true, error: null });
    try {
      const conversations = await apiService.getConversations();
      set({ conversations, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch conversations',
        isLoading: false,
      });
    }
  },

  fetchConversation: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await apiService.getConversation(id);
      set({
        currentConversation: conversation,
        messages: conversation.messages,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch conversation',
        isLoading: false,
      });
    }
  },

  createConversation: async (title: string, model: string) => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await apiService.createConversation({ title, model });
      set((state) => ({
        conversations: [conversation, ...state.conversations],
        currentConversation: conversation,
        messages: [],
        isLoading: false,
      }));
      return conversation;
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to create conversation',
        isLoading: false,
      });
      throw error;
    }
  },

  deleteConversation: async (id: string) => {
    try {
      await apiService.deleteConversation(id);
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== id),
        currentConversation:
          state.currentConversation?.id === id ? null : state.currentConversation,
        messages: state.currentConversation?.id === id ? [] : state.messages,
      }));
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to delete conversation',
      });
    }
  },

  sendMessage: async (content: string, options = {}) => {
    const { currentConversation, messages, selectedModel } = get();

    // Add user message optimistically
    const userMessage: Partial<Message> = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      conversation_id: currentConversation?.id || '',
      prompt_tokens: 0,
      completion_tokens: 0,
      total_tokens: 0,
      estimated_cost: 0,
      metadata: {},
    };

    set((state) => ({
      messages: [...state.messages, userMessage as Message],
      isStreaming: true,
      streamingMessage: '',
      error: null,
    }));

    try {
      // Create conversation if needed
      let conversationId = currentConversation?.id;
      if (!conversationId) {
        const newConversation = await get().createConversation('New Chat', selectedModel);
        conversationId = newConversation.id;
      }

      const allMessages = [...messages, userMessage as Message].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      let fullResponse = '';

      await apiService.streamChatCompletion(
        {
          model: selectedModel,
          messages: allMessages,
          conversation_id: conversationId,
          rag_enabled: options.ragEnabled,
          web_search: options.webSearch,
          stream: true,
        },
        (chunk: string) => {
          fullResponse += chunk;
          set({ streamingMessage: fullResponse });
        },
        () => {
          // On complete, add assistant message
          const assistantMessage: Partial<Message> = {
            id: `temp-${Date.now()}`,
            role: 'assistant',
            content: fullResponse,
            created_at: new Date().toISOString(),
            conversation_id: conversationId || '',
            model: selectedModel,
            prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0,
            estimated_cost: 0,
            metadata: {},
          };

          set((state) => ({
            messages: [...state.messages, assistantMessage as Message],
            isStreaming: false,
            streamingMessage: '',
          }));

          // Refresh conversation to get actual data
          if (conversationId) {
            get().fetchConversation(conversationId);
          }
        },
        (error: Error) => {
          set({
            isStreaming: false,
            streamingMessage: '',
            error: error.message || 'Failed to send message',
          });
        }
      );
    } catch (error: any) {
      set({
        isStreaming: false,
        streamingMessage: '',
        error: error.message || 'Failed to send message',
      });
    }
  },

  setCurrentConversation: (conversation: Conversation | null) => {
    set({
      currentConversation: conversation,
      messages: conversation?.messages || [],
    });
  },

  setSelectedModel: (model: string) => {
    set({ selectedModel: model });
  },

  fetchModels: async () => {
    try {
      const { models } = await apiService.getModels();
      set({ models });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch models',
      });
    }
  },

  clearError: () => set({ error: null }),
}));
