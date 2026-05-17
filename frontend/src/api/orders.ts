import type { OrderDetail, OrderListItem } from '../types/order'
import { apiFetch } from './client'

export async function listBuyerOrders(status?: string): Promise<OrderListItem[]> {
  const qs = status ? `?status_filter=${encodeURIComponent(status)}` : ''
  return apiFetch<OrderListItem[]>(`/api/v1/orders${qs}`, { method: 'GET', auth: true })
}

export async function listSellerOrders(status?: string): Promise<OrderListItem[]> {
  const qs = status ? `?status_filter=${encodeURIComponent(status)}` : ''
  return apiFetch<OrderListItem[]>(`/api/v1/orders/sales${qs}`, { method: 'GET', auth: true })
}

export async function getOrder(id: number): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/api/v1/orders/${id}`, { method: 'GET', auth: true })
}

export async function createOrder(body: {
  product_id: number
  quantity: number
  remark?: string
  shipping_address_id?: number
}): Promise<OrderDetail> {
  return apiFetch<OrderDetail>('/api/v1/orders', {
    method: 'POST',
    body: JSON.stringify(body),
    auth: true,
  })
}

export async function mockPayOrder(id: number, success: boolean): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/api/v1/orders/${id}/mock-pay`, {
    method: 'POST',
    body: JSON.stringify({ success }),
    auth: true,
  })
}

export async function confirmReceipt(id: number): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/api/v1/orders/${id}/confirm-receipt`, {
    method: 'POST',
    auth: true,
  })
}

export async function cancelOrder(id: number): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/api/v1/orders/${id}/cancel`, {
    method: 'POST',
    auth: true,
  })
}

export async function requestRefund(id: number, reason: string): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/api/v1/orders/${id}/request-refund`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
    auth: true,
  })
}
