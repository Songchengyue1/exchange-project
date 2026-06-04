<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import UserAvatar from '../components/UserAvatar.vue'
import { showConfirm } from '../composables/useConfirm'
import { APP_ICON, APP_NAME } from '../constants/app'
import { useAuthStore } from '../stores/auth'

const health = ref('检查中…')
const navOpen = ref(false)
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

async function onLogout() {
  const ok = await showConfirm({
    title: '退出登录',
    message: '确定要退出当前账号吗？',
    confirmText: '退出',
    cancelText: '取消',
    variant: 'danger',
  })
  if (!ok) return
  auth.logout()
  navOpen.value = false
  void router.push('/login')
}

onMounted(async () => {
  try {
    const res = await fetch('/health')
    const data = await res.json()
    health.value = data.status === 'ok' ? '后端在线' : JSON.stringify(data)
  } catch {
    health.value = '后端未启动'
  }
  if (auth.token && !auth.user) {
    await auth.hydrate()
  }
})

watch(
  () => route.fullPath,
  () => {
    navOpen.value = false
  },
)
</script>

<template>
  <div class="page">
    <header class="top-nav">
      <div class="top-nav__inner">
        <RouterLink class="brand" to="/" @click="navOpen = false">
          <img class="brand__icon" :src="APP_ICON" :alt="APP_NAME" width="36" height="36" />
          <span class="brand__text">{{ APP_NAME }}</span>
        </RouterLink>

        <nav class="top-nav__links" :class="{ 'top-nav__links--open': navOpen }">
          <div class="top-nav__links-stripe ds-m-stripe" aria-hidden="true" />
          <RouterLink to="/" :class="{ active: route.name === 'home' }">首页</RouterLink>
          <RouterLink
            to="/products"
            :class="{ active: route.name === 'products' || route.name === 'product-detail' }"
          >
            商品
          </RouterLink>
          <RouterLink
            v-if="auth.isAuthenticated"
            to="/my-products"
            :class="{ active: route.name === 'my-products' }"
          >
            我的商品
          </RouterLink>
          <RouterLink
            v-if="auth.isAuthenticated"
            to="/favorites"
            :class="{ active: route.name === 'favorites' }"
          >
            收藏
          </RouterLink>
          <RouterLink to="/sell" :class="{ active: route.name === 'sell' }">发布</RouterLink>
          <RouterLink to="/orders" :class="{ active: route.name === 'orders' }">订单</RouterLink>
          <RouterLink
            v-if="auth.isAuthenticated"
            to="/feedback"
            :class="{ active: route.name === 'feedback' || route.name === 'feedback-mine' }"
          >
            反馈
          </RouterLink>
          <RouterLink
            v-if="auth.user?.role === 'admin'"
            to="/admin"
            :class="{ active: String(route.name ?? '').startsWith('admin-') }"
          >
            管理后台
          </RouterLink>
        </nav>

        <div class="top-nav__actions">
          <span class="health-pill ds-hover-pill" data-testid="health">{{ health }}</span>
          <template v-if="auth.isAuthenticated">
            <RouterLink to="/me" class="user-chip">
              <UserAvatar
                :src="auth.user?.avatar_url"
                :name="auth.user?.nickname ?? '用户'"
                size="sm"
              />
              <span class="user-chip__name">{{ auth.user?.nickname ?? '…' }}</span>
            </RouterLink>
            <button type="button" class="link-btn ds-label-caps" @click="onLogout">退出</button>
          </template>
          <template v-else>
            <RouterLink class="link-btn ds-label-caps" to="/login">登录</RouterLink>
            <RouterLink class="ds-btn ds-btn--compact" to="/register">注册</RouterLink>
          </template>
        </div>

        <button
          type="button"
          class="nav-toggle ds-label-caps"
          aria-label="打开菜单"
          @click="navOpen = !navOpen"
        >
          Menu
        </button>
      </div>
    </header>

    <div class="ds-m-stripe" aria-hidden="true" />

    <main class="main">
      <RouterView />
    </main>

    <footer class="site-footer">
      <div class="site-footer__inner">
        <div class="site-footer__col">
          <p class="site-footer__head ds-label-caps">Platform</p>
          <RouterLink to="/about" :class="{ active: route.name === 'about' }">关于</RouterLink>
          <RouterLink to="/help" :class="{ active: route.name === 'help' }">帮助</RouterLink>
        </div>
        <div class="site-footer__col">
          <p class="site-footer__head ds-label-caps">Legal</p>
          <RouterLink to="/privacy" :class="{ active: route.name === 'privacy' }">隐私</RouterLink>
          <RouterLink to="/terms" :class="{ active: route.name === 'terms' }">条款</RouterLink>
        </div>
        <div class="site-footer__col site-footer__col--wide">
          <p class="site-footer__note">
            界面样式遵循 docs/DESIGN.md；用户与 JWT 接口已接入 /api/v1。
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  min-height: 100svh;
  background: var(--color-canvas);
  color: var(--color-body);
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 64px;
  background: var(--color-canvas);
  border-bottom: 1px solid var(--color-hairline);
}

.top-nav__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--space-lg);
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-on-dark);
  flex-shrink: 0;
  text-decoration: none;
  transition: transform var(--duration-fast) var(--ease-out), opacity var(--duration-fast) ease;
}

.brand:hover {
  transform: translateX(3px);
  opacity: 0.92;
}

.brand__icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  object-fit: cover;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  transition: transform var(--duration-fast) var(--ease-out);
}

.brand:hover .brand__icon {
  transform: scale(1.04);
}

.brand__text {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.nav-toggle {
  display: none;
  flex-shrink: 0;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-surface-card);
  border: 1px solid var(--color-hairline);
  color: var(--color-on-dark);
  border-radius: 0;
  cursor: pointer;
  transition:
    border-color var(--duration-fast) ease,
    background-color var(--duration-fast) ease,
    transform var(--duration-fast) var(--ease-out);
}

.nav-toggle:hover {
  border-color: var(--color-on-dark);
  background: var(--color-surface-elevated);
  transform: translateY(-1px);
}

.top-nav__links {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  margin-left: auto;
  margin-right: var(--space-md);
}

.top-nav__links a {
  position: relative;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.4;
  letter-spacing: 0.5px;
  color: var(--color-body-strong);
  text-decoration: none;
  transition: color var(--duration-fast) ease, transform var(--duration-fast) var(--ease-out);
}

.top-nav__links a::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -4px;
  width: 100%;
  height: 1px;
  background: var(--color-on-dark);
  transform: scaleX(0);
  transform-origin: left center;
  transition: transform var(--duration-normal) var(--ease-out);
}

.top-nav__links a.active,
.top-nav__links a:hover {
  color: var(--color-on-dark);
}

.top-nav__links a:hover {
  transform: translateY(-1px);
}

.top-nav__links a:hover::after,
.top-nav__links a.active::after {
  transform: scaleX(1);
}

.top-nav__actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-shrink: 0;
}

.health-pill {
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0.5px;
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--color-hairline);
  color: var(--color-muted);
  background: var(--color-surface-soft);
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  max-width: 160px;
  padding: 4px 8px 4px 4px;
  text-decoration: none;
  color: var(--color-on-dark);
  border: 1px solid transparent;
  transition:
    border-color var(--duration-fast) ease,
    background-color var(--duration-fast) ease,
    transform var(--duration-fast) var(--ease-out);
}

.user-chip:hover {
  border-color: var(--color-hairline);
  background: var(--color-surface-elevated);
  transform: translateY(-1px);
}

.user-chip__name {
  font-size: 14px;
  font-weight: 400;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.link-btn {
  position: relative;
  background: none;
  border: none;
  color: var(--color-body-strong);
  cursor: pointer;
  text-decoration: none;
  padding: 0;
  font: inherit;
  transition: color var(--duration-fast) ease;
}

.link-btn::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -2px;
  width: 100%;
  height: 1px;
  background: currentColor;
  transform: scaleX(0);
  transform-origin: left center;
  transition: transform var(--duration-normal) var(--ease-out);
}

.link-btn:hover {
  color: var(--color-on-dark);
}

.link-btn:hover::after {
  transform: scaleX(1);
}

.ds-btn--compact {
  height: 40px;
  padding: 0 20px;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.top-nav__links-stripe {
  display: none;
}

@media (max-width: 1023px) {
  .health-pill {
    display: none;
  }
}

@media (max-width: 767px) {
  .nav-toggle {
    display: inline-flex;
  }

  .top-nav__links-stripe {
    display: block;
    width: calc(100% + 2 * var(--space-lg));
    margin: calc(-1 * var(--space-lg)) calc(-1 * var(--space-lg)) var(--space-md);
  }

  .top-nav__links {
    position: fixed;
    inset: 64px 0 0;
    flex-direction: column;
    align-items: flex-start;
    gap: 0;
    padding: var(--space-lg);
    background: var(--color-canvas);
    border-top: 1px solid var(--color-hairline);
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    margin: 0;
  }

  .top-nav__links--open {
    transform: translateX(0);
  }

  .top-nav__links a {
    width: 100%;
    padding: var(--space-md) 0;
    border-bottom: 1px solid var(--color-hairline);
  }

  .top-nav__actions {
    margin-left: auto;
  }

  .user-chip__name {
    max-width: 72px;
  }
}

.main {
  flex: 1;
}

.site-footer {
  border-top: 1px solid var(--color-hairline);
  padding: var(--space-xxl) var(--space-lg);
  background: var(--color-canvas);
  color: var(--color-body);
}

.site-footer__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  display: grid;
  gap: var(--space-xl);
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .site-footer__inner {
    grid-template-columns: repeat(2, 1fr) minmax(0, 2fr);
  }
}

.site-footer__col {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
}

.site-footer__col a {
  color: var(--color-body);
  text-decoration: none;
  transition: color var(--duration-fast) ease, transform var(--duration-fast) var(--ease-out);
}

.site-footer__col a:hover {
  color: var(--color-on-dark);
  transform: translateX(4px);
}

.site-footer__head {
  margin: 0 0 var(--space-xs);
  color: var(--color-muted);
}

.site-footer__note {
  margin: 0;
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0.5px;
  color: var(--color-muted);
  max-width: 48ch;
}
</style>
