<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { APP_ICON, APP_NAME } from '../constants/app'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth = useAuthStore()

const nav = [
  { name: 'admin-products', label: '商品审核', to: '/admin/products' },
  { name: 'admin-users', label: '用户管理', to: '/admin/users' },
  { name: 'admin-categories', label: '分类管理', to: '/admin/categories' },
  { name: 'admin-orders', label: '订单监管', to: '/admin/orders' },
  { name: 'admin-feedback', label: '反馈管理', to: '/admin/feedback' },
]

const pageTitle = computed(() => {
  const item = nav.find((n) => n.name === route.name)
  return item?.label ?? '管理后台'
})

onMounted(async () => {
  if (auth.token && !auth.user) {
    await auth.hydrate()
  }
})
</script>

<template>
  <div class="admin">
    <aside class="admin__side">
      <RouterLink class="admin__brand" to="/">
        <img class="admin__brand-icon" :src="APP_ICON" :alt="APP_NAME" width="32" height="32" />
        <span>管理后台</span>
      </RouterLink>
      <nav class="admin__nav">
        <RouterLink
          v-for="item in nav"
          :key="item.name"
          :to="item.to"
          class="admin__nav-link"
          :class="{ 'admin__nav-link--on': route.name === item.name }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
      <RouterLink class="admin__back ds-label-caps" to="/">← 返回前台</RouterLink>
    </aside>

    <div class="admin__main">
      <header class="admin__head">
        <div class="admin__head-row">
          <p class="admin__eyebrow ds-label-caps">Admin</p>
          <p v-if="auth.user" class="admin__who ds-label-caps">
            {{ auth.user.nickname }}（{{ auth.user.username }}） · {{ auth.user.role }}
          </p>
        </div>
        <h1 class="admin__title">{{ pageTitle }}</h1>
      </header>
      <div class="admin__stripe ds-m-stripe" aria-hidden="true" />
      <div class="admin__content">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin {
  display: flex;
  min-height: calc(100svh - 64px);
  background: var(--color-canvas);
}

.admin__side {
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-hairline);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  background: var(--color-surface-soft);
}

.admin__brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 15px;
  color: var(--color-on-dark);
  text-decoration: none;
}

.admin__brand-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.admin__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.admin__nav-link {
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--color-body-strong);
  text-decoration: none;
  transition:
    background-color var(--duration-fast) ease,
    color var(--duration-fast) ease;
}

.admin__nav-link:hover {
  background: var(--color-surface-elevated);
  color: var(--color-on-dark);
}

.admin__nav-link--on {
  background: var(--color-on-dark);
  color: var(--color-canvas);
  font-weight: 500;
}

.admin__back {
  font-size: 12px;
  color: var(--color-muted);
  text-decoration: none;
}

.admin__back:hover {
  color: var(--color-on-dark);
}

.admin__main {
  flex: 1;
  min-width: 0;
  padding: var(--space-xl) var(--space-lg);
}

.admin__head {
  margin-bottom: var(--space-md);
}

.admin__head-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-md);
}

.admin__eyebrow {
  margin: 0 0 var(--space-xs);
  color: var(--color-muted);
}

.admin__who {
  margin: 0 0 var(--space-xs);
  color: var(--color-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 52ch;
}

.admin__title {
  margin: 0;
  font-size: clamp(22px, 3vw, 28px);
  font-weight: 700;
  color: var(--color-on-dark);
}

.admin__stripe {
  margin-bottom: var(--space-xl);
}

.admin__content {
  max-width: 960px;
}

@media (max-width: 767px) {
  .admin {
    flex-direction: column;
  }

  .admin__side {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-hairline);
  }

  .admin__nav {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
</style>
