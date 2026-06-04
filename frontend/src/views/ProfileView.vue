<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import * as authApi from '../api/auth'
import AddressSelector from '../components/AddressSelector.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { showConfirm } from '../composables/useConfirm'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const nickname = ref('')
const phone = ref('')
const message = ref('')
const error = ref('')
const loading = ref(false)
const avatarBusy = ref(false)

function syncFromUser() {
  const u = auth.user
  if (!u) return
  nickname.value = u.nickname
  phone.value = u.phone ?? ''
}

onMounted(() => {
  syncFromUser()
})

watch(
  () => auth.user,
  () => {
    syncFromUser()
  },
)

async function save() {
  const ok = await showConfirm({
    title: '保存资料',
    message: '确定要保存昵称与手机号吗？',
    confirmText: '保存',
  })
  if (!ok) return

  error.value = ''
  message.value = ''
  loading.value = true
  try {
    await authApi.updateMe({
      nickname: nickname.value.trim(),
      phone: phone.value.trim(),
    })
    await auth.refreshProfile()
    message.value = '已保存'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    loading.value = false
  }
}

async function onAvatar(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  avatarBusy.value = true
  error.value = ''
  message.value = ''
  try {
    await authApi.uploadAvatar(file)
    await auth.refreshProfile()
    message.value = '头像已更新'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '上传失败'
  } finally {
    avatarBusy.value = false
    input.value = ''
  }
}
</script>

<template>
  <section class="wrap">
    <p class="eyebrow ds-label-caps">Account</p>
    <h1 class="title">个人中心</h1>
    <p class="lede">维护昵称、手机号与收货地址；头像支持 JPG / PNG / WEBP，最大 2MB。</p>

    <div class="avatar-row">
      <UserAvatar
        :src="auth.user?.avatar_url"
        :name="auth.user?.nickname ?? '用户'"
        size="lg"
      />
      <label class="ds-btn ds-btn--file">
        {{ avatarBusy ? '上传中…' : '更换头像' }}
        <input type="file" accept="image/jpeg,image/png,image/webp" hidden @change="onAvatar" />
      </label>
    </div>

    <form class="form" @submit.prevent="save">
      <p v-if="message" class="msg">{{ message }}</p>
      <p v-if="error" class="ds-form-error">{{ error }}</p>

      <div class="ds-field">
        <label class="ds-label" for="nick">昵称</label>
        <input id="nick" v-model="nickname" class="ds-input" required maxlength="64" />
      </div>
      <div class="ds-field">
        <label class="ds-label" for="phone">手机</label>
        <input id="phone" v-model="phone" class="ds-input" maxlength="32" />
      </div>
      <button type="submit" class="ds-btn" :disabled="loading">{{ loading ? '保存中…' : '保存资料' }}</button>
    </form>

    <section class="address-section">
      <AddressSelector mode="manage" />
    </section>
  </section>
</template>

<style scoped>
.wrap {
  max-width: 640px;
  margin: 0 auto;
  padding: var(--space-section) var(--space-lg);
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
  font-weight: 400;
  line-height: 1.5;
  color: var(--color-body);
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
}

.ds-btn--file {
  cursor: pointer;
  position: relative;
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-xxl);
  padding-bottom: var(--space-xxl);
  border-bottom: 1px solid var(--color-hairline);
}

.address-section {
  margin-top: var(--space-md);
}

.msg {
  margin: 0;
  font-size: 14px;
  font-weight: 400;
  color: var(--color-success);
}
</style>
