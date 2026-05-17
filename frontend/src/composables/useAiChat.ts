import { ref } from 'vue'

const open = ref(false)
const LAST_CONV_KEY = 'ai_last_conversation_id'

export function getLastConversationId(): number | undefined {
  if (typeof localStorage === 'undefined') return undefined
  const raw = localStorage.getItem(LAST_CONV_KEY)
  if (!raw) return undefined
  const n = Number(raw)
  return Number.isFinite(n) && n > 0 ? n : undefined
}

export function setLastConversationId(id: number) {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(LAST_CONV_KEY, String(id))
}

export function clearLastConversationId() {
  if (typeof localStorage === 'undefined') return
  localStorage.removeItem(LAST_CONV_KEY)
}

export function useAiChat() {
  function show() {
    open.value = true
  }
  function hide() {
    open.value = false
  }
  function toggle() {
    open.value = !open.value
  }
  return { open, show, hide, toggle }
}
