<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { acceptConfirm, dismissConfirm, useConfirmState } from '../composables/useConfirm'

const state = useConfirmState()

function onKeydown(e: KeyboardEvent) {
  if (!state.visible) return
  if (e.key === 'Escape') dismissConfirm()
}

watch(
  () => state.visible,
  (open) => {
    document.body.style.overflow = open ? 'hidden' : ''
  },
)

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="confirm-fade">
      <div
        v-if="state.visible"
        class="confirm-overlay"
        role="presentation"
        @click.self="dismissConfirm"
      >
        <div
          class="confirm-panel"
          role="alertdialog"
          aria-modal="true"
          :aria-labelledby="state.visible ? 'confirm-title' : undefined"
          :aria-describedby="state.visible ? 'confirm-message' : undefined"
        >
          <div class="confirm-panel__stripe ds-m-stripe" aria-hidden="true" />
          <h2 id="confirm-title" class="confirm-panel__title">{{ state.title }}</h2>
          <p id="confirm-message" class="confirm-panel__message">{{ state.message }}</p>
          <div class="confirm-panel__actions">
            <button type="button" class="ds-btn confirm-panel__btn" @click="dismissConfirm">
              {{ state.cancelText }}
            </button>
            <button
              type="button"
              class="ds-btn confirm-panel__btn confirm-panel__btn--primary"
              :class="{ 'confirm-panel__btn--danger': state.variant === 'danger' }"
              @click="acceptConfirm"
            >
              {{ state.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-overlay {
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

.confirm-panel {
  width: min(100%, 420px);
  padding: var(--space-lg);
  background: var(--color-surface-card);
  border: 1px solid var(--color-hairline);
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.45);
}

.confirm-panel__stripe {
  width: calc(100% + 2 * var(--space-lg));
  margin: calc(-1 * var(--space-lg)) calc(-1 * var(--space-lg)) var(--space-md);
}

.confirm-panel__title {
  margin: 0 0 var(--space-sm);
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-on-dark);
}

.confirm-panel__message {
  margin: 0 0 var(--space-xl);
  font-size: 15px;
  font-weight: 400;
  line-height: 1.55;
  color: var(--color-body);
}

.confirm-panel__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.confirm-panel__btn {
  height: 44px;
  padding: 0 24px;
  min-width: 96px;
}

.confirm-panel__btn--primary {
  background: var(--color-on-dark);
  color: var(--color-on-primary);
  border-color: var(--color-on-dark);
}

.confirm-panel__btn--primary:hover {
  background: var(--color-body-strong);
  border-color: var(--color-body-strong);
  color: var(--color-on-primary);
}

.confirm-panel__btn--danger {
  background: var(--color-m-red);
  border-color: var(--color-m-red);
  color: #fff;
}

.confirm-panel__btn--danger:hover {
  background: #c41f12;
  border-color: #c41f12;
  color: #fff;
}

.confirm-fade-enter-active,
.confirm-fade-leave-active {
  transition: opacity 0.18s ease;
}

.confirm-fade-enter-active .confirm-panel,
.confirm-fade-leave-active .confirm-panel {
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.confirm-fade-enter-from,
.confirm-fade-leave-to {
  opacity: 0;
}

.confirm-fade-enter-from .confirm-panel,
.confirm-fade-leave-to .confirm-panel {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}
</style>
