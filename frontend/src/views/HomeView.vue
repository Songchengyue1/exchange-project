<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getRecommendations } from '../api/ai'
import { listCategories } from '../api/categories'
import { listProducts } from '../api/products'
import type { CategoryPublic, ProductListItem } from '../types/product'
import { CONDITION_LABELS, TRADE_LABELS } from '../constants/productLabels'

const categories = ref<CategoryPublic[]>([])
const hotItems = ref<ProductListItem[]>([])
const latestItems = ref<ProductListItem[]>([])
const guessItems = ref<ProductListItem[]>([])
const loading = ref(true)

function formatPrice(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

onMounted(async () => {
  loading.value = true
  try {
    const [cats, page, rec] = await Promise.all([
      listCategories(),
      listProducts({ page_size: 12, sort: 'created_at_desc' }),
      getRecommendations(8).catch(() => ({ items: [], mode: 'empty' as const })),
    ])
    categories.value = cats
    latestItems.value = page.items.slice(0, 8)
    hotItems.value = page.items.filter((i) => i.is_hot).slice(0, 8)
    guessItems.value = rec.items
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="hero-band">
    <p class="hero-band__eyebrow ds-label-caps">Local · C2C · Trusted</p>
    <h1 class="hero-band__title">本地闲置<br />即刻成交</h1>
    <p class="hero-band__lede">
      分类、上架审核与商品列表已接入；热门标签基于卖家信誉分（≥4.5）自动展示。订单与支付将在 M3 继续完善。
    </p>
    <div class="hero-band__cta">
      <RouterLink class="ds-btn" to="/products">浏览商品</RouterLink>
      <RouterLink class="ds-text-link ds-label-caps" to="/sell">发布闲置 →</RouterLink>
    </div>
  </section>

  <section class="section">
    <div class="section__head">
      <p class="section__label ds-label-caps">Categories</p>
      <div class="category-tabs" role="navigation">
        <RouterLink class="category-link" to="/products">全部</RouterLink>
        <span class="category-tab__sep" aria-hidden="true">·</span>
        <RouterLink
          v-for="c in categories"
          :key="c.id"
          class="category-link"
          :to="{ path: '/products', query: { category: String(c.id) } }"
        >
          {{ c.name }}
        </RouterLink>
      </div>
    </div>

    <p v-if="loading" class="muted">加载推荐中…</p>

    <template v-else>
      <div class="block">
        <div class="block__head">
          <h2 class="block__title ds-label-caps">Hot picks</h2>
          <RouterLink class="more ds-text-link ds-label-caps" to="/products">查看全部 →</RouterLink>
        </div>
        <div v-if="!hotItems.length" class="muted">暂无热门商品（卖家信誉分达到 4.5 后自动展示）</div>
        <div v-else class="prod-grid">
          <RouterLink v-for="p in hotItems" :key="p.id" class="mini ds-hover-card" :to="`/products/${p.id}`">
            <div class="mini__media ds-hover-card__media">
              <img v-if="p.cover_image" :src="p.cover_image" :alt="p.title" />
              <div v-else class="mini__ph" />
              <span class="mini__hot ds-label-caps">Hot</span>
            </div>
            <p class="mini__t">{{ p.title }}</p>
            <p class="mini__m">{{ CONDITION_LABELS[p.condition] ?? p.condition }} · {{ TRADE_LABELS[p.trade_type] ?? p.trade_type }}</p>
            <p class="mini__p ds-hover-card__price">¥ {{ formatPrice(p.price) }}</p>
          </RouterLink>
        </div>
      </div>

      <div v-if="guessItems.length" class="block block--spaced">
        <div class="block__head">
          <h2 class="block__title ds-label-caps">For you</h2>
          <span class="muted small">猜你喜欢</span>
        </div>
        <div class="prod-grid">
          <RouterLink v-for="p in guessItems" :key="'g-' + p.id" class="mini ds-hover-card" :to="`/products/${p.id}`">
            <div class="mini__media ds-hover-card__media">
              <img v-if="p.cover_image" :src="p.cover_image" :alt="p.title" />
              <div v-else class="mini__ph" />
            </div>
            <p class="mini__t">{{ p.title }}</p>
            <p class="mini__m">{{ p.category_name }}</p>
            <p class="mini__p ds-hover-card__price">¥ {{ formatPrice(p.price) }}</p>
          </RouterLink>
        </div>
      </div>

      <div class="block block--spaced">
        <div class="block__head">
          <h2 class="block__title ds-label-caps">Latest</h2>
          <RouterLink class="more ds-text-link ds-label-caps" to="/products">查看全部 →</RouterLink>
        </div>
        <div class="prod-grid">
          <RouterLink v-for="p in latestItems" :key="p.id" class="mini ds-hover-card" :to="`/products/${p.id}`">
            <div class="mini__media ds-hover-card__media">
              <img v-if="p.cover_image" :src="p.cover_image" :alt="p.title" />
              <div v-else class="mini__ph" />
            </div>
            <p class="mini__t">{{ p.title }}</p>
            <p class="mini__m">{{ p.category_name }}</p>
            <p class="mini__p ds-hover-card__price">¥ {{ formatPrice(p.price) }}</p>
          </RouterLink>
        </div>
      </div>
    </template>
  </section>

  <section class="cta-band">
    <div class="cta-band__inner">
      <h2 class="cta-band__title">准备好连接买家与卖家</h2>
      <a class="ds-btn cta-band__btn" href="/docs" target="_blank" rel="noopener noreferrer">后端 Swagger</a>
    </div>
  </section>
</template>

<style scoped>
.hero-band {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-xxl) var(--space-lg) var(--space-section);
}

.hero-band__eyebrow {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.hero-band__title {
  margin: 0 0 var(--space-lg);
  font-family: var(--font-display);
  font-size: clamp(40px, 7vw, 80px);
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: -0.5px;
  color: var(--color-on-dark);
}

.hero-band__lede {
  margin: 0 0 var(--space-xl);
  max-width: 52ch;
  font-size: 16px;
  font-weight: 300;
  line-height: 1.5;
  color: var(--color-body);
}

.hero-band__cta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-lg);
}

.section {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--space-lg) var(--space-section);
}

.section__head {
  margin-bottom: var(--space-xl);
}

.section__label {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs);
}

.category-link {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  padding: var(--space-sm) 0;
  color: var(--color-body);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  transition:
    color var(--duration-fast) ease,
    border-color var(--duration-fast) ease,
    transform var(--duration-fast) var(--ease-out);
}

.category-link:hover {
  color: var(--color-body-strong);
  transform: translateY(-2px);
}

.category-link.router-link-active {
  color: var(--color-on-dark);
  border-bottom-color: var(--color-on-dark);
}

.category-tab__sep {
  color: var(--color-muted);
  user-select: none;
}

.muted {
  margin: 0 0 var(--space-lg);
  color: var(--color-muted);
  font-weight: 300;
}

.muted.small {
  margin: 0;
  font-size: 13px;
}

.block--spaced {
  margin-top: var(--space-xxl);
}

.block__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.block__title {
  margin: 0;
  color: var(--color-muted);
}

.prod-grid {
  display: grid;
  gap: var(--space-lg);
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

.mini {
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-card);
  text-decoration: none;
  color: inherit;
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.mini__media {
  position: relative;
  aspect-ratio: 16 / 10;
  background: var(--color-surface-soft);
}

.mini__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.mini__ph {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--color-surface-soft), var(--color-carbon-gray));
}

.mini__hot {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 8px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  font-size: 10px;
}

.mini__t {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-on-dark);
  line-height: 1.35;
}

.mini__m {
  margin: 0;
  font-size: 13px;
  font-weight: 300;
  color: var(--color-body);
}

.mini__p {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.cta-band {
  border-top: 1px solid var(--color-hairline);
  padding: 80px var(--space-lg);
  background: var(--color-canvas);
  transition: background-color var(--duration-normal) ease;
}

.cta-band:hover {
  background: var(--color-surface-soft);
}

.cta-band__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  text-align: center;
}

.cta-band__title {
  margin: 0 0 var(--space-xl);
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.5px;
  color: var(--color-on-dark);
}

.cta-band__btn {
  margin: 0 auto;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
