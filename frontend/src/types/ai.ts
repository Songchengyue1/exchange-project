import type { ProductListItem } from './product'

export type AISearchMode = 'hybrid' | 'keyword' | 'vector'

export interface AISearchResult {
  items: ProductListItem[]
  total: number
  page: number
  page_size: number
  mode: AISearchMode
  used_llm: boolean
  fallback: boolean
}

export interface AIRecommendResult {
  items: ProductListItem[]
  mode: 'history_vector' | 'popular' | 'empty'
}

export interface ChatStreamDone {
  conversation_id: number
  assistant_message_id: number
  product_ids: number[]
}

export interface AIMessage {
  id: number
  role: 'user' | 'assistant' | string
  content: string
  created_at: string
  product_ids: number[]
}

export interface AIConversation {
  id: number
  title: string | null
  created_at: string
  updated_at: string
}

export interface AIConversationDetail extends AIConversation {
  messages: AIMessage[]
}
