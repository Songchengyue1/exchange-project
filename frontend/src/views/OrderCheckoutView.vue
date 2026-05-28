<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { createOrder } from '../api/orders'
import { getProduct } from '../api/products'
import AddressSelector from '../components/AddressSelector.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useAuthStore } from '../stores/auth'
import type { ProductDetail } from '../types/product'
import { CONDITION_LABELS, TRADE_LABELS } from '../constants/productLabels'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const productId = computed(() => Number(route.params.productId))

const product = ref<ProductDetail | null>(null)
const quantity = ref(1)
const remark = ref('')
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const selectedAddressId = ref<number | null>(null)
const addressSelectorRef = ref<InstanceType<typeof AddressSelector> | null>(null)

const CHECKOUT_STEPS = [
  { n: 1, label: '提交订单' },
  { n: 2, label: '模拟支付' },
  { n: 3, label: '卖家履约' },
  { n: 4, label: '买家确认' },
]

function formatPrice(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

const total = computed(() => {
  if (!product.value) return 0
  return Math.round(product.value.price * quantity.value * 100) / 100
})

const coverImage = computed(() => {
  const imgs = product.value?.images
  if (!imgs?.length) return null
  const sorted = [...imgs].sort((a, b) => a.sort_order - b.sort_order)
  return sorted[0]?.path ?? null
})

const tradeLabel = computed(() => {
  if (!product.value) return ''
  return TRADE_LABELS[product.value.trade_type] ?? product.value.trade_type
})

const fulfillmentTips = computed(() => {
  const t = product.value?.trade_type
  if (t === 'pickup') {
    return [
      '本单为自提：支付成功后请主动联系卖家，约定见面时间与地点。',
      '卖家确认交付后再确认收货；如有问题可在订单内申请退款。',
    ]
  }
  if (t === 'shipping') {
    return [
      '本单为邮寄：请确认下方收货信息准确，支付后由卖家安排发货。',
      '运费、快递公司与发货时效请与卖家在备注或私信中确认（平台不代收运费）。',
    ]
  }
  return [
    '本单支持自提或邮寄：支付成功后请与卖家确认具体履约方式。',
    '邮寄请核对收货地址；自提请约定见面地点并当面验货。',
  ]
})

const needsShippingAddress = computed(() => {
  const t = product.value?.trade_type
  return t === 'shipping' || t === 'both'
})

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    if (auth.token && !auth.user) {
      await auth.hydrate()
    }
    product.value = await getProduct(productId.value)
    if (product.value.status !== 'approved' || product.value.stock < 1) {
      error.value = '商品当前不可购买'
    }
    const saved = localStorage.getItem('checkout_address_id')
    if (saved) {
      const n = Number(saved)
      if (Number.isFinite(n) && n > 0) selectedAddressId.value = n
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
})

async function submit() {
  if (!product.value) return
  if (needsShippingAddress.value && !addressSelectorRef.value?.validate()) {
    return
  }
  error.value = ''
  submitting.value = true
  try {
    const order = await createOrder({
      product_id: product.value.id,
      quantity: quantity.value,
      remark: remark.value.trim() || undefined,
      shipping_address_id: needsShippingAddress.value ? selectedAddressId.value ?? undefined : undefined,
    })
    await router.replace({ name: 'order-pay', params: { id: String(order.id) } })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '下单失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="wrap page-checkout">
    <p class="eyebrow ds-label-caps">Checkout</p>
    <h1 class="title">确认订单</h1>

    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error && !product" class="ds-form-error">{{ error }}</p>

    <div v-else-if="product" class="checkout-grid">
      <div class="checkout-main">
        <section class="panel">
          <h2 class="panel__title ds-label-caps">商品信息</h2>
          <div class="summary__main">
            <div class="summary__media">
              <img v-if="coverImage" :src="coverImage" :alt="product.title" class="summary__img" />
              <div v-else class="summary__ph" aria-hidden="true" />
            </div>
            <div class="summary__body">
              <RouterLink class="summary__title" :to="`/products/${product.id}`">
                {{ product.title }}
              </RouterLink>
              <p class="summary__price">¥ {{ formatPrice(product.price) }}</p>
              <ul class="summary__specs">
                <li><span class="k">分类</span>{{ product.category_name }}</li>
                <li>
                  <span class="k">成色</span>{{ CONDITION_LABELS[product.condition] ?? product.condition }}
                </li>
                <li><span class="k">交易方式</span>{{ tradeLabel }}</li>
                <li><span class="k">库存</span>{{ product.stock }}</li>
              </ul>
              <div class="summary__seller">
                <UserAvatar
                  :src="product.seller.avatar_url"
                  :name="product.seller.nickname"
                  size="sm"
                />
                <span class="summary__seller-name">{{ product.seller.nickname }}</span>
                <span v-if="product.seller.rating_avg != null" class="summary__seller-rate">
                  信誉 {{ product.seller.rating_avg.toFixed(1) }}
                </span>
              </div>
              <p v-if="product.description" class="summary__desc">{{ product.description }}</p>
            </div>
          </div>
        </section>

        <section v-if="needsShippingAddress" class="panel">
          <AddressSelector
            ref="addressSelectorRef"
            v-model="selectedAddressId"
            :require-address="needsShippingAddress"
          />
        </section>
        <section v-else class="panel">
          <h2 class="panel__title ds-label-caps">联系信息</h2>
          <p class="muted">本单为自提，无需填写收货地址；支付后请与卖家约定见面地点。</p>
          <p v-if="auth.user?.phone" class="contact-line">联系电话：{{ auth.user.phone }}</p>
        </section>

        <section class="panel">
          <h2 class="panel__title ds-label-caps">履约说明</h2>
          <p class="panel__badge">交易方式：{{ tradeLabel }}</p>
          <ul class="tip-list">
            <li v-for="(tip, i) in fulfillmentTips" :key="i">{{ tip }}</li>
          </ul>
        </section>

        <section class="panel">
          <h2 class="panel__title ds-label-caps">给卖家留言</h2>
          <div class="ds-field">
            <label class="ds-label" for="rmk">订单备注（可选）</label>
            <textarea
              id="rmk"
              v-model="remark"
              class="ds-textarea"
              maxlength="500"
              placeholder="如：希望周末自提、请发顺丰到付等"
            />
          </div>
        </section>
      </div>

      <aside class="checkout-aside">
        <form class="panel panel--sticky" @submit.prevent="submit">
          <h2 class="panel__title ds-label-caps">订单明细</h2>

          <ol class="steps">
            <li v-for="s in CHECKOUT_STEPS" :key="s.n" class="steps__item">
              <span class="steps__n">{{ s.n }}</span>
              <span class="steps__label">{{ s.label }}</span>
            </li>
          </ol>

          <div class="ds-field">
            <label class="ds-label" for="qty">购买数量</label>
            <input
              id="qty"
              v-model.number="quantity"
              class="ds-input"
              type="number"
              min="1"
              :max="product.stock"
              required
            />
          </div>

          <dl class="bill">
            <div class="bill__row">
              <dt>商品单价</dt>
              <dd>¥ {{ formatPrice(product.price) }}</dd>
            </div>
            <div class="bill__row">
              <dt>数量</dt>
              <dd>× {{ quantity }}</dd>
            </div>
            <div class="bill__row">
              <dt>运费</dt>
              <dd class="bill__muted">与卖家协商 / 自理</dd>
            </div>
            <div class="bill__row bill__row--total">
              <dt>应付合计</dt>
              <dd class="bill__total">¥ {{ formatPrice(total) }}</dd>
            </div>
          </dl>

          <p v-if="error" class="ds-form-error">{{ error }}</p>

          <button type="submit" class="ds-btn submit-btn" :disabled="submitting || product.stock < 1">
            {{ submitting ? '提交中…' : '提交订单' }}
          </button>

          <ul class="guarantee">
            <li>提交后将进入<strong>模拟支付</strong>页，仅用于演示，非真实扣款。</li>
            <li>支付成功后订单为「待卖家履约」，请等待卖家确认发货或交付。</li>
            <li>卖家履约后再确认收货；问题可申请退款由管理员审核。</li>
          </ul>
        </form>
      </aside>
    </div>
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
  font-weight: 300;
  font-size: 14px;
}

.page-checkout {
  max-width: var(--content-max);
  margin: 0 auto;
  padding-left: var(--space-lg);
  padding-right: var(--space-lg);
}

.checkout-grid {
  display: grid;
  gap: var(--space-xl);
  align-items: start;
}

@media (min-width: 900px) {
  .checkout-grid {
    grid-template-columns: minmax(0, 1fr) minmax(300px, 360px);
  }
}

.panel {
  border: 1px solid var(--color-hairline);
  padding: var(--space-lg);
  background: var(--color-surface-card);
  margin-bottom: var(--space-lg);
}

.panel--sticky {
  margin-bottom: 0;
}

@media (min-width: 900px) {
  .panel--sticky {
    position: sticky;
    top: calc(64px + var(--space-lg));
  }
}

.panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.panel__title {
  margin: 0 0 var(--space-md);
  font-size: 12px;
  color: var(--color-muted);
}

.panel__head .panel__title {
  margin-bottom: 0;
}

.panel__link {
  font-size: 13px;
  color: var(--color-body-strong);
  text-decoration: none;
}

.panel__link:hover {
  color: var(--color-on-dark);
  text-decoration: underline;
}

.panel__hint {
  margin: 0 0 var(--space-md);
  padding: var(--space-sm) var(--space-md);
  font-size: 13px;
  color: var(--color-body);
  background: rgba(226, 39, 24, 0.08);
  border: 1px solid rgba(226, 39, 24, 0.25);
}

.panel__badge {
  margin: 0 0 var(--space-sm);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-on-dark);
}

.summary__main {
  display: flex;
  gap: var(--space-lg);
  align-items: flex-start;
}

.summary__media {
  flex-shrink: 0;
  width: 120px;
  aspect-ratio: 1;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
  overflow: hidden;
}

.summary__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.summary__ph {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--color-surface-soft), var(--color-carbon-gray));
}

.summary__body {
  flex: 1;
  min-width: 0;
}

.summary__title {
  display: inline-block;
  margin: 0 0 var(--space-xs);
  font-weight: 700;
  font-size: 17px;
  color: var(--color-on-dark);
  text-decoration: none;
}

.summary__title:hover {
  color: var(--color-body-strong);
}

.summary__price {
  margin: 0 0 var(--space-sm);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.summary__specs {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-sm);
  font-size: 13px;
  font-weight: 300;
  color: var(--color-body);
}

.summary__specs li {
  display: flex;
  gap: var(--space-sm);
  padding: 2px 0;
}

.summary__specs .k {
  width: 56px;
  flex-shrink: 0;
  color: var(--color-muted);
}

.summary__seller {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-hairline);
}

.summary__seller-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-on-dark);
}

.summary__seller-rate {
  font-size: 13px;
  color: var(--color-muted);
  margin-left: auto;
}

.summary__desc {
  margin: var(--space-sm) 0 0;
  font-size: 13px;
  font-weight: 300;
  line-height: 1.5;
  color: var(--color-body);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 14px;
  font-weight: 300;
  color: var(--color-body);
}

.info-list li {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-hairline);
}

.info-list li:last-child {
  border-bottom: none;
}

.info-list .k {
  width: 72px;
  flex-shrink: 0;
  color: var(--color-muted);
}

.info-list__empty {
  color: var(--color-muted);
}

.tip-list {
  margin: 0;
  padding-left: 1.2rem;
  font-size: 14px;
  font-weight: 300;
  line-height: 1.6;
  color: var(--color-body);
}

.tip-list li + li {
  margin-top: var(--space-sm);
}

.contact-line {
  margin: var(--space-sm) 0 0;
  font-size: 14px;
  color: var(--color-body);
}

.steps {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-lg);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.steps__item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-body);
  padding: 4px 10px;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
}

.steps__n {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-on-dark);
  color: var(--color-canvas);
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.bill {
  margin: 0 0 var(--space-lg);
  padding: 0;
}

.bill__row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  font-size: 14px;
  font-weight: 300;
  color: var(--color-body);
  border-bottom: 1px solid var(--color-hairline);
}

.bill__row dt {
  margin: 0;
  color: var(--color-muted);
}

.bill__row dd {
  margin: 0;
  text-align: right;
}

.bill__muted {
  color: var(--color-muted);
  font-size: 13px;
}

.bill__row--total {
  border-bottom: none;
  padding-top: var(--space-md);
}

.bill__total {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.submit-btn {
  width: 100%;
  margin-bottom: var(--space-lg);
}

.guarantee {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 12px;
  font-weight: 300;
  line-height: 1.55;
  color: var(--color-muted);
}

.guarantee li + li {
  margin-top: var(--space-xs);
}

.guarantee strong {
  color: var(--color-body);
  font-weight: 500;
}

@media (max-width: 520px) {
  .summary__main {
    flex-direction: column;
  }

  .summary__media {
    width: 100%;
    max-width: 160px;
  }
}
</style>
