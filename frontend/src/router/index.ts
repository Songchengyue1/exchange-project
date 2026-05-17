import { createRouter, createWebHistory } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'
import MainLayout from '../layouts/MainLayout.vue'
import AdminCategoriesView from '../views/AdminCategoriesView.vue'
import AdminFeedbackView from '../views/AdminFeedbackView.vue'
import AdminOrdersView from '../views/AdminOrdersView.vue'
import AdminProductsView from '../views/AdminProductsView.vue'
import AdminUsersView from '../views/AdminUsersView.vue'
import FeedbackView from '../views/FeedbackView.vue'
import MyFeedbackView from '../views/MyFeedbackView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import MyProductsView from '../views/MyProductsView.vue'
import OrderCheckoutView from '../views/OrderCheckoutView.vue'
import OrderDetailView from '../views/OrderDetailView.vue'
import OrderListView from '../views/OrderListView.vue'
import OrderPayView from '../views/OrderPayView.vue'
import ProductDetailView from '../views/ProductDetailView.vue'
import ProductListView from '../views/ProductListView.vue'
import ProfileView from '../views/ProfileView.vue'
import RegisterView from '../views/RegisterView.vue'
import SellView from '../views/SellView.vue'
import SitePageView from '../views/SitePageView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', name: 'home', component: HomeView },
        { path: 'about', name: 'about', component: SitePageView, meta: { sitePage: 'about' } },
        { path: 'help', name: 'help', component: SitePageView, meta: { sitePage: 'help' } },
        { path: 'privacy', name: 'privacy', component: SitePageView, meta: { sitePage: 'privacy' } },
        { path: 'terms', name: 'terms', component: SitePageView, meta: { sitePage: 'terms' } },
        { path: 'login', name: 'login', component: LoginView, meta: { guestOnly: true } },
        { path: 'register', name: 'register', component: RegisterView, meta: { guestOnly: true } },
        {
          path: 'me',
          name: 'profile',
          component: ProfileView,
          meta: { requiresAuth: true },
        },
        {
          path: 'sell',
          name: 'sell',
          component: SellView,
          meta: { requiresAuth: true },
        },
        {
          path: 'my-products',
          name: 'my-products',
          component: MyProductsView,
          meta: { requiresAuth: true },
        },
        {
          path: 'feedback',
          name: 'feedback',
          component: FeedbackView,
          meta: { requiresAuth: true },
        },
        {
          path: 'feedback/mine',
          name: 'feedback-mine',
          component: MyFeedbackView,
          meta: { requiresAuth: true },
        },
        {
          path: 'products/:id',
          name: 'product-detail',
          component: ProductDetailView,
        },
        {
          path: 'products',
          name: 'products',
          component: ProductListView,
        },
        {
          path: 'orders/checkout/:productId',
          name: 'order-checkout',
          component: OrderCheckoutView,
          meta: { requiresAuth: true },
        },
        {
          path: 'orders/:id/pay',
          name: 'order-pay',
          component: OrderPayView,
          meta: { requiresAuth: true },
        },
        {
          path: 'orders/:id',
          name: 'order-detail',
          component: OrderDetailView,
          meta: { requiresAuth: true },
        },
        {
          path: 'orders',
          name: 'orders',
          component: OrderListView,
          meta: { requiresAuth: true },
        },
      ],
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        { path: '', redirect: { name: 'admin-products' } },
        { path: 'products', name: 'admin-products', component: AdminProductsView },
        { path: 'users', name: 'admin-users', component: AdminUsersView },
        { path: 'categories', name: 'admin-categories', component: AdminCategoriesView },
        { path: 'orders', name: 'admin-orders', component: AdminOrdersView },
        { path: 'feedback', name: 'admin-feedback', component: AdminFeedbackView },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  const needsAuth = to.matched.some((r) => r.meta.requiresAuth)
  const needsAdmin = to.matched.some((r) => r.meta.requiresAdmin)
  if (needsAuth && !auth.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (needsAdmin) {
    if (!auth.token) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (auth.user?.role !== 'admin') {
      return { name: 'home' }
    }
  }
  if (to.meta.guestOnly && auth.token) {
    return { name: 'home' }
  }
  return true
})

export default router
