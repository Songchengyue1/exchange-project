import type { CategoryPublic } from '../types/product'
import type { AdminAuditLogItem, AdminOrderItem, AdminUserItem } from '../types/admin'
import type { ProductDetail } from '../types/product'
import type { OrderDetail } from '../types/order'
import { apiFetch } from './client'

export async function listPendingProducts(): Promise<ProductDetail[]> {
  return apiFetch<ProductDetail[]>('/api/v1/admin/products/pending', { method: 'GET', auth: true })
}

export async function approveProduct(id: number): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(`/api/v1/admin/products/${id}/approve`, { method: 'POST', auth: true })
}

export async function rejectProduct(id: number, reason: string): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(`/api/v1/admin/products/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
    auth: true,
  })
}

export async function listAdminCategories(): Promise<CategoryPublic[]> {
  return apiFetch<CategoryPublic[]>('/api/v1/admin/categories', { method: 'GET', auth: true })
}

export async function createAdminCategory(body: { name: string; sort_order: number }) {
  return apiFetch<CategoryPublic>('/api/v1/admin/categories', {
    method: 'POST',
    body: JSON.stringify(body),
    auth: true,
  })
}

export async function updateAdminCategory(
  id: number,
  body: { name?: string; sort_order?: number },
) {
  return apiFetch<CategoryPublic>(`/api/v1/admin/categories/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
    auth: true,
  })
}

export async function deleteAdminCategory(id: number) {
  return apiFetch<void>(`/api/v1/admin/categories/${id}`, { method: 'DELETE', auth: true })
}

export async function listAdminUsers(): Promise<AdminUserItem[]> {
  return apiFetch<AdminUserItem[]>('/api/v1/admin/users', { method: 'GET', auth: true })
}

export async function patchAdminUser(id: number, body: { is_disabled: boolean }) {
  return apiFetch<AdminUserItem>(`/api/v1/admin/users/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
    auth: true,
  })
}

export async function resetAdminUserPassword(id: number, new_password: string) {
  return apiFetch<void>(`/api/v1/admin/users/${id}/reset-password`, {
    method: 'POST',
    body: JSON.stringify({ new_password }),
    auth: true,
  })
}

export async function listAdminOrders(status?: string): Promise<AdminOrderItem[]> {
  const qs = status ? `?status_filter=${encodeURIComponent(status)}` : ''
  return apiFetch<AdminOrderItem[]>(`/api/v1/admin/orders${qs}`, { method: 'GET', auth: true })
}

export async function approveAdminRefund(orderId: number): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/api/v1/admin/orders/${orderId}/refund-approve`, {
    method: 'POST',
    auth: true,
  })
}

export async function rejectAdminRefund(orderId: number, note?: string): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/api/v1/admin/orders/${orderId}/refund-reject`, {
    method: 'POST',
    body: JSON.stringify({ note: note ?? null }),
    auth: true,
  })
}

export async function listAdminAuditLogs(): Promise<AdminAuditLogItem[]> {
  return apiFetch<AdminAuditLogItem[]>('/api/v1/admin/audit-logs', { method: 'GET', auth: true })
}
