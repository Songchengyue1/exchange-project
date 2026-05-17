import { computed, onUnmounted, ref, watch, type Ref } from 'vue'
import { PAYMENT_TIMEOUT_MS } from '../constants/orderPayment'

function parseMs(iso: string): number {
  const t = Date.parse(iso)
  return Number.isFinite(t) ? t : NaN
}

export function paymentExpiresAtMs(createdAt: string, expiresAt?: string | null): number {
  if (expiresAt) {
    const t = parseMs(expiresAt)
    if (Number.isFinite(t)) return t
  }
  const created = parseMs(createdAt)
  if (!Number.isFinite(created)) return Date.now()
  return created + PAYMENT_TIMEOUT_MS
}

export function formatCountdown(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000))
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function usePaymentCountdown(
  createdAt: Ref<string | undefined>,
  expiresAt: Ref<string | null | undefined>,
  options?: { onExpired?: () => void },
) {
  const remainingMs = ref(0)
  let timer: ReturnType<typeof setInterval> | null = null
  let expiredFired = false

  const deadlineMs = computed(() => {
    if (!createdAt.value) return Date.now()
    return paymentExpiresAtMs(createdAt.value, expiresAt.value)
  })

  const isExpired = computed(() => remainingMs.value <= 0)

  const label = computed(() => formatCountdown(remainingMs.value))

  function tick() {
    remainingMs.value = Math.max(0, deadlineMs.value - Date.now())
    if (remainingMs.value <= 0 && !expiredFired) {
      expiredFired = true
      options?.onExpired?.()
    }
  }

  function start() {
    stop()
    expiredFired = false
    tick()
    timer = setInterval(tick, 1000)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  watch([createdAt, expiresAt], () => {
    expiredFired = false
    start()
  }, { immediate: true })

  onUnmounted(stop)

  return { remainingMs, isExpired, label, stop, restart: start }
}
