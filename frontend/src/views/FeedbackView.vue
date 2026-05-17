<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { submitFeedback } from '../api/feedback'
import { showConfirm } from '../composables/useConfirm'

const subject = ref('')
const content = ref('')
const message = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  if (!subject.value.trim()) {
    error.value = '请填写主题'
    return
  }
  if (!content.value.trim()) {
    error.value = '请填写反馈内容'
    return
  }

  const ok = await showConfirm({
    title: '提交反馈',
    message: '确定提交该意见反馈？提交后可在「我的反馈」查看处理进度。',
    confirmText: '提交',
  })
  if (!ok) return

  loading.value = true
  error.value = ''
  message.value = ''
  try {
    await submitFeedback({
      subject: subject.value.trim(),
      content: content.value.trim(),
    })
    subject.value = ''
    content.value = ''
    message.value = '反馈已提交，感谢你的意见'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '提交失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="wrap page-narrow">
    <p class="eyebrow ds-label-caps">Feedback</p>
    <h1 class="title">意见反馈</h1>
    <p class="lede">遇到问题或有产品建议？填写后管理员会跟进处理。</p>

    <p v-if="message" class="msg">{{ message }}</p>
    <p v-if="error" class="ds-form-error">{{ error }}</p>

    <form class="form" @submit.prevent="onSubmit">
      <div class="ds-field">
        <label class="ds-label" for="fb-subject">主题</label>
        <input id="fb-subject" v-model="subject" class="ds-input" maxlength="120" required />
      </div>
      <div class="ds-field">
        <label class="ds-label" for="fb-content">内容</label>
        <textarea
          id="fb-content"
          v-model="content"
          class="ds-textarea"
          rows="6"
          maxlength="5000"
          required
        />
      </div>
      <button type="submit" class="ds-btn" :disabled="loading">
        {{ loading ? '提交中…' : '提交反馈' }}
      </button>
    </form>

    <p class="foot">
      <RouterLink to="/feedback/mine" class="text-link">查看我的反馈 →</RouterLink>
    </p>
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
  color: var(--color-body);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.msg {
  margin: 0 0 var(--space-md);
  color: var(--color-success);
}

.foot {
  margin-top: var(--space-xl);
}

.text-link {
  color: var(--color-on-dark);
  text-decoration: none;
}
</style>
