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

export interface AISearchByImageResult extends AISearchResult {
  recognized_item: string | null
  keywords: string[]
  query: string
}

export interface AIRecommendResult {
  items: ProductListItem[]
  mode: 'history_vector' | 'popular' | 'empty'
}

export type AIProductsKind = 'target' | 'recommend'

export interface AIProductRef {
  id: number
  title: string
}

export interface ChatStreamDone {
  conversation_id: number
  assistant_message_id: number
  product_ids: number[]
  product_refs?: AIProductRef[]
  products_kind?: AIProductsKind
  /** 校正后的最终正文（覆盖流式过程中错误的「暂无匹配」等） */
  content?: string
}

export interface AIMessage {
  id: number
  role: 'user' | 'assistant' | string
  content: string
  created_at: string
  product_ids: number[]
  product_refs?: AIProductRef[]
  products_kind?: AIProductsKind
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
