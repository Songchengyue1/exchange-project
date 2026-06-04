<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { aiSearch } from '../api/ai'
import { listProducts } from '../api/products'
import type { ProductListItem } from '../types/product'
import type { AISearchMode } from '../types/ai'
import { CONDITION_LABELS, TRADE_LABELS } from '../constants/productLabels'

const route = useRoute()
const router = useRouter()

const page = ref(Number(route.query.page) > 0 ? Number(route.query.page) : 1)
const pageSize = 12
const items = ref<ProductListItem[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref('')
const aiMode = ref<AISearchMode | null>(null)
const searchInput = ref('')

const categoryId = computed(() => {
  const raw = route.query.category
  if (raw == null || raw === '') return undefined
  const n = Number(raw)
  return Number.isFinite(n) ? n : undefined
})

const q = computed(() => (typeof route.query.q === 'string' ? route.query.q : '') || '')

const sort = computed(() =>
  typeof route.query.sort === 'string' && route.query.sort ? route.query.sort : 'created_at_desc',
)

async function load() {
  loading.value = true
  error.value = ''
  aiMode.value = null
  try {
    const res = await listProducts({
      page: page.value,
      page_size: pageSize,
      category_id: categoryId.value,
      q: q.value || undefined,
      sort: sort.value,
    })
    items.value = res.items
    total.value = res.total
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

watch(
  () => route.fullPath,
  () => {
    page.value = Number(route.query.page) > 0 ? Number(route.query.page) : 1
    if (route.query.ai === '1' && q.value) {
      void runAiSearch()
    } else {
      void load()
    }
  },
)

function setQuery(partial: Record<string, string | number | undefined>) {
  const next = { ...route.query, ...partial }
  Object.keys(next).forEach((k) => {
    const v = next[k]
    if (v === '' || v === undefined) delete next[k]
  })
  void router.push({ path: '/products', query: next as Record<string, string> })
}

function formatPrice(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

async function runAiSearch() {
  const query = searchInput.value.trim()
  if (!query) return
  loading.value = true
  error.value = ''
  try {
    const res = await aiSearch(query, page.value, pageSize)
    items.value = res.items
    total.value = res.total
    aiMode.value = res.mode
    void router.push({ path: '/products', query: { q: query, ai: '1', page: String(page.value) } })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '智能搜索失败'
  } finally {
    loading.value = false
  }
}

watch(
  () => q.value,
  (v) => {
    searchInput.value = v
  },
  { immediate: true },
)
</script>

<template>
  <section class="wrap">
    <header class="head">
      <p class="eyebrow ds-label-caps">Marketplace</p>
      <h1 class="title">商品列表</h1>
      <p class="lede">支持关键词搜索；也可使用自然语言智能搜索（向量 + 关键词混合）。</p>
    </header>

    <div class="toolbar">
      <input
        v-model="searchInput"
        class="ds-input toolbar__search"
        type="search"
        placeholder="搜索或描述需求，如：两千以内的二手手机…"
        @keydown.enter="route.query.ai === '1' ? runAiSearch() : setQuery({ q: searchInput, page: 1 })"
      />
      <button type="button" class="ds-btn toolbar__ai" @click="runAiSearch">智能搜索</button>
      <select class="ds-input toolbar__sort" :value="sort" @change="setQuery({ sort: ($event.target as HTMLSelectElement).value, page: 1 })">
        <option value="created_at_desc">最新上架</option>
        <option value="price_asc">价格从低到高</option>
        <option value="price_desc">价格从高到低</option>
      </select>
    </div>

    <p v-if="aiMode" class="ai-badge ds-label-caps">检索模式：{{ aiMode }}</p>
    <p v-if="error" class="ds-form-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-else class="grid">
      <RouterLink v-for="p in items" :key="p.id" class="card ds-hover-card" :to="`/products/${p.id}`">
        <div class="card__media ds-hover-card__media">
          <img v-if="p.cover_image" :src="p.cover_image" :alt="p.title" />
          <div v-else class="card__ph" aria-hidden="true" />
          <span v-if="p.is_hot" class="pill ds-label-caps">Hot</span>
        </div>
        <div class="card__body">
          <p class="card__cat">{{ p.category_name }}</p>
          <h2 class="card__title">{{ p.title }}</h2>
          <p class="card__meta">
            {{ CONDITION_LABELS[p.condition] ?? p.condition }} · {{ TRADE_LABELS[p.trade_type] ?? p.trade_type }}
          </p>
          <p class="card__price ds-hover-card__price">¥ {{ formatPrice(p.price) }}</p>
        </div>
      </RouterLink>
    </div>

    <nav v-if="total > pageSize" class="pager">
      <button type="button" class="ds-btn pager__btn" :disabled="page <= 1" @click="setQuery({ page: page - 1 })">
        上一页
      </button>
      <span class="pager__info">第 {{ page }} 页 · 共 {{ Math.ceil(total / pageSize) }} 页</span>
      <button
        type="button"
        class="ds-btn pager__btn"
        :disabled="page >= Math.ceil(total / pageSize)"
        @click="setQuery({ page: page + 1 })"
      >
        下一页
      </button>
    </nav>
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
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.lede {
  margin: 0;
  max-width: 60ch;
  font-size: 16px;
  font-weight: 400;
  color: var(--color-body);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.toolbar__search {
  flex: 1 1 240px;
}

.toolbar__ai {
  height: 48px;
  padding: 0 16px;
  flex-shrink: 0;
}

.toolbar__sort {
  width: 200px;
}

.ai-badge {
  margin: 0 0 var(--space-md);
  font-size: 12px;
  color: var(--color-muted);
}

.muted {
  color: var(--color-muted);
  font-weight: 400;
}

.grid {
  display: grid;
  gap: var(--space-lg);
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

.card {
  text-decoration: none;
  color: inherit;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-card);
  display: flex;
  flex-direction: column;
  min-height: 100%;
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
  letter-spacing: 0.5px;
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
  font-weight: 400;
  color: var(--color-body);
}

.card__price {
  margin: auto 0 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
  margin-top: var(--space-xl);
}

.pager__btn {
  height: 40px;
  padding: 0 16px;
}

.pager__info {
  font-size: 14px;
  font-weight: 400;
  color: var(--color-body);
}
</style>
