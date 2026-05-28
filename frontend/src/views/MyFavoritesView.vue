<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listFavoriteProducts, unfavoriteProduct } from '../api/products'
import { showConfirm } from '../composables/useConfirm'
import { CONDITION_LABELS, STATUS_LABELS, TRADE_LABELS } from '../constants/productLabels'
import type { ProductFavoriteItem } from '../types/product'

const items = ref<ProductFavoriteItem[]>([])
const loading = ref(true)
const error = ref('')
const busyId = ref<number | null>(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await listFavoriteProducts()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function formatPrice(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function isPurchasable(status: string, stock: number) {
  return status === 'approved' && stock > 0
}

function statusLabel(status: string) {
  return STATUS_LABELS[status] ?? status
}

async function removeFavorite(id: number) {
  const ok = await showConfirm({
    title: '取消收藏',
    message: '确定从收藏中移除该商品？',
    confirmText: '取消收藏',
    variant: 'danger',
  })
  if (!ok) return

  busyId.value = id
  error.value = ''
  try {
    await unfavoriteProduct(id)
    items.value = items.value.filter((item) => item.product.id !== id)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <section class="wrap">
    <header class="head">
      <p class="eyebrow ds-label-caps">Favorites</p>
      <h1 class="title">我的收藏</h1>
      <p class="lede">集中查看感兴趣的商品，便于后续比较和下单。</p>
    </header>

    <p v-if="error" class="ds-form-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-else class="grid">
      <article
        v-for="item in items"
        :key="item.product.id"
        class="card ds-hover-card"
        :class="{ 'card--muted': !isPurchasable(item.product.status, item.product.stock) }"
      >
        <RouterLink class="card__link" :to="`/products/${item.product.id}`">
          <div class="card__media ds-hover-card__media">
            <img v-if="item.product.cover_image" :src="item.product.cover_image" :alt="item.product.title" />
            <div v-else class="card__ph" aria-hidden="true" />
            <span v-if="item.product.is_hot" class="pill ds-label-caps">Hot</span>
            <span
              v-if="!isPurchasable(item.product.status, item.product.stock)"
              class="pill pill--status ds-label-caps"
            >
              {{ statusLabel(item.product.status) }}{{ item.product.stock <= 0 ? ' · 无库存' : '' }}
            </span>
          </div>
          <div class="card__body">
            <p class="card__cat">{{ item.product.category_name }}</p>
            <h2 class="card__title">{{ item.product.title }}</h2>
            <p class="card__meta">
              {{ CONDITION_LABELS[item.product.condition] ?? item.product.condition }} ·
              {{ TRADE_LABELS[item.product.trade_type] ?? item.product.trade_type }}
            </p>
            <p
              v-if="!isPurchasable(item.product.status, item.product.stock)"
              class="card__hint"
            >
              暂不可购买，可查看详情或取消收藏
            </p>
            <p class="card__price ds-hover-card__price">¥ {{ formatPrice(item.product.price) }}</p>
          </div>
        </RouterLink>
        <button
          type="button"
          class="remove-btn ds-label-caps"
          :disabled="busyId === item.product.id"
          @click="removeFavorite(item.product.id)"
        >
          取消收藏
        </button>
      </article>
      <p v-if="!items.length" class="muted">暂无收藏商品</p>
    </div>
  </section>
</template>

<style scoped>
.wrap {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-xxl) var(--space-lg) var(--space-section);
}

.head {
  margin-bottom: var(--space-xl);
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

.lede,
.muted {
  color: var(--color-body);
  font-weight: 300;
}

.grid {
  display: grid;
  gap: var(--space-lg);
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

.card {
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-card);
  display: flex;
  flex-direction: column;
}

.card--muted {
  opacity: 0.88;
}

.card--muted .card__media img {
  filter: grayscale(0.15);
}

.card__link {
  color: inherit;
  text-decoration: none;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.card__media {
  position: relative;
  aspect-ratio: 16 / 10;
  background: var(--color-surface-soft);
}

.card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.card__ph {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--color-surface-soft), var(--color-carbon-gray));
}

.pill {
  position: absolute;
  top: var(--space-sm);
  left: var(--space-sm);
  padding: 4px 8px;
  background: var(--color-canvas);
  color: var(--color-on-dark);
  border: 1px solid var(--color-hairline);
  font-size: 11px;
}

.pill--status {
  left: auto;
  right: var(--space-sm);
  background: var(--color-surface-soft);
  color: var(--color-body);
}

.card__hint {
  margin: 0;
  font-size: 13px;
  color: var(--color-muted);
}

.card__body {
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  flex: 1;
}

.card__cat {
  margin: 0;
  font-size: 12px;
  color: var(--color-muted);
}

.card__title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-dark);
  line-height: 1.35;
}

.card__meta {
  margin: 0;
  font-size: 14px;
  font-weight: 300;
  color: var(--color-body);
}

.card__price {
  margin: auto 0 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.remove-btn {
  margin: 0 var(--space-lg) var(--space-lg);
  padding: 8px 0;
  border: none;
  background: transparent;
  color: var(--color-muted);
  cursor: pointer;
  text-align: left;
}

.remove-btn:hover {
  color: var(--color-on-dark);
}
</style>
