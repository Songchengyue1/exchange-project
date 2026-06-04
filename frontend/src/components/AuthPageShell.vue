<script setup lang="ts">
defineProps<{
  title: string
  lede: string
  eyebrow?: string
}>()
</script>

<template>
  <section class="auth-page">
    <div class="auth-page__bg" aria-hidden="true">
      <!-- 临时去掉代码雨背景（CodeRainCanvas） -->
    </div>

    <div class="auth-page__inner page-narrow">
      <header class="auth-page__head">
        <p class="auth-page__eyebrow ds-label-caps">{{ eyebrow ?? 'Account' }}</p>
        <h1 class="auth-page__title">{{ title }}</h1>
        <p class="auth-page__lede">{{ lede }}</p>
      </header>

      <div class="auth-page__card">
        <span class="auth-page__stripe ds-m-stripe" aria-hidden="true" />
        <div class="auth-page__body">
          <slot />
        </div>
      </div>

      <footer v-if="$slots.foot" class="auth-page__foot">
        <slot name="foot" />
      </footer>
    </div>
  </section>
</template>

<style scoped>
.auth-page {
  position: relative;
  overflow: hidden;
  min-height: calc(100svh - 72px);
  padding-top: var(--space-xxl);
  padding-bottom: var(--space-section);
}

.auth-page__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  background:
    radial-gradient(800px 420px at 24% 10%, rgba(28, 105, 212, 0.08), transparent 55%),
    radial-gradient(700px 500px at 78% 18%, rgba(28, 105, 212, 0.05), transparent 60%),
    radial-gradient(1200px 720px at 50% 90%, rgba(0, 0, 0, 0.03), transparent 60%),
    linear-gradient(180deg, #ffffff 0%, #fafbfc 40%, #f5f6f8 100%);
}

.auth-page__inner {
  position: relative;
  z-index: 1;
}

.auth-page__head > * {
  animation: auth-fade-up 0.65s var(--ease-out) both;
}

.auth-page__eyebrow {
  margin: 0 0 var(--space-md);
  color: var(--color-muted);
  animation-delay: 0.05s;
}

.auth-page__title {
  margin: 0 0 var(--space-sm);
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  color: var(--color-on-dark);
  animation-delay: 0.12s;
}

.auth-page__lede {
  margin: 0 0 var(--space-xl);
  font-size: 16px;
  font-weight: 400;
  color: var(--color-body);
  animation-delay: 0.2s;
}

.auth-page__card {
  position: relative;
  border: 1px solid color-mix(in srgb, var(--color-hairline) 80%, var(--color-m-blue-dark));
  background: linear-gradient(
    165deg,
    color-mix(in srgb, var(--color-surface-elevated) 96%, transparent) 0%,
    color-mix(in srgb, var(--color-surface-card) 98%, transparent) 100%
  );
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.04) inset,
    0 16px 48px rgba(0, 0, 0, 0.08),
    0 0 80px rgba(28, 105, 212, 0.06);
  animation: auth-card-in 0.75s var(--ease-out) 0.18s both;
}

.auth-page__stripe {
  display: block;
  transform-origin: left center;
  animation: auth-stripe-grow 0.9s var(--ease-out) 0.35s both;
}

.auth-page__body {
  padding: var(--space-lg) var(--space-lg) var(--space-xl);
}

/* —— 登录/注册专用表单（覆盖全局 ds-* 在窄页上的观感） —— */
.auth-page__body :deep(.auth-form.ds-stack) {
  gap: var(--space-lg);
}

.auth-page__body :deep(.auth-form.ds-stack > *) {
  animation: auth-fade-up 0.55s var(--ease-out) both;
}

.auth-page__body :deep(.auth-form.ds-stack > *:nth-child(1)) {
  animation-delay: 0.42s;
}
.auth-page__body :deep(.auth-form.ds-stack > *:nth-child(2)) {
  animation-delay: 0.5s;
}
.auth-page__body :deep(.auth-form.ds-stack > *:nth-child(3)) {
  animation-delay: 0.58s;
}
.auth-page__body :deep(.auth-form.ds-stack > *:nth-child(4)) {
  animation-delay: 0.66s;
}
.auth-page__body :deep(.auth-form.ds-stack > *:nth-child(5)) {
  animation-delay: 0.74s;
}
.auth-page__body :deep(.auth-form.ds-stack > *:nth-child(6)) {
  animation-delay: 0.82s;
}

.auth-page__body :deep(.auth-form .ds-field) {
  margin-bottom: 0;
  gap: 10px;
}

.auth-page__body :deep(.auth-form .ds-label) {
  font-size: 11px;
  font-weight: 400;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-body-strong);
}

.auth-page__body :deep(.auth-form .ds-input) {
  height: 52px;
  padding: 0 18px;
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 400;
  letter-spacing: 0.02em;
  line-height: 52px;
  color: var(--color-on-dark);
  background: var(--color-surface-soft);
  border: 1px solid var(--color-hairline-strong);
  border-radius: 2px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transition:
    border-color var(--duration-fast) ease,
    box-shadow var(--duration-normal) var(--ease-out),
    transform var(--duration-fast) var(--ease-out),
    background-color var(--duration-fast) ease;
}

.auth-page__body :deep(.auth-form .ds-input::placeholder) {
  color: var(--color-muted);
  font-weight: 400;
}

.auth-page__body :deep(.auth-form .ds-input:hover:not(:disabled):not(:focus)) {
  border-color: color-mix(in srgb, var(--color-body-strong) 70%, var(--color-hairline));
  background: var(--color-surface-elevated);
}

.auth-page__body :deep(.auth-form .ds-input:focus) {
  outline: none;
  transform: translateY(-1px);
  border-color: var(--color-m-blue-dark);
  background: #ffffff;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 0 0 1px var(--color-m-blue-dark),
    0 12px 32px rgba(28, 105, 212, 0.12);
}

/* 修复 Chrome 自动填充导致的蓝灰底 */
.auth-page__body :deep(.auth-form .ds-input:-webkit-autofill),
.auth-page__body :deep(.auth-form .ds-input:-webkit-autofill:hover),
.auth-page__body :deep(.auth-form .ds-input:-webkit-autofill:focus) {
  -webkit-text-fill-color: var(--color-on-dark) !important;
  caret-color: var(--color-on-dark);
  border: 1px solid var(--color-hairline-strong) !important;
  -webkit-box-shadow: 0 0 0 1000px var(--color-surface-soft) inset !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    0 0 0 1000px var(--color-surface-soft) inset !important;
  transition: background-color 99999s ease-out 0s;
}

.auth-page__body :deep(.auth-form .ds-input:-webkit-autofill:focus) {
  -webkit-box-shadow:
    0 0 0 1000px #ffffff inset,
    0 0 0 1px var(--color-m-blue-dark) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 0 0 1000px #ffffff inset,
    0 0 0 1px var(--color-m-blue-dark),
    0 12px 32px rgba(28, 105, 212, 0.12) !important;
}

.auth-page__body :deep(.auth-form .ds-btn) {
  width: 100%;
  height: 52px;
  margin-top: var(--space-xs);
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  transition:
    transform var(--duration-fast) var(--ease-out),
    opacity var(--duration-fast) ease,
    background-color var(--duration-fast) ease,
    box-shadow var(--duration-normal) var(--ease-out);
}

.auth-page__body :deep(.auth-form .ds-btn:hover:not(:disabled)) {
  transform: translateY(-2px);
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.1);
}

.auth-page__body :deep(.auth-form .ds-btn:active:not(:disabled)) {
  transform: translateY(0);
}

.auth-page__body :deep(.auth-form .ds-btn:disabled) {
  animation: auth-btn-pulse 1.2s ease-in-out infinite;
}

.auth-page__body :deep(.auth-form .ds-form-error) {
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  font-size: 13px;
  font-weight: 400;
  line-height: 1.45;
  color: var(--color-m-red);
  background: color-mix(in srgb, var(--color-m-red) 12%, transparent);
  border-left: 3px solid var(--color-m-red);
}

.auth-page__body :deep(.auth-form .ds-form-error.auth-shake) {
  animation: auth-shake 0.45s ease;
}

.auth-page__foot {
  margin: var(--space-xl) 0 0;
  font-size: 14px;
  font-weight: 400;
  color: var(--color-muted);
  animation: auth-fade-up 0.6s var(--ease-out) 0.88s both;
}

.auth-page__foot :deep(a) {
  color: var(--color-on-dark);
  text-decoration: none;
  position: relative;
  transition: color var(--duration-fast) ease;
}

.auth-page__foot :deep(a)::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -2px;
  width: 100%;
  height: 1px;
  background: var(--color-m-blue-dark);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform var(--duration-normal) var(--ease-out);
}

.auth-page__foot :deep(a:hover) {
  color: var(--color-body-strong);
}

.auth-page__foot :deep(a:hover)::after {
  transform: scaleX(1);
}

@keyframes auth-fade-up {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes auth-card-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes auth-stripe-grow {
  from {
    transform: scaleX(0);
    opacity: 0.6;
  }
  to {
    transform: scaleX(1);
    opacity: 1;
  }
}

@keyframes auth-shake {
  0%,
  100% {
    transform: translateX(0);
  }
  20%,
  60% {
    transform: translateX(-5px);
  }
  40%,
  80% {
    transform: translateX(5px);
  }
}

@keyframes auth-btn-pulse {
  0%,
  100% {
    opacity: 0.72;
  }
  50% {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth-page__head > *,
  .auth-page__card,
  .auth-page__stripe,
  .auth-page__body :deep(.auth-form.ds-stack > *),
  .auth-page__foot,
  .auth-page__body :deep(.auth-form .ds-btn:disabled) {
    animation: none !important;
  }

  .auth-page__body :deep(.auth-form .ds-input:focus),
  .auth-page__body :deep(.auth-form .ds-btn:hover:not(:disabled)) {
    transform: none;
  }
}
</style>
