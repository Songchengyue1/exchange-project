import { apiFetch } from './client'
import type {
  AIConversation,
  AIConversationDetail,
  AISearchResult,
  AIRecommendResult,
  ChatStreamDone,
} from '../types/ai'

export function recordBrowse(productId: number) {
  return apiFetch<void>('/api/v1/ai/browse', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId }),
  })
}

export function aiSearch(query: string, page = 1, pageSize = 12) {
  return apiFetch<AISearchResult>('/api/v1/ai/search', {
    method: 'POST',
    auth: false,
    body: JSON.stringify({ query, page, page_size: pageSize }),
  })
}

export function getRecommendations(limit = 8) {
  return apiFetch<AIRecommendResult>(`/api/v1/ai/recommendations?limit=${limit}`, { auth: false })
}

export function listAiConversations() {
  return apiFetch<AIConversation[]>('/api/v1/ai/conversations')
}

export function getAiConversation(id: number) {
  return apiFetch<AIConversationDetail>(`/api/v1/ai/conversations/${id}`)
}

export function deleteAiConversation(id: number) {
  return apiFetch<void>(`/api/v1/ai/conversations/${id}`, { method: 'DELETE' })
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

function getToken(): string | null {
  if (typeof localStorage === 'undefined') return null
  return localStorage.getItem('access_token')
}

export type ChatStreamHandler = {
  onChunk: (content: string) => void
  onMeta?: (data: { status?: string; product_ids?: number[] }) => void
  onDone: (data: ChatStreamDone) => void
  onError: (detail: string) => void
}

/** 流式对话：仅 assistant 分块；用户消息由调用方一次性展示 */
export async function streamAiChat(
  message: string,
  handlers: ChatStreamHandler,
  options?: { conversationId?: number; signal?: AbortSignal },
): Promise<void> {
  const token = getToken()
  if (!token) throw new Error('请先登录后使用 AI 助手')

  const res = await fetch(`${API_BASE}/api/v1/ai/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message,
      conversation_id: options?.conversationId ?? null,
    }),
    signal: options?.signal,
  })

  if (res.status === 401) {
    localStorage.removeItem('access_token')
    throw new Error('登录已失效')
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      const j = (await res.json()) as { detail?: unknown }
      if (typeof j.detail === 'string') detail = j.detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error('无法读取流式响应')

  const decoder = new TextDecoder()
  let buffer = ''

  const processBlock = (block: string) => {
    const lines = block.split('\n')
    let event = 'message'
    let dataStr = ''
    for (const line of lines) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataStr += line.slice(5).trim()
    }
    if (!dataStr) return
    try {
      const data = JSON.parse(dataStr) as Record<string, unknown>
      if (event === 'meta') {
        handlers.onMeta?.(data as { status?: string; product_ids?: number[] })
      } else if (event === 'chunk' && typeof data.content === 'string') {
        handlers.onChunk(data.content)
      } else if (event === 'done') {
        handlers.onDone(data as unknown as ChatStreamDone)
      } else if (event === 'error') {
        handlers.onError(typeof data.detail === 'string' ? data.detail : '对话失败')
      }
    } catch {
      /* ignore malformed */
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''
    for (const part of parts) {
      if (part.trim()) processBlock(part)
    }
  }
  if (buffer.trim()) processBlock(buffer)
}
