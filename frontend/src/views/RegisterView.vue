<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const auth = useAuthStore()
const router = useRouter()

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.register(username.value.trim(), password.value)
    await router.replace('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="wrap page-narrow">
    <p class="eyebrow ds-label-caps">Account</p>
    <h1 class="title">注册</h1>
    <p class="lede">用户名 3–32 位字母数字下划线；密码至少 6 位。</p>

    <form class="ds-stack" @submit.prevent="onSubmit">
      <p v-if="error" class="ds-form-error">{{ error }}</p>
      <div class="ds-field">
        <label class="ds-label" for="reg-user">用户名</label>
        <input id="reg-user" v-model="username" class="ds-input" autocomplete="username" required />
      </div>
      <div class="ds-field">
        <label class="ds-label" for="reg-pass">密码</label>
        <input
          id="reg-pass"
          v-model="password"
          class="ds-input"
          type="password"
          autocomplete="new-password"
          required
        />
      </div>
      <button type="submit" class="ds-btn" :disabled="loading">{{ loading ? '请稍候…' : '创建账号' }}</button>
    </form>

    <p class="foot">
      已有账号？
      <RouterLink to="/login">去登录</RouterLink>
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
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.lede {
  margin: 0 0 var(--space-xl);
  font-size: 16px;
  font-weight: 300;
  color: var(--color-body);
}

.foot {
  margin: var(--space-xl) 0 0;
  font-size: 14px;
  font-weight: 300;
  color: var(--color-muted);
}

.foot a {
  color: var(--color-on-dark);
  text-decoration: none;
}

.foot a:hover {
  text-decoration: underline;
}
</style>
