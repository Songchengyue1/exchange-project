<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { deleteAiConversation, getAiConversation, listAiConversations, streamAiChat } from '../api/ai'
import { showConfirm } from '../composables/useConfirm'
import {
  clearLastConversationId,
  getLastConversationId,
  setLastConversationId,
  useAiChat,
} from '../composables/useAiChat'
import { useAuthStore } from '../stores/auth'
import type { AIConversation, AIMessage, AIProductRef, AIProductsKind, ChatStreamDone } from '../types/ai'

type ChatMsg = {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  thinking?: boolean
  productIds?: number[]
  productRefs?: AIProductRef[]
  productsKind?: AIProductsKind
}

const { open, hide } = useAiChat()
const auth = useAuthStore()

const input = ref('')
const messages = ref<ChatMsg[]>([])
const conversationId = ref<number | undefined>()
const conversations = ref<AIConversation[]>([])
const historyLoading = ref(false)
const messagesLoading = ref(false)
const showHistory = ref(true)
const streaming = ref(false)
const deletingId = ref<number | null>(null)
const error = ref('')
const listEl = ref<HTMLElement | null>(null)
let abortCtrl: AbortController | null = null

const canSend = computed(() => !!input.value.trim() && !streaming.value && !messagesLoading.value)

function scrollBottom() {
  void nextTick(() => {
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
  })
}

function isThinking(m: ChatMsg) {
  return m.role === 'assistant' && !!m.thinking
}

function showCursor(m: ChatMsg) {
  return m.role === 'assistant' && m.streaming && !m.thinking && !!m.content
}

function formatHistoryTime(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  const sameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  if (sameDay) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function productLinksFromMessage(m: Pick<AIMessage, 'product_ids' | 'product_refs' | 'products_kind'>) {
  const refs =
    m.product_refs?.length
      ? m.product_refs
      : m.product_ids?.map((id) => ({ id, title: `商品 #${id}` }))
  if (!refs?.length) return { productRefs: undefined, productsKind: undefined as AIProductsKind | undefined }
  return {
    productRefs: refs,
    productsKind: m.products_kind ?? 'recommend',
  }
}

function linksSectionLabel(kind?: AIProductsKind) {
  return kind === 'target' ? '目标商品' : '推荐商品'
}

function mapApiMessage(m: AIMessage): ChatMsg {
  const role = m.role === 'user' ? 'user' : 'assistant'
  const links = productLinksFromMessage(m)
  return {
    id: `db-${m.id}`,
    role,
    content: m.content,
    productIds: m.product_ids?.length ? m.product_ids : undefined,
    productRefs: links.productRefs,
    productsKind: links.productsKind,
  }
}

async function loadConversationList() {
  if (!auth.token) return
  historyLoading.value = true
  try {
    conversations.value = await listAiConversations()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载历史失败'
  } finally {
    historyLoading.value = false
  }
}

async function loadConversation(id: number) {
  if (!auth.token) return
  messagesLoading.value = true
  error.value = ''
  try {
    const detail = await getAiConversation(id)
    conversationId.value = detail.id
    setLastConversationId(detail.id)
    messages.value = detail.messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map(mapApiMessage)
    scrollBottom()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载会话失败'
    if (conversationId.value === id) {
      conversationId.value = undefined
      clearLastConversationId()
    }
  } finally {
    messagesLoading.value = false
  }
}

function startNewChat() {
  abortCtrl?.abort()
  abortCtrl = null
  streaming.value = false
  conversationId.value = undefined
  messages.value = []
  error.value = ''
  clearLastConversationId()
}

async function deleteConversation(c: AIConversation, e: Event) {
  e.stopPropagation()
  e.preventDefault()
  if (streaming.value || deletingId.value !== null) return

  const ok = await showConfirm({
    title: '删除对话',
    message: `确定删除「${convTitle(c)}」？删除后无法恢复。`,
    confirmText: '删除',
    cancelText: '取消',
    variant: 'danger',
  })
  if (!ok) return

  deletingId.value = c.id
  error.value = ''
  try {
    await deleteAiConversation(c.id)
    conversations.value = conversations.value.filter((x) => x.id !== c.id)
    if (conversationId.value === c.id) {
      startNewChat()
    } else if (getLastConversationId() === c.id) {
      clearLastConversationId()
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '删除失败'
  } finally {
    deletingId.value = null
  }
}

async function onOpenDrawer() {
  if (!auth.token) {
    error.value = '请先登录后使用 AI 助手'
    return
  }
  await loadConversationList()
  const lastId = getLastConversationId()
  if (lastId && conversations.value.some((c) => c.id === lastId)) {
    await loadConversation(lastId)
  } else if (conversations.value.length && !messages.value.length) {
    await loadConversation(conversations.value[0].id)
  }
}

watch(open, (v) => {
  if (v) {
    void onOpenDrawer()
  } else {
    abortCtrl?.abort()
    abortCtrl = null
    streaming.value = false
  }
})

function close() {
  hide()
}

async function send() {
  const text = input.value.trim()
  if (!text || streaming.value || messagesLoading.value) return
  if (!auth.token) {
    error.value = '请先登录'
    return
  }

  error.value = ''
  streaming.value = true
  input.value = ''

  const userId = `u-${Date.now()}`
  messages.value.push({ id: userId, role: 'user', content: text })

  const assistantId = `a-${Date.now()}`
  messages.value.push({
    id: assistantId,
    role: 'assistant',
    content: '',
    streaming: true,
    thinking: true,
  })
  scrollBottom()

  abortCtrl?.abort()
  abortCtrl = new AbortController()

  try {
    await streamAiChat(
      text,
      {
        onMeta() {
          scrollBottom()
        },
        onChunk(chunk) {
          const m = messages.value.find((x) => x.id === assistantId)
          if (!m) return
          m.thinking = false
          m.content += chunk
          scrollBottom()
        },
        onDone(data: ChatStreamDone) {
          conversationId.value = data.conversation_id
          setLastConversationId(data.conversation_id)
          const m = messages.value.find((x) => x.id === assistantId)
          if (m) {
            m.streaming = false
            m.thinking = false
            const links = productLinksFromMessage({
              product_ids: data.product_ids ?? [],
              product_refs: data.product_refs,
              products_kind: data.products_kind,
            })
            m.productIds = data.product_ids ?? []
            m.productRefs = links.productRefs
            m.productsKind = links.productsKind
            if (typeof data.content === 'string' && data.content.trim()) {
              m.content = data.content
            }
          }
          void loadConversationList()
          scrollBottom()
        },
        onError(detail) {
          error.value = detail
          const m = messages.value.find((x) => x.id === assistantId)
          if (m) {
            m.streaming = false
            m.thinking = false
            if (!m.content) m.content = detail
          }
        },
      },
      { conversationId: conversationId.value, signal: abortCtrl.signal },
    )
  } catch (e) {
    if ((e as Error).name === 'AbortError') return
    error.value = e instanceof Error ? e.message : '发送失败'
    const m = messages.value.find((x) => x.id === assistantId)
    if (m) {
      m.streaming = false
      m.thinking = false
      if (!m.content) m.content = error.value
    }
  } finally {
    streaming.value = false
    abortCtrl = null
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    void send()
  }
}

function convTitle(c: AIConversation) {
  return c.title?.trim() || `会话 #${c.id}`
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="drawer-root" @click.self="close">
      <aside class="drawer" :class="{ 'drawer--wide': showHistory }" role="dialog" aria-label="AI 助手">
        <header class="drawer__head">
          <div>
            <p class="drawer__eyebrow ds-label-caps">AI Assistant</p>
            <h2 class="drawer__title">酱菜智能客服</h2>
          </div>
          <div class="drawer__head-actions">
            <button type="button" class="drawer__icon-btn" title="历史记录" @click="showHistory = !showHistory">
              历史
            </button>
            <button type="button" class="drawer__icon-btn drawer__icon-btn--primary" @click="startNewChat">
              新对话
            </button>
            <button type="button" class="drawer__close" aria-label="关闭" @click="close">×</button>
          </div>
        </header>
        <div class="drawer__stripe ds-m-stripe" aria-hidden="true" />

        <div class="drawer__body">
          <aside v-if="showHistory" class="history">
            <p class="history__label ds-label-caps">历史记录</p>
            <p v-if="historyLoading" class="history__muted">加载中…</p>
            <p v-else-if="!conversations.length" class="history__muted">暂无历史，发送消息后将自动保存</p>
            <ul v-else class="history__list">
              <li v-for="c in conversations" :key="c.id" class="history__row">
                <button
                  type="button"
                  class="history__item"
                  :class="{ 'history__item--on': conversationId === c.id }"
                  :disabled="deletingId === c.id"
                  @click="loadConversation(c.id)"
                >
                  <span class="history__item-title">{{ convTitle(c) }}</span>
                  <span class="history__item-time">{{ formatHistoryTime(c.updated_at) }}</span>
                </button>
                <button
                  type="button"
                  class="history__delete"
                  :disabled="deletingId === c.id || streaming"
                  aria-label="删除此对话"
                  title="删除"
                  @click="deleteConversation(c, $event)"
                >
                  {{ deletingId === c.id ? '…' : '×' }}
                </button>
              </li>
            </ul>
          </aside>

          <div class="chat">
            <div ref="listEl" class="chat__messages">
              <p v-if="messagesLoading" class="chat__hint">加载会话中…</p>
              <p v-else-if="!messages.length" class="chat__hint">
                可询问商品推荐、如何下单、模拟支付等。回答基于平台已上架商品检索，对话将自动保存。
              </p>
              <div
                v-for="m in messages"
                :key="m.id"
                class="bubble-row"
                :class="m.role === 'user' ? 'bubble-row--user' : 'bubble-row--bot'"
              >
                <div class="bubble" :class="m.role === 'user' ? 'bubble--user' : 'bubble--bot'">
                  <div v-if="isThinking(m)" class="bubble__thinking" aria-live="polite">
                    <span class="thinking-dots" aria-hidden="true">
                      <span /><span /><span />
                    </span>
                    <span class="thinking-label">AI 思考中</span>
                  </div>
                  <p v-else class="bubble__text">
                    {{ m.content }}<span v-if="showCursor(m)" class="cursor">▍</span>
                  </p>
                  <div v-if="m.productRefs?.length && !isThinking(m)" class="bubble__links">
                    <p class="bubble__links-label ds-label-caps">
                      {{ linksSectionLabel(m.productsKind) }}
                    </p>
                    <RouterLink
                      v-for="ref in m.productRefs"
                      :key="ref.id"
                      class="bubble__link"
                      :to="`/products/${ref.id}`"
                      @click="close"
                    >
                      {{ ref.title }}
                    </RouterLink>
                  </div>
                </div>
              </div>
            </div>

            <p v-if="error" class="chat__error ds-form-error">{{ error }}</p>

            <footer class="chat__foot">
              <div class="composer">
                <textarea
                  v-model="input"
                  class="composer__input"
                  rows="2"
                  placeholder="输入问题… Enter 发送"
                  @keydown="onKeydown"
                />
                <button type="button" class="composer__send" :disabled="!canSend" @click="send">发送</button>
              </div>
            </footer>
          </div>
        </div>
      </aside>
    </div>
  </Teleport>
</template>

<style scoped>
.drawer-root {
  position: fixed;
  inset: 0;
  z-index: 900;
  background: rgba(0, 0, 0, 0.55);
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: flex-end;
}

.drawer {
  width: min(100%, 420px);
  height: 100%;
  background: var(--color-canvas);
  border-left: 1px solid var(--color-hairline);
  display: flex;
  flex-direction: column;
  box-shadow: -12px 0 40px rgba(0, 0, 0, 0.45);
}

.drawer--wide {
  width: min(100%, 720px);
}

.drawer__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--space-lg);
  gap: var(--space-md);
  flex-shrink: 0;
}

.drawer__head-actions {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  flex-shrink: 0;
}

.drawer__icon-btn {
  padding: 8px 12px;
  border: 1px solid var(--color-hairline);
  border-radius: 10px;
  background: var(--color-surface-card);
  color: var(--color-body);
  font-size: 12px;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition:
    border-color var(--duration-fast) ease,
    background-color var(--duration-fast) ease;
}

.drawer__icon-btn:hover {
  border-color: var(--color-body-strong);
  color: var(--color-on-dark);
}

.drawer__icon-btn--primary {
  border-color: var(--color-on-dark);
  color: var(--color-on-dark);
}

.drawer__eyebrow {
  margin: 0 0 var(--space-xs);
  color: var(--color-muted);
}

.drawer__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.drawer__close {
  border: 1px solid var(--color-hairline);
  border-radius: 10px;
  background: var(--color-surface-card);
  color: var(--color-on-dark);
  width: 36px;
  height: 36px;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.drawer__stripe {
  flex-shrink: 0;
}

.drawer__body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.history {
  width: 200px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  gap: var(--space-sm);
  overflow-y: auto;
}

.history__label {
  margin: 0;
  color: var(--color-muted);
}

.history__muted {
  margin: 0;
  font-size: 13px;
  font-weight: 400;
  color: var(--color-muted);
  line-height: 1.5;
}

.history__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.history__row {
  display: flex;
  align-items: stretch;
  gap: 4px;
}

.history__item {
  flex: 1;
  min-width: 0;
  text-align: left;
  padding: 10px 12px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition:
    background-color var(--duration-fast) ease,
    border-color var(--duration-fast) ease;
}

.history__item:hover {
  background: var(--color-surface-card);
  border-color: var(--color-hairline);
}

.history__item--on {
  background: var(--color-surface-elevated);
  border-color: var(--color-body-strong);
}

.history__item-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-dark);
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history__item-time {
  font-size: 11px;
  color: var(--color-muted);
}

.history__item:disabled {
  opacity: 0.5;
  cursor: wait;
}

.history__delete {
  flex-shrink: 0;
  width: 32px;
  align-self: center;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: var(--color-muted);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  transition:
    color var(--duration-fast) ease,
    background-color var(--duration-fast) ease,
    border-color var(--duration-fast) ease;
}

.history__delete:hover:not(:disabled) {
  color: var(--color-m-red);
  border-color: rgba(226, 39, 24, 0.35);
  background: rgba(226, 39, 24, 0.08);
}

.history__delete:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat__messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.chat__hint {
  margin: 0;
  padding: var(--space-md);
  font-size: 14px;
  font-weight: 400;
  color: var(--color-body);
  line-height: 1.55;
  border: 1px solid var(--color-hairline);
  border-radius: 14px;
  background: var(--color-surface-soft);
}

.chat__error {
  margin: 0 var(--space-lg) var(--space-sm);
}

.chat__foot {
  padding: var(--space-md) var(--space-lg) var(--space-lg);
  border-top: 1px solid var(--color-hairline);
  flex-shrink: 0;
}

.bubble-row {
  display: flex;
  width: 100%;
}

.bubble-row--user {
  justify-content: flex-end;
}

.bubble-row--bot {
  justify-content: flex-start;
}

.bubble {
  max-width: min(92%, 320px);
  padding: 12px 14px;
  border: 1px solid var(--color-hairline);
}

.bubble--user {
  border-radius: 18px 18px 4px 18px;
  background: linear-gradient(145deg, var(--color-surface-elevated), var(--color-surface-card));
}

.bubble--bot {
  border-radius: 18px 18px 18px 4px;
  background: var(--color-surface-card);
}

.bubble__thinking {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 22px;
}

.thinking-label {
  font-size: 14px;
  color: var(--color-body);
}

.thinking-dots {
  display: inline-flex;
  gap: 4px;
}

.thinking-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-body-strong);
  animation: thinking-bounce 1.2s ease-in-out infinite;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.thinking-dots span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes thinking-bounce {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.45;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.bubble__text {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-on-dark);
  white-space: pre-wrap;
  word-break: break-word;
}

.cursor {
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

.bubble__links {
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-hairline);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.bubble__links-label {
  margin: 0 0 2px;
  font-size: 11px;
  color: var(--color-muted);
  letter-spacing: 0.06em;
}

.bubble__link {
  font-size: 13px;
  color: var(--color-m-blue-light);
  text-decoration: none;
}

.bubble__link:hover {
  text-decoration: underline;
}

.composer {
  display: flex;
  align-items: flex-end;
  gap: var(--space-sm);
  padding: 8px;
  border: 1px solid var(--color-hairline);
  border-radius: 16px;
  background: var(--color-surface-soft);
}

.composer:focus-within {
  border-color: var(--color-body-strong);
}

.composer__input {
  flex: 1;
  min-height: 44px;
  max-height: 120px;
  resize: none;
  border: none;
  background: transparent;
  color: var(--color-on-dark);
  font-size: 14px;
  padding: 8px 4px;
  outline: none;
}

.composer__send {
  flex-shrink: 0;
  height: 40px;
  padding: 0 18px;
  border: 1px solid var(--color-on-dark);
  border-radius: 12px;
  background: var(--color-on-dark);
  color: var(--color-on-primary);
  font-weight: 700;
  cursor: pointer;
}

.composer__send:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .drawer--wide {
    width: 100%;
  }

  .history {
    width: 140px;
  }
}
</style>
