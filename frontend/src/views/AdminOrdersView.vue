<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { approveAdminRefund, listAdminOrders, rejectAdminRefund } from '../api/admin'
import { showConfirm } from '../composables/useConfirm'
import { ORDER_STATUS_LABELS } from '../constants/orderLabels'
import type { AdminOrderItem } from '../types/admin'

const tab = ref('')
const items = ref<AdminOrderItem[]>([])
const loading = ref(true)
const error = ref('')
const busyId = ref<number | null>(null)
const rejectNote = ref<Record<number, string>>({})

const tabs = [
  { value: '', label: '全部' },
  { value: 'refund_pending', label: '退款待审' },
  { value: 'pending_fulfillment', label: '待卖家履约' },
  { value: 'pending_receipt', label: '待买家确认' },
  { value: 'pending_payment', label: '待付款' },
  { value: 'completed', label: '已完成' },
  { value: 'refunded', label: '已退款' },
  { value: 'cancelled', label: '已取消' },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await listAdminOrders(tab.value || undefined)
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

async function approve(o: AdminOrderItem) {
  const ok = await showConfirm({
    title: '通过退款',
    message: `订单 #${o.id} 将通过退款并恢复库存，确定？`,
    confirmText: '通过',
  })
  if (!ok) return
  busyId.value = o.id
  error.value = ''
  try {
    await approveAdminRefund(o.id)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    busyId.value = null
  }
}

async function reject(o: AdminOrderItem) {
  const ok = await showConfirm({
    title: '驳回退款',
    message: `订单 #${o.id} 将恢复到退款前状态，确定？`,
    confirmText: '驳回',
    variant: 'danger',
  })
  if (!ok) return
  busyId.value = o.id
  error.value = ''
  try {
    await rejectAdminRefund(o.id, rejectNote.value[o.id]?.trim() || undefined)
    rejectNote.value[o.id] = ''
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    busyId.value = null
  }
}

function formatPrice(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}
</script>

<template>
  <section>
    <p class="lede">查看全站订单；处理买家申请的退款（通过则恢复库存）。</p>

    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.value"
        type="button"
        class="tab"
        :class="{ 'tab--on': tab === t.value }"
        @click="tab = t.value"
      >
        {{ t.label }}
      </button>
    </div>

    <p v-if="error" class="ds-form-error">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="!items.length" class="muted">暂无订单</p>

    <ul v-else class="list">
      <li v-for="o in items" :key="o.id" class="card">
        <div class="card__head">
          <RouterLink :to="`/products/${o.product_id}`" class="title">{{ o.product_title }}</RouterLink>
          <div class="card__head-right">
            <RouterLink class="mini-link ds-label-caps" :to="{ name: 'order-detail', params: { id: String(o.id) } }">
              查看订单
            </RouterLink>
            <span class="status">{{ ORDER_STATUS_LABELS[o.status] ?? o.status }}</span>
          </div>
        </div>
        <p class="meta">
          订单 #{{ o.id }} · ¥ {{ formatPrice(o.amount) }} · 买家 {{ o.buyer_nickname }} · 卖家
          {{ o.seller_nickname }}
        </p>
        <p v-if="o.refund_reason" class="reason">退款原因：{{ o.refund_reason }}</p>
        <p v-if="o.refund_reject_reason" class="reason reason--muted">
          退款驳回：{{ o.refund_reject_reason }}
        </p>
        <div v-if="o.status === 'refund_pending'" class="actions">
          <button type="button" class="ds-btn" :disabled="busyId === o.id" @click="approve(o)">通过退款</button>
          <input v-model="rejectNote[o.id]" class="ds-input" placeholder="驳回备注（可选）" />
          <button type="button" class="link-btn danger" :disabled="busyId === o.id" @click="reject(o)">
            驳回
          </button>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.lede {
  margin: 0 0 var(--space-md);
  font-size: 14px;
  color: var(--color-body);
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: var(--space-lg);
}

.tab {
  padding: 6px 12px;
  border: 1px solid var(--color-hairline);
  background: var(--color-surface-card);
  font-size: 13px;
  cursor: pointer;
  border-radius: 999px;
}

.tab--on {
  background: var(--color-on-dark);
  color: var(--color-canvas);
  border-color: var(--color-on-dark);
}

.muted {
  color: var(--color-muted);
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.card {
  border: 1px solid var(--color-hairline);
  padding: var(--space-md);
  background: var(--color-surface-card);
}

.card__head {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  align-items: flex-start;
}

.card__head-right {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.mini-link {
  font-size: 11px;
  color: var(--color-body);
  text-decoration: none;
  border: 1px solid var(--color-hairline);
  padding: 4px 10px;
  border-radius: 999px;
  transition:
    color var(--duration-fast) ease,
    border-color var(--duration-fast) ease,
    background-color var(--duration-fast) ease;
}

.mini-link:hover {
  color: var(--color-on-dark);
  border-color: var(--color-on-dark);
  background: var(--color-surface-elevated);
}

.title {
  font-weight: 700;
  color: var(--color-on-dark);
  text-decoration: none;
}

.status {
  font-size: 12px;
  color: var(--color-muted);
  white-space: nowrap;
}

.meta,
.reason {
  margin: var(--space-sm) 0 0;
  font-size: 14px;
  color: var(--color-body);
}

.reason {
  color: var(--color-m-red);
}

.reason--muted {
  color: var(--color-body);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  align-items: center;
}

.link-btn.danger {
  background: none;
  border: none;
  color: var(--color-m-red);
  cursor: pointer;
}
</style>
