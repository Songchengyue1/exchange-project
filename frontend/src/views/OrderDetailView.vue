<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cancelOrder, confirmReceipt, fulfillOrder, getOrder, requestRefund } from '../api/orders'
import OrderPaymentCountdown from '../components/OrderPaymentCountdown.vue'
import ReviewModal from '../components/ReviewModal.vue'
import { showConfirm } from '../composables/useConfirm'
import { useAuthStore } from '../stores/auth'
import type { OrderDetail } from '../types/order'
import { ORDER_STATUS_LABELS } from '../constants/orderLabels'
import { TRADE_LABELS } from '../constants/productLabels'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const orderId = computed(() => Number(route.params.id))

const order = ref<OrderDetail | null>(null)
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const reviewOpen = ref(false)
const refundReason = ref('')
const refundOpen = ref(false)

const isBuyer = computed(() => order.value && auth.user && order.value.buyer.id === auth.user.id)
const isSeller = computed(() => order.value && auth.user && order.value.seller.id === auth.user.id)
const canRequestRefund = computed(
  () => isBuyer.value && ['pending_fulfillment', 'pending_receipt'].includes(order.value?.status ?? ''),
)

function formatPrice(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    order.value = await getOrder(orderId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(orderId, () => {
  void load()
})

async function onConfirmReceipt() {
  const ok = await showConfirm({
    title: '确认收货',
    message: '确认已收到商品？确认后订单将完成，请确保商品无误。',
    confirmText: '确认收货',
  })
  if (!ok) return

  busy.value = true
  error.value = ''
  try {
    order.value = await confirmReceipt(orderId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    busy.value = false
  }
}

async function onFulfill() {
  if (!order.value) return
  const ok = await showConfirm({
    title: order.value.trade_type === 'shipping' ? '确认发货' : '确认履约',
    message:
      order.value.trade_type === 'shipping'
        ? '确认已安排发货？确认后订单将等待买家确认收货。'
        : '确认已完成线下交付或履约？确认后订单将等待买家确认。',
    confirmText: order.value.trade_type === 'shipping' ? '确认发货' : '确认履约',
  })
  if (!ok) return

  busy.value = true
  error.value = ''
  try {
    order.value = await fulfillOrder(orderId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    busy.value = false
  }
}

async function onRequestRefund() {
  const reason = refundReason.value.trim()
  if (!reason) {
    error.value = '请填写退款原因'
    return
  }
  const ok = await showConfirm({
    title: '申请退款',
    message: '提交后需管理员审核，通过后将退款并恢复商品库存。',
    confirmText: '提交申请',
    variant: 'danger',
  })
  if (!ok) return
  busy.value = true
  error.value = ''
  try {
    order.value = await requestRefund(orderId.value, reason)
    refundOpen.value = false
    refundReason.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '申请失败'
  } finally {
    busy.value = false
  }
}

async function cancel() {
  const ok = await showConfirm({
    title: '取消订单',
    message: '确认取消该订单？',
    confirmText: '取消订单',
    variant: 'danger',
  })
  if (!ok) return
  busy.value = true
  try {
    await cancelOrder(orderId.value)
    await router.push({ name: 'orders' })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '取消失败'
  } finally {
    busy.value = false
  }
}

</script>

<template>
  <section class="wrap page-narrow">
    <p class="eyebrow ds-label-caps">Order</p>
    <h1 class="title">订单详情</h1>

    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error && !order" class="ds-form-error">{{ error }}</p>

    <template v-else-if="order">
      <OrderPaymentCountdown
        v-if="isBuyer && order.status === 'pending_payment'"
        :created-at="order.created_at"
        :payment-expires-at="order.payment_expires_at"
        @expired="load"
      />

      <div class="card">
        <div v-if="order.product.cover_image" class="cover">
          <img :src="order.product.cover_image" :alt="order.product_title" />
        </div>
        <p class="card__title">{{ order.product_title }}</p>
        <p class="card__meta">
          订单号 #{{ order.id }} · {{ ORDER_STATUS_LABELS[order.status] ?? order.status }}
        </p>
        <ul class="specs">
          <li><span class="k">金额</span>¥ {{ formatPrice(order.amount) }}</li>
          <li><span class="k">数量</span>×{{ order.quantity }}</li>
          <li><span class="k">交易方式</span>{{ TRADE_LABELS[order.trade_type] ?? order.trade_type }}</li>
          <li><span class="k">买家</span>{{ order.buyer.nickname }}</li>
          <li><span class="k">卖家</span>{{ order.seller.nickname }}</li>
          <li v-if="order.shipping_address_snapshot">
            <span class="k">收货信息</span>{{ order.shipping_address_snapshot }}
          </li>
          <li v-if="order.remark"><span class="k">备注</span>{{ order.remark }}</li>
          <li v-if="order.refund_reason"><span class="k">退款原因</span>{{ order.refund_reason }}</li>
          <li v-if="order.refund_reject_reason">
            <span class="k">退款驳回</span>{{ order.refund_reject_reason }}
          </li>
          <li v-if="order.payment_ref"><span class="k">支付单号</span>{{ order.payment_ref }}</li>
        </ul>
      </div>

      <p v-if="error" class="ds-form-error">{{ error }}</p>

      <div class="actions">
        <RouterLink
          v-if="isBuyer && order.status === 'pending_payment'"
          class="ds-btn pay-link"
          :to="{ name: 'order-pay', params: { id: String(order.id) } }"
        >
          去支付
        </RouterLink>
        <button
          v-if="isSeller && order.status === 'pending_fulfillment'"
          type="button"
          class="ds-btn"
          :disabled="busy"
          @click="onFulfill"
        >
          {{ order.trade_type === 'shipping' ? '确认发货' : '确认履约' }}
        </button>
        <button
          v-if="isBuyer && order.status === 'pending_receipt'"
          type="button"
          class="ds-btn"
          :disabled="busy"
          @click="onConfirmReceipt"
        >
          确认收货
        </button>
        <button
          v-if="canRequestRefund && !refundOpen"
          type="button"
          class="link-btn ds-label-caps"
          :disabled="busy"
          @click="refundOpen = true"
        >
          申请退款
        </button>
        <template v-if="canRequestRefund && refundOpen">
          <input v-model="refundReason" class="ds-input refund-input" placeholder="退款原因（必填）" />
          <button type="button" class="ds-btn" :disabled="busy" @click="onRequestRefund">提交退款申请</button>
          <button type="button" class="link-btn ds-label-caps" :disabled="busy" @click="refundOpen = false">
            取消
          </button>
        </template>
        <button
          v-if="isBuyer && order.status === 'pending_payment'"
          type="button"
          class="link-btn ds-label-caps"
          :disabled="busy"
          @click="cancel"
        >
          取消订单
        </button>
        <button
          v-if="isBuyer && order.status === 'completed' && !order.buyer_has_reviewed"
          type="button"
          class="ds-btn"
          @click="reviewOpen = true"
        >
          评价订单
        </button>
        <RouterLink class="text-link ds-label-caps" :to="`/products/${order.product_id}`">查看商品 →</RouterLink>
      </div>

      <div v-if="order.review" class="review-card">
        <p class="ds-label-caps review-card__label">我的评价</p>
        <p class="review-card__rating">{{ order.review.rating }} 分</p>
        <p v-if="order.review.comment" class="review-card__comment">{{ order.review.comment }}</p>
      </div>
    </template>

    <ReviewModal
      v-if="order"
      :open="reviewOpen"
      :order-id="order.id"
      :product-title="order.product_title"
      @close="reviewOpen = false"
      @submitted="load"
    />
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
  margin: 0 0 var(--space-xl);
  font-size: clamp(26px, 3.5vw, 36px);
  font-weight: 700;
  color: var(--color-on-dark);
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

.cover {
  margin: calc(-1 * var(--space-lg)) calc(-1 * var(--space-lg)) var(--space-lg);
  aspect-ratio: 16 / 9;
  background: var(--color-surface-soft);
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card__title {
  margin: 0 0 var(--space-sm);
  font-weight: 700;
  color: var(--color-on-dark);
}

.card__meta {
  margin: 0 0 var(--space-lg);
  font-size: 14px;
  color: var(--color-body);
  font-weight: 400;
}

.specs {
  list-style: none;
  padding: 0;
  margin: 0;
  border-top: 1px solid var(--color-hairline);
}

.specs li {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-hairline);
  font-size: 14px;
  font-weight: 400;
  color: var(--color-body);
}

.k {
  width: 88px;
  flex-shrink: 0;
  color: var(--color-muted);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  align-items: center;
}

.text-link {
  text-decoration: none;
  color: var(--color-on-dark);
}

.link-btn {
  background: none;
  border: none;
  color: var(--color-body);
  cursor: pointer;
}

.refund-input {
  flex: 1 1 200px;
  min-width: 180px;
}

.pay-link {
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.review-card {
  margin-top: var(--space-lg);
  padding: var(--space-lg);
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
}

.review-card__label {
  margin: 0 0 var(--space-sm);
  color: var(--color-muted);
}

.review-card__rating {
  margin: 0 0 var(--space-xs);
  font-weight: 700;
  color: var(--color-on-dark);
}

.review-card__comment {
  margin: 0;
  font-size: 14px;
  color: var(--color-body);
  line-height: 1.5;
}
</style>
