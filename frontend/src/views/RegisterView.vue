<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AuthPageShell from '../components/AuthPageShell.vue'
import { useAuthStore } from '../stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const errorShake = ref(false)
const loading = ref(false)
const auth = useAuthStore()
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
  <AuthPageShell title="注册" lede="用户名 3–32 位字母数字下划线；密码至少 6 位。">
    <form class="auth-form ds-stack" @submit.prevent="onSubmit">
      <p v-if="error" class="ds-form-error" :class="{ 'auth-shake': errorShake }">{{ error }}</p>
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

    <template #foot>
      已有账号？
      <RouterLink to="/login">去登录</RouterLink>
    </template>
  </AuthPageShell>
</template>
