<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { approveProduct, rejectProduct } from '../api/admin'
import { getRecommendations, recordBrowse } from '../api/ai'
import { getProduct } from '../api/products'
import { showConfirm } from '../composables/useConfirm'
import { useAuthStore } from '../stores/auth'
import type { ProductListItem } from '../types/product'
import UserAvatar from '../components/UserAvatar.vue'
import type { ProductDetail } from '../types/product'
import { CONDITION_LABELS, TRADE_LABELS, STATUS_LABELS } from '../constants/productLabels'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const id = computed(() => Number(route.params.id))
const related = ref<ProductListItem[]>([])

const product = ref<ProductDetail | null>(null)
const loading = ref(true)
const error = ref('')
const activeIndex = ref(0)
const rejectReason = ref('')
const reviewBusy = ref(false)
const reviewError = ref('')

const fromAdmin = computed(() => route.query.from === 'admin')
const showAdminReview = computed(
  () => auth.user?.role === 'admin' && product.value?.status === 'pending',
)
const showAdminBack = computed(() => fromAdmin.value || showAdminReview.value)

async function load() {
  loading.value = true
  error.value = ''
  product.value = null
  activeIndex.value = 0
  try {
    product.value = await getProduct(id.value)
    if (auth.token) {
      recordBrowse(id.value).catch(() => {})
    }
    const rec = await getRecommendations(4).catch(() => ({ items: [] as ProductListItem[] }))
    related.value = rec.items.filter((p) => p.id !== id.value).slice(0, 4)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(id, () => {
  void load()
})

const mainImage = computed(() => {
  if (!product.value?.images?.length) return null
  const sorted = [...product.value.images].sort((a, b) => a.sort_order - b.sort_order)
  return sorted[activeIndex.value]?.path ?? sorted[0]?.path
})

function formatPrice(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

async function adminApprove() {
  if (!product.value) return
  const ok = await showConfirm({
    title: '通过审核',
    message: `确定通过「${product.value.title}」并上架？`,
    confirmText: '通过',
  })
  if (!ok) return

  reviewBusy.value = true
  reviewError.value = ''
  try {
    await approveProduct(product.value.id)
    await router.push({ name: 'admin-products' })
  } catch (e) {
    reviewError.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    reviewBusy.value = false
  }
}

async function adminReject() {
  if (!product.value) return
  const reason = rejectReason.value.trim()
  if (!reason) {
    reviewError.value = '请填写驳回原因'
    return
  }
  const ok = await showConfirm({
    title: '驳回商品',
    message: `确定驳回「${product.value.title}」？`,
    confirmText: '驳回',
    variant: 'danger',
  })
  if (!ok) return

  reviewBusy.value = true
  reviewError.value = ''
  try {
    await rejectProduct(product.value.id, reason)
    await router.push({ name: 'admin-products' })
  } catch (e) {
    reviewError.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    reviewBusy.value = false
  }
}
</script>

<template>
  <section class="wrap">
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="ds-form-error">{{ error }}</p>
    <div v-else-if="product" class="layout">
      <div class="gallery">
        <div class="hero">
          <img v-if="mainImage" :src="mainImage" :alt="product.title" class="hero__img" />
          <div v-else class="hero__ph" aria-hidden="true" />
          <span v-if="product.is_hot" class="pill ds-label-caps">Hot</span>
        </div>
        <div v-if="product.images.length" class="thumbs">
          <button
            v-for="(img, idx) in [...product.images].sort((a, b) => a.sort_order - b.sort_order)"
            :key="img.id"
            type="button"
            class="thumb"
            :class="{ 'thumb--active': idx === activeIndex }"
            @click="activeIndex = idx"
          >
            <img :src="img.path" alt="" />
          </button>
        </div>
      </div>

      <aside class="side">
        <p class="eyebrow ds-label-caps">Detail</p>
        <h1 class="title">{{ product.title }}</h1>
        <p class="price">¥ {{ formatPrice(product.price) }}</p>
        <ul class="specs">
          <li><span class="k">分类</span>{{ product.category_name }}</li>
          <li><span class="k">成色</span>{{ CONDITION_LABELS[product.condition] ?? product.condition }}</li>
          <li><span class="k">交易方式</span>{{ TRADE_LABELS[product.trade_type] ?? product.trade_type }}</li>
          <li><span class="k">库存</span>{{ product.stock }}</li>
          <li><span class="k">状态</span>{{ STATUS_LABELS[product.status] ?? product.status }}</li>
        </ul>
        <p v-if="product.reject_reason" class="reject">驳回原因：{{ product.reject_reason }}</p>

        <div class="seller">
          <p class="ds-label-caps seller__label">Seller</p>
          <div class="seller__row">
            <UserAvatar
              :src="product.seller.avatar_url"
              :name="product.seller.nickname"
              size="md"
            />
            <div>
              <p class="seller__name">{{ product.seller.nickname }}</p>
              <p class="seller__rate">
                信誉分：
                {{
                  product.seller.rating_avg != null ? product.seller.rating_avg.toFixed(1) : '暂无'
                }}
              </p>
            </div>
          </div>
        </div>

        <p class="desc">{{ product.description }}</p>

        <div v-if="showAdminBack" class="admin-bar">
          <RouterLink :to="{ name: 'admin-products' }" class="admin-bar__back ds-label-caps">
            ← 返回审核列表
          </RouterLink>
        </div>

        <div v-if="showAdminReview" class="admin-review">
          <p class="admin-review__label ds-label-caps">管理员审核</p>
          <p v-if="reviewError" class="ds-form-error">{{ reviewError }}</p>
          <input
            v-model="rejectReason"
            class="ds-input"
            type="text"
            placeholder="驳回原因（驳回时必填）"
            :disabled="reviewBusy"
          />
          <div class="admin-review__actions">
            <button type="button" class="ds-btn" :disabled="reviewBusy" @click="adminApprove">
              {{ reviewBusy ? '处理中…' : '通过审核' }}
            </button>
            <button
              type="button"
              class="ds-btn ds-btn--ghost"
              :disabled="reviewBusy"
              @click="adminReject"
            >
              驳回
            </button>
          </div>
        </div>

        <RouterLink
          v-if="product.status === 'approved' && product.stock > 0"
          class="ds-btn buy"
          :to="{ name: 'order-checkout', params: { productId: String(product.id) } }"
        >
          立即购买
        </RouterLink>
        <p v-else class="buy-muted">当前不可购买</p>

        <div v-if="related.length" class="related">
          <p class="ds-label-caps related__label">猜你喜欢</p>
          <ul class="related__list">
            <li v-for="p in related" :key="p.id">
              <RouterLink class="related__link" :to="`/products/${p.id}`">
                <span class="related__title">{{ p.title }}</span>
                <span class="related__price">¥ {{ formatPrice(p.price) }}</span>
              </RouterLink>
            </li>
          </ul>
        </div>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.wrap {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-xxl) var(--space-lg) var(--space-section);
}

.muted {
  color: var(--color-muted);
}

.layout {
  display: grid;
  gap: var(--space-xl);
  grid-template-columns: 1fr;
}

@media (min-width: 960px) {
  .layout {
    grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
    align-items: start;
  }
}

.gallery {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.hero {
  position: relative;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
  aspect-ratio: 16 / 10;
}

.hero__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.hero__ph {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--color-surface-soft), var(--color-carbon-gray));
}

.pill {
  position: absolute;
  top: var(--space-md);
  left: var(--space-md);
  padding: 4px 10px;
  background: var(--color-canvas);
  color: var(--color-on-dark);
  border: 1px solid var(--color-hairline);
  font-size: 11px;
}

.thumbs {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.thumb {
  padding: 0;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-card);
  width: 72px;
  height: 72px;
  cursor: pointer;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.thumb--active {
  outline: 2px solid var(--color-on-dark);
  outline-offset: 0;
}

.side {
  border: 1px solid var(--color-hairline);
  padding: var(--space-xl);
  background: var(--color-surface-card);
}

.eyebrow {
  margin: 0 0 var(--space-sm);
  color: var(--color-muted);
}

.title {
  margin: 0 0 var(--space-md);
  font-size: clamp(22px, 3vw, 32px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.price {
  margin: 0 0 var(--space-lg);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.specs {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-lg);
  border-top: 1px solid var(--color-hairline);
}

.specs li {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-hairline);
  font-size: 14px;
  font-weight: 300;
  color: var(--color-body);
}

.k {
  width: 88px;
  flex-shrink: 0;
  color: var(--color-muted);
}

.reject {
  margin: 0 0 var(--space-lg);
  font-size: 14px;
  font-weight: 300;
  color: var(--color-m-red);
}

.seller {
  margin-bottom: var(--space-lg);
  padding: var(--space-md) 0;
  border-top: 1px solid var(--color-hairline);
}

.seller__label {
  margin: 0 0 var(--space-sm);
  color: var(--color-muted);
}

.seller__row {
  display: flex;
  gap: var(--space-md);
  align-items: center;
}

.seller__name {
  margin: 0;
  font-weight: 700;
  color: var(--color-on-dark);
}

.seller__rate {
  margin: 4px 0 0;
  font-size: 13px;
  font-weight: 300;
  color: var(--color-body);
}

.desc {
  margin: 0 0 var(--space-xl);
  white-space: pre-wrap;
  line-height: 1.6;
  font-weight: 300;
  color: var(--color-body);
}

.buy {
  text-decoration: none;
  display: inline-flex;
  justify-content: center;
  width: 100%;
  box-sizing: border-box;
}

.related {
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-hairline);
}

.related__label {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.related__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.related__link {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  text-decoration: none;
  border-bottom: 1px solid var(--color-hairline);
  color: var(--color-on-dark);
  font-size: 14px;
}

.related__link:hover {
  color: var(--color-body-strong);
}

.related__title {
  flex: 1;
  font-weight: 400;
}

.related__price {
  font-weight: 700;
  flex-shrink: 0;
}

.buy-muted {
  margin: 0;
  font-size: 14px;
  color: var(--color-muted);
  font-weight: 300;
}

.admin-bar {
  margin-bottom: var(--space-md);
}

.admin-bar__back {
  display: inline-flex;
  font-size: 13px;
  color: var(--color-body-strong);
  text-decoration: none;
  transition: color var(--duration-fast) ease;
}

.admin-bar__back:hover {
  color: var(--color-on-dark);
}

.admin-review {
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
}

.admin-review__label {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.admin-review__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.admin-review .ds-input {
  width: 100%;
  box-sizing: border-box;
}
</style>
