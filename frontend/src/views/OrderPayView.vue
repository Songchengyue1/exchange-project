<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import OrderPaymentCountdown from '../components/OrderPaymentCountdown.vue'
import { cancelOrder, getOrder, mockPayOrder } from '../api/orders'
import { PAYMENT_TIMEOUT_MINUTES } from '../constants/orderPayment'
import { showConfirm } from '../composables/useConfirm'
import type { OrderDetail } from '../types/order'
import { ORDER_STATUS_LABELS } from '../constants/orderLabels'
import { TRADE_LABELS } from '../constants/productLabels'

const route = useRoute()
const router = useRouter()
const orderId = computed(() => Number(route.params.id))

const order = ref<OrderDetail | null>(null)
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const msg = ref('')

function formatPrice(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

async function loadOrder() {
  order.value = await getOrder(orderId.value)
  if (order.value.status !== 'pending_payment') {
    await router.replace({ name: 'order-detail', params: { id: String(orderId.value) } })
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await loadOrder()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
})

async function pay(success: boolean) {
  busy.value = true
  error.value = ''
  msg.value = ''
  try {
    order.value = await mockPayOrder(orderId.value, success)
    if (success) {
      msg.value = '支付成功'
      await router.replace({ name: 'order-detail', params: { id: String(orderId.value) } })
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '支付失败'
  } finally {
    busy.value = false
  }
}

function payLater() {
  router.push({
    name: 'orders',
    query: { payLater: '1' },
  })
}

async function onPaymentExpired() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    const o = await getOrder(orderId.value)
    order.value = o
    if (o.status === 'cancelled') {
      await router.replace({ name: 'orders', query: { notice: 'payment_expired' } })
    }
  } catch {
    await router.replace({ name: 'orders', query: { notice: 'payment_expired' } })
  } finally {
    busy.value = false
  }
}

async function cancel() {
  const ok = await showConfirm({
    title: '取消订单',
    message: '确认取消订单？取消后库存将恢复。',
    confirmText: '取消订单',
    variant: 'danger',
  })
  if (!ok) return
  busy.value = true
  error.value = ''
  try {
    await cancelOrder(orderId.value)
    await router.replace({ name: 'orders' })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '取消失败'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="wrap page-narrow">
    <p class="eyebrow ds-label-caps">Payment</p>
    <h1 class="title">模拟支付</h1>
    <p class="lede">
      教学环境演示：可选择支付成功或失败，不产生真实扣款。请在
      <strong>{{ PAYMENT_TIMEOUT_MINUTES }} 分钟</strong>内完成付款，超时订单将自动取消。
    </p>

    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error && !order" class="ds-form-error">{{ error }}</p>

    <template v-else-if="order">
      <OrderPaymentCountdown
        :created-at="order.created_at"
        :payment-expires-at="order.payment_expires_at"
        @expired="onPaymentExpired"
      />

      <div class="card">
        <p class="card__t">{{ order.product_title }}</p>
        <p class="card__m">
          {{ ORDER_STATUS_LABELS[order.status] ?? order.status }} ·
          {{ TRADE_LABELS[order.trade_type] ?? order.trade_type }} · ×{{ order.quantity }}
        </p>
        <p class="card__p">应付 ¥ {{ formatPrice(order.amount) }}</p>
      </div>

      <p v-if="error" class="ds-form-error">{{ error }}</p>
      <p v-if="msg" class="msg">{{ msg }}</p>

      <div class="actions">
        <button type="button" class="ds-btn" :disabled="busy" @click="pay(true)">模拟支付成功</button>
        <button type="button" class="ds-btn" :disabled="busy" @click="pay(false)">模拟支付失败</button>
        <button type="button" class="ds-btn ds-btn--ghost" :disabled="busy" @click="payLater">稍后支付</button>
        <button type="button" class="link-btn ds-label-caps" :disabled="busy" @click="cancel">取消订单</button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.wrap {
  padding-top: var(--space-section);
  padding-bottom: var(--space-section);
}

.eyebrow {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.title {
  margin: 0 0 var(--space-sm);
  font-size: clamp(26px, 3.5vw, 36px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.lede {
  margin: 0 0 var(--space-xl);
  font-size: 16px;
  font-weight: 300;
  color: var(--color-body);
}

.lede strong {
  font-weight: 600;
  color: var(--color-body-strong);
}

.muted {
  color: var(--color-muted);
}

.card {
  border: 1px solid var(--color-hairline);
  padding: var(--space-lg);
  background: var(--color-surface-card);
  margin-bottom: var(--space-xl);
}

.card__t {
  margin: 0 0 var(--space-sm);
  font-weight: 700;
  color: var(--color-on-dark);
}

.card__m {
  margin: 0 0 var(--space-sm);
  font-size: 14px;
  font-weight: 300;
  color: var(--color-body);
}

.card__p {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.msg {
  color: var(--color-success);
  font-size: 14px;
  margin: 0 0 var(--space-md);
}

.actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  align-items: flex-start;
}

.link-btn {
  background: none;
  border: none;
  color: var(--color-body);
  cursor: pointer;
  padding: 0;
}
</style>
