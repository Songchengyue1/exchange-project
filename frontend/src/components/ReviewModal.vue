<script setup lang="ts">
import { ref, watch } from 'vue'
import { createOrderReview } from '../api/reviews'

const props = defineProps<{
  open: boolean
  orderId: number
  productTitle: string
}>()

const emit = defineEmits<{
  close: []
  submitted: []
}>()

const rating = ref(5)
const comment = ref('')
const busy = ref(false)
const error = ref('')

watch(
  () => props.open,
  (v) => {
    if (v) {
      rating.value = 5
      comment.value = ''
      error.value = ''
    }
  },
)

function dismiss() {
  if (busy.value) return
  emit('close')
}

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await createOrderReview(props.orderId, {
      rating: rating.value,
      comment: comment.value.trim() || undefined,
    })
    emit('submitted')
    emit('close')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '提交失败'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="open" class="modal-overlay" role="presentation" @click.self="dismiss">
        <div
          class="modal-panel"
          role="dialog"
          aria-modal="true"
          aria-labelledby="review-title"
        >
          <div class="modal-panel__stripe ds-m-stripe" aria-hidden="true" />
          <h2 id="review-title" class="modal-panel__title">评价订单</h2>
          <p class="modal-panel__sub">{{ productTitle }}</p>

          <div class="ds-field">
            <label class="ds-label" for="rating">评分</label>
            <select id="rating" v-model.number="rating" class="ds-input">
              <option :value="5">5 分 — 非常满意</option>
              <option :value="4">4 分 — 满意</option>
              <option :value="3">3 分 — 一般</option>
              <option :value="2">2 分 — 不满意</option>
              <option :value="1">1 分 — 很差</option>
            </select>
          </div>
          <div class="ds-field">
            <label class="ds-label" for="review-comment">评价内容（选填）</label>
            <textarea
              id="review-comment"
              v-model="comment"
              class="ds-textarea"
              maxlength="2000"
              rows="4"
              placeholder="描述交易体验，帮助其他买家参考"
            />
          </div>

          <p v-if="error" class="ds-form-error">{{ error }}</p>

          <div class="modal-panel__actions">
            <button type="button" class="ds-btn modal-panel__btn" :disabled="busy" @click="dismiss">
              取消
            </button>
            <button
              type="button"
              class="ds-btn modal-panel__btn modal-panel__btn--primary"
              :disabled="busy"
              @click="submit"
            >
              {{ busy ? '提交中…' : '提交评价' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(4px);
}

.modal-panel {
  width: min(100%, 440px);
  padding: var(--space-lg);
  background: var(--color-surface-card);
  border: 1px solid var(--color-hairline);
}

.modal-panel__stripe {
  width: calc(100% + 2 * var(--space-lg));
  margin: calc(-1 * var(--space-lg)) calc(-1 * var(--space-lg)) var(--space-md);
}

.modal-panel__title {
  margin: 0 0 var(--space-xs);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-dark);
}

.modal-panel__sub {
  margin: 0 0 var(--space-lg);
  font-size: 14px;
  color: var(--color-muted);
}

.modal-panel__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.modal-panel__btn {
  height: 44px;
  padding: 0 20px;
}

.modal-panel__btn--primary {
  background: var(--color-on-dark);
  color: var(--color-on-primary);
  border-color: var(--color-on-dark);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.18s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
