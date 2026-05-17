<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { approveProduct, listPendingProducts, rejectProduct } from '../api/admin'
import type { ProductDetail } from '../types/product'

const items = ref<ProductDetail[]>([])
const loading = ref(true)
const error = ref('')
const busyId = ref<number | null>(null)
const rejectReason = ref<Record<number, string>>({})

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await listPendingProducts()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function approve(id: number) {
  busyId.value = id
  error.value = ''
  try {
    await approveProduct(id)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    busyId.value = null
  }
}

async function reject(id: number) {
  const reason = (rejectReason.value[id] || '').trim()
  if (!reason) {
    error.value = '请填写驳回原因'
    return
  }
  busyId.value = id
  error.value = ''
  try {
    await rejectProduct(id, reason)
    rejectReason.value[id] = ''
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <section>
    <p class="lede">处理待审核商品：通过上架或驳回并填写原因。</p>
    <p v-if="error" class="ds-form-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-else class="list">
      <article v-for="p in items" :key="p.id" class="card">
        <div class="card__top">
          <RouterLink
            class="card__title"
            :to="{ path: `/products/${p.id}`, query: { from: 'admin' } }"
          >
            {{ p.title }}
          </RouterLink>
          <p class="card__sub">卖家：{{ p.seller.nickname }} · ¥ {{ p.price }} · {{ p.category_name }}</p>
        </div>
        <p class="card__desc">{{ p.description }}</p>
        <div class="card__row">
          <input
            v-model="rejectReason[p.id]"
            class="ds-input"
            type="text"
            placeholder="驳回原因（必填方可驳回）"
          />
          <button type="button" class="ds-btn" :disabled="busyId === p.id" @click="reject(p.id)">
            驳回
          </button>
          <button type="button" class="ds-btn" :disabled="busyId === p.id" @click="approve(p.id)">
            通过
          </button>
        </div>
      </article>
      <p v-if="!items.length" class="muted">暂无待审核商品</p>
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

.muted {
  color: var(--color-muted);
}

.list {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.card {
  border: 1px solid var(--color-hairline);
  padding: var(--space-lg);
  background: var(--color-surface-card);
}

.card__title {
  font-weight: 700;
  color: var(--color-on-dark);
  text-decoration: none;
}

.card__sub {
  margin: var(--space-xs) 0 0;
  font-size: 14px;
  color: var(--color-body);
  font-weight: 300;
}

.card__desc {
  margin: var(--space-md) 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--color-body);
  font-weight: 300;
  white-space: pre-wrap;
}

.card__row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
}

.card__row .ds-input {
  flex: 1 1 220px;
}

.card__row .ds-btn {
  height: 40px;
  padding: 0 14px;
}
</style>
