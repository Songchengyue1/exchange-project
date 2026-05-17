<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { adminListFeedback, adminUpdateFeedback } from '../api/feedback'
import { FEEDBACK_STATUS_LABELS } from '../constants/feedbackLabels'
import { showConfirm } from '../composables/useConfirm'
import type { FeedbackAdminItem, FeedbackStatus } from '../types/feedback'

const tab = ref<string>('')
const items = ref<FeedbackAdminItem[]>([])
const loading = ref(true)
const error = ref('')
const busyId = ref<number | null>(null)

const replyDraft = ref<Record<number, string>>({})
const statusDraft = ref<Record<number, FeedbackStatus>>({})

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await adminListFeedback(tab.value || undefined)
    for (const f of items.value) {
      replyDraft.value[f.id] = f.admin_reply ?? ''
      statusDraft.value[f.id] = (f.status as FeedbackStatus) || 'pending'
    }
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

async function save(f: FeedbackAdminItem) {
  const ok = await showConfirm({
    title: '更新反馈',
    message: `确定更新反馈 #${f.id} 的状态与回复吗？`,
    confirmText: '保存',
  })
  if (!ok) return

  busyId.value = f.id
  error.value = ''
  try {
    await adminUpdateFeedback(f.id, {
      status: statusDraft.value[f.id],
      admin_reply: replyDraft.value[f.id]?.trim() || undefined,
    })
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <section>
    <div class="tabs">
      <button type="button" class="tab ds-hover-tab" :class="{ active: tab === '', 'ds-hover-tab--on': tab === '' }" @click="tab = ''">全部</button>
      <button type="button" class="tab ds-hover-tab" :class="{ active: tab === 'pending', 'ds-hover-tab--on': tab === 'pending' }" @click="tab = 'pending'">
        待处理
      </button>
      <button type="button" class="tab ds-hover-tab" :class="{ active: tab === 'processing', 'ds-hover-tab--on': tab === 'processing' }" @click="tab = 'processing'">
        处理中
      </button>
      <button type="button" class="tab ds-hover-tab" :class="{ active: tab === 'resolved', 'ds-hover-tab--on': tab === 'resolved' }" @click="tab = 'resolved'">
        已处理
      </button>
    </div>

    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="ds-form-error">{{ error }}</p>
    <p v-else-if="!items.length" class="muted">暂无反馈</p>

    <ul v-else class="list">
      <li v-for="f in items" :key="f.id" class="card ds-hover-card">
        <div class="card__head">
          <div>
            <p class="card__meta">#{{ f.id }} · {{ f.nickname }}（{{ f.username }}）</p>
            <h2 class="card__title">{{ f.subject }}</h2>
          </div>
          <span class="pill">{{ FEEDBACK_STATUS_LABELS[f.status] ?? f.status }}</span>
        </div>
        <p class="card__content">{{ f.content }}</p>
        <div class="ds-field">
          <label class="ds-label" :for="`st-${f.id}`">状态</label>
          <select :id="`st-${f.id}`" v-model="statusDraft[f.id]" class="ds-input">
            <option value="pending">待处理</option>
            <option value="processing">处理中</option>
            <option value="resolved">已处理</option>
          </select>
        </div>
        <div class="ds-field">
          <label class="ds-label" :for="`rp-${f.id}`">管理员回复</label>
          <textarea :id="`rp-${f.id}`" v-model="replyDraft[f.id]" class="ds-textarea" rows="3" />
        </div>
        <button type="button" class="ds-btn" :disabled="busyId === f.id" @click="save(f)">
          {{ busyId === f.id ? '保存中…' : '保存' }}
        </button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.wrap {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-section) var(--space-lg);
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

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-xl);
}

.tab {
  padding: var(--space-xs) var(--space-md);
  border: 1px solid var(--color-hairline);
  background: transparent;
  color: var(--color-body);
  cursor: pointer;
  font-size: 13px;
}

.tab.active {
  color: var(--color-on-dark);
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
  gap: var(--space-lg);
}

.card {
  border: 1px solid var(--color-hairline);
  padding: var(--space-lg);
  background: var(--color-surface-card);
}

.card__head {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  margin-bottom: var(--space-sm);
}

.card__meta {
  margin: 0 0 var(--space-xs);
  font-size: 12px;
  color: var(--color-muted);
}

.card__title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.pill {
  font-size: 12px;
  padding: 2px 8px;
  border: 1px solid var(--color-hairline);
  white-space: nowrap;
}

.card__content {
  margin: 0 0 var(--space-md);
  font-size: 14px;
  color: var(--color-body);
  line-height: 1.5;
}
</style>
