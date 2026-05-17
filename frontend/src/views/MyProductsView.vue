<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { listMyProducts, offlineProduct } from '../api/products'
import { showConfirm } from '../composables/useConfirm'
import type { ProductDetail } from '../types/product'
import { STATUS_LABELS } from '../constants/productLabels'

const items = ref<ProductDetail[]>([])
const loading = ref(true)
const error = ref('')
const tab = ref<string>('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await listMyProducts(tab.value || undefined)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(tab, () => {
  void load()
})

async function offline(id: number) {
  const ok = await showConfirm({
    title: '下架商品',
    message: '确认下架该商品？下架后买家将无法购买。',
    confirmText: '下架',
    variant: 'danger',
  })
  if (!ok) return
  error.value = ''
  try {
    await offlineProduct(id)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '下架失败'
  }
}
</script>

<template>
  <section class="wrap">
    <header class="head">
      <p class="eyebrow ds-label-caps">Seller</p>
      <h1 class="title">我的商品</h1>
      <p class="lede">查看审核状态；驳回原因仅本人可见。编辑将重新进入待审核。</p>
    </header>

    <div class="tabs">
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': tab === '', 'ds-hover-tab--on': tab === '' }" @click="tab = ''">全部</button>
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': tab === 'pending', 'ds-hover-tab--on': tab === 'pending' }" @click="tab = 'pending'">
        待审核
      </button>
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': tab === 'approved', 'ds-hover-tab--on': tab === 'approved' }" @click="tab = 'approved'">
        已上架
      </button>
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': tab === 'rejected', 'ds-hover-tab--on': tab === 'rejected' }" @click="tab = 'rejected'">
        已驳回
      </button>
      <button type="button" class="tab ds-hover-tab" :class="{ 'tab--on': tab === 'offline', 'ds-hover-tab--on': tab === 'offline' }" @click="tab = 'offline'">
        已下架
      </button>
    </div>

    <p v-if="error" class="ds-form-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-else class="list">
      <article v-for="p in items" :key="p.id" class="row ds-hover-row ds-hover-row--flex">
        <div class="row__main">
          <RouterLink class="row__title" :to="`/products/${p.id}`">{{ p.title }}</RouterLink>
          <p class="row__meta">
            {{ STATUS_LABELS[p.status] ?? p.status }} · ¥ {{ p.price }} · 库存 {{ p.stock }}
          </p>
          <p v-if="p.status === 'rejected' && p.reject_reason" class="row__reject">
            驳回原因：{{ p.reject_reason }}
          </p>
        </div>
        <div class="row__actions">
          <RouterLink class="ds-btn row__btn" :to="`/sell?edit=${p.id}`">编辑</RouterLink>
          <button
            v-if="p.status !== 'offline'"
            type="button"
            class="ds-btn row__btn"
            @click="offline(p.id)"
          >
            下架
          </button>
        </div>
      </article>
      <p v-if="!items.length" class="muted">暂无商品</p>
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

.lede {
  margin: 0;
  font-size: 16px;
  font-weight: 300;
  color: var(--color-body);
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
  padding: 10px 14px;
  cursor: pointer;
  font-size: 13px;
  letter-spacing: 0.5px;
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

.row {
  border: 1px solid var(--color-hairline);
  padding: var(--space-lg);
  background: var(--color-surface-card);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  justify-content: space-between;
}

.row__title {
  font-weight: 700;
  color: var(--color-on-dark);
  text-decoration: none;
}

.row__title:hover {
  text-decoration: underline;
}

.row__meta {
  margin: var(--space-xs) 0 0;
  font-size: 14px;
  color: var(--color-body);
  font-weight: 300;
}

.row__reject {
  margin: var(--space-sm) 0 0;
  font-size: 14px;
  color: var(--color-m-red);
  font-weight: 300;
}

.row__actions {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-start;
}

.row__btn {
  height: 40px;
  padding: 0 14px;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
