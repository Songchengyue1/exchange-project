<script setup lang="ts">
import { computed, toRef } from 'vue'
import { usePaymentCountdown } from '../composables/usePaymentCountdown'

const props = withDefaults(
  defineProps<{
    createdAt: string
    paymentExpiresAt?: string | null
    compact?: boolean
  }>(),
  { compact: false },
)

const emit = defineEmits<{
  expired: []
}>()

const { label, isExpired } = usePaymentCountdown(
  toRef(props, 'createdAt'),
  toRef(props, 'paymentExpiresAt'),
  { onExpired: () => emit('expired') },
)

const text = computed(() =>
  isExpired.value ? '付款已超时，订单将自动取消' : `剩余付款时间 ${label.value}`,
)
</script>

<template>
  <p class="countdown" :class="{ 'countdown--warn': isExpired, 'countdown--compact': compact }">
    {{ text }}
  </p>
</template>

<style scoped>
.countdown {
  margin: 0 0 var(--space-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-warning);
}

.countdown--compact {
  margin: var(--space-xs) 0 0;
  font-size: 12px;
  font-weight: 400;
}

.countdown--warn {
  color: var(--color-body-strong);
}
</style>
