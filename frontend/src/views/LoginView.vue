<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    const r = route.query.redirect
    await router.replace(typeof r === 'string' ? r : '/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="wrap page-narrow">
    <p class="eyebrow ds-label-caps">Account</p>
    <h1 class="title">登录</h1>
    <p class="lede">使用用户名与密码进入平台。</p>

    <form class="ds-stack" @submit.prevent="onSubmit">
      <p v-if="error" class="ds-form-error">{{ error }}</p>
      <div class="ds-field">
        <label class="ds-label" for="login-user">用户名</label>
        <input id="login-user" v-model="username" class="ds-input" autocomplete="username" required />
      </div>
      <div class="ds-field">
        <label class="ds-label" for="login-pass">密码</label>
        <input
          id="login-pass"
          v-model="password"
          class="ds-input"
          type="password"
          autocomplete="current-password"
          required
        />
      </div>
      <button type="submit" class="ds-btn" :disabled="loading">{{ loading ? '请稍候…' : '登录' }}</button>
    </form>

    <p class="foot">
      没有账号？
      <RouterLink to="/register">去注册</RouterLink>
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
