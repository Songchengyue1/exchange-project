<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthPageShell from '../components/AuthPageShell.vue'
import { useAuthStore } from '../stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const errorShake = ref(false)
const loading = ref(false)
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

watch(error, (v) => {
  if (!v) return
  errorShake.value = false
  requestAnimationFrame(() => {
    errorShake.value = true
  })
})

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
  <AuthPageShell title="登录" lede="使用用户名与密码进入平台。">
    <form class="auth-form ds-stack" @submit.prevent="onSubmit">
      <p v-if="error" class="ds-form-error" :class="{ 'auth-shake': errorShake }">{{ error }}</p>
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

    <template #foot>
      没有账号？
      <RouterLink to="/register">去注册</RouterLink>
    </template>
  </AuthPageShell>
</template>
