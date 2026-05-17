<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { listMyFeedback } from '../api/feedback'
import { FEEDBACK_STATUS_LABELS } from '../constants/feedbackLabels'
import type { FeedbackPublic } from '../types/feedback'

const items = ref<FeedbackPublic[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    items.value = await listMyFeedback()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
})

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<template>
  <section class="wrap page-narrow">
    <p class="eyebrow ds-label-caps">Feedback</p>
    <h1 class="title">我的反馈</h1>
    <p class="lede">
      <RouterLink to="/feedback" class="ds-text-link">提交新反馈 →</RouterLink>
    </p>

    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="ds-form-error">{{ error }}</p>
    <p v-else-if="!items.length" class="muted">暂无反馈记录</p>

    <ul v-else class="list">
      <li v-for="f in items" :key="f.id" class="card ds-hover-card">
        <div class="card__head">
          <h2 class="card__title">{{ f.subject }}</h2>
          <span class="pill">{{ FEEDBACK_STATUS_LABELS[f.status] ?? f.status }}</span>
        </div>
        <p class="card__content">{{ f.content }}</p>
        <p v-if="f.admin_reply" class="card__reply">
          <span class="k">管理员回复</span>{{ f.admin_reply }}
        </p>
        <p class="card__meta">{{ formatTime(f.created_at) }}</p>
      </li>
    </ul>
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
  margin: 0 0 var(--space-sm);
  font-size: clamp(26px, 3.5vw, 36px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.lede {
  margin: 0 0 var(--space-xl);
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
  padding: var(--space-lg);
  background: var(--color-surface-card);
}

.card__head {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  align-items: flex-start;
  margin-bottom: var(--space-sm);
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
  color: var(--color-body-strong);
  white-space: nowrap;
}

.card__content {
  margin: 0 0 var(--space-sm);
  font-size: 14px;
  color: var(--color-body);
  line-height: 1.5;
}

.card__reply {
  margin: 0 0 var(--space-sm);
  padding: var(--space-sm);
  background: var(--color-surface-soft);
  font-size: 14px;
  color: var(--color-body);
}

.k {
  color: var(--color-muted);
  margin-right: var(--space-xs);
}

.card__meta {
  margin: 0;
  font-size: 12px;
  color: var(--color-muted);
}

.text-link {
  color: var(--color-on-dark);
  text-decoration: none;
}
</style>
