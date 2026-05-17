<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import OrderPaymentCountdown from '../components/OrderPaymentCountdown.vue'
import { listBuyerOrders, listSellerOrders } from '../api/orders'
import type { OrderListItem } from '../types/order'
import { ORDER_STATUS_LABELS } from '../constants/orderLabels'
import { TRADE_LABELS } from '../constants/productLabels'

const route = useRoute()
const router = useRouter()

const role = ref<'buy' | 'sell'>('buy')
const tab = ref('')
const items = ref<OrderListItem[]>([])
const loading = ref(true)
const error = ref('')
const banner = ref('')

const showPayLaterHint = computed(() => route.query.payLater === '1')
const showExpiredNotice = computed(() => route.query.notice === 'payment_expired')

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value =
      role.value === 'buy'
        ? await listBuyerOrders(tab.value || undefined)
        : await listSellerOrders(tab.value || undefined)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function clearQueryFlags() {
  if (!route.query.payLater && !route.query.notice) return
  const q = { ...route.query }
  delete q.payLater
  delete q.notice
  router.replace({ query: q })
}

function onPaymentExpired() {
  banner.value = '订单付款超时，已自动取消'
  void load()
  clearQueryFlags()
}

onMounted(() => {
  if (showPayLaterHint.value) {
    banner.value = '订单已保留，请在 30 分钟内于「待付款」中完成支付'
    clearQueryFlags()
  } else if (showExpiredNotice.value) {
    banner.value = '订单付款超时，已自动取消'
    clearQueryFlags()
  }
  void load()
})

watch([role, tab], () => {
  void load()
})

function formatPrice(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function payLink(id: number) {
  return { name: 'order-pay' as const, params: { id: String(id) } }
}
</script>

<template>
  <section class="wrap">
    <header class="head">
      <p class="eyebrow ds-label-caps">Orders</p>
      <h1 class="title">我的订单</h1>
    </header>

    <p v-if="banner" class="banner">{{ banner }}</p>

    <div class="role-tabs">
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': role === 'buy', 'ds-hover-tab--on': role === 'buy' }" @click="role = 'buy'">
        我买到的
      </button>
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': role === 'sell', 'ds-hover-tab--on': role === 'sell' }" @click="role = 'sell'">
        我卖出的
      </button>
    </div>

    <div class="tabs">
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': tab === '', 'ds-hover-tab--on': tab === '' }" @click="tab = ''">全部</button>
      <button
        type="button"
        class="tab ds-hover-tab"
        :class="{ 'tab--on': tab === 'pending_payment', 'ds-hover-tab--on': tab === 'pending_payment' }"
        @click="tab = 'pending_payment'"
      >
        待付款
      </button>
      <button
        type="button"
        class="tab ds-hover-tab"
        :class="{ 'tab--on': tab === 'pending_fulfillment', 'ds-hover-tab--on': tab === 'pending_fulfillment' }"
        @click="tab = 'pending_fulfillment'"
      >
        待履约
      </button>
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': tab === 'completed', 'ds-hover-tab--on': tab === 'completed' }" @click="tab = 'completed'">
        已完成
      </button>
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': tab === 'cancelled', 'ds-hover-tab--on': tab === 'cancelled' }" @click="tab = 'cancelled'">
        已取消
      </button>
    </div>

    <p v-if="error" class="ds-form-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-else class="list">
      <article v-for="o in items" :key="o.id" class="row-wrap">
        <RouterLink class="row ds-hover-row ds-hover-row--flex" :to="`/orders/${o.id}`">
          <div v-if="o.cover_image" class="row__img ds-hover-row__img">
            <img :src="o.cover_image" alt="" />
          </div>
          <div v-else class="row__img row__img--ph" />
          <div class="row__body">
            <p class="row__title">{{ o.product_title }}</p>
            <p class="row__meta">
              {{ ORDER_STATUS_LABELS[o.status] ?? o.status }} ·
              {{ role === 'buy' ? '卖家' : '买家' }} {{ o.counterparty_nickname }} ·
              {{ TRADE_LABELS[o.trade_type] ?? o.trade_type }}
            </p>
            <p class="row__price">¥ {{ formatPrice(o.amount) }} · ×{{ o.quantity }}</p>
            <OrderPaymentCountdown
              v-if="role === 'buy' && o.status === 'pending_payment'"
              compact
              :created-at="o.created_at"
              :payment-expires-at="o.payment_expires_at"
              @expired="onPaymentExpired"
            />
          </div>
        </RouterLink>
        <RouterLink
          v-if="role === 'buy' && o.status === 'pending_payment'"
          class="row__pay ds-btn ds-btn--ghost"
          :to="payLink(o.id)"
          @click.stop
        >
          去支付
        </RouterLink>
      </article>
      <p v-if="!items.length" class="muted">暂无订单</p>
    </div>
  </section>
</template>

<style scoped>
.wrap {
  max-width: 900px;
  margin: 0 auto;
  padding: var(--space-xxl) var(--space-lg) var(--space-section);
}

.head {
  margin-bottom: var(--space-lg);
}

.banner {
  margin: 0 0 var(--space-lg);
  padding: var(--space-sm) var(--space-md);
  font-size: 14px;
  color: var(--color-body-strong);
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-hairline);
}

.eyebrow {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.title {
  margin: 0;
  font-size: clamp(26px, 3.5vw, 36px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.role-tabs {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-xl);
}

.tab {
  border: 1px solid var(--color-hairline);
  background: transparent;
  color: var(--color-body);
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
}

.tab--on {
  color: var(--color-on-dark);
  border-color: var(--color-on-dark);
}

.muted {
  color: var(--color-muted);
  font-weight: 300;
}

.list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.row-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.row {
  display: flex;
  gap: var(--space-md);
  border: 1px solid var(--color-hairline);
  padding: var(--space-md);
  background: var(--color-surface-card);
  text-decoration: none;
  color: inherit;
}

.row__pay {
  align-self: flex-start;
  margin-left: var(--space-md);
  text-decoration: none;
  font-size: 13px;
  padding: 6px 14px;
}

.row__img {
  width: 96px;
  height: 72px;
  flex-shrink: 0;
  background: var(--color-surface-soft);
}

.row__img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.row__img--ph {
  background: linear-gradient(135deg, var(--color-surface-soft), var(--color-carbon-gray));
}

.row__title {
  margin: 0 0 var(--space-xs);
  font-weight: 700;
  color: var(--color-on-dark);
}

.row__meta {
  margin: 0 0 var(--space-xs);
  font-size: 13px;
  font-weight: 300;
  color: var(--color-body);
}

.row__price {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-on-dark);
}
</style>
