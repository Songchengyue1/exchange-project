import type {
  ProductDetail,
  ProductFavoriteItem,
  ProductFavoriteState,
  ProductPage,
} from '../types/product'
import { apiFetch } from './client'

export async function listProducts(params: {
  page?: number
  page_size?: number
  category_id?: number
  q?: string
  sort?: string
}): Promise<ProductPage> {
  const sp = new URLSearchParams()
  if (params.page) sp.set('page', String(params.page))
  if (params.page_size) sp.set('page_size', String(params.page_size))
  if (params.category_id != null) sp.set('category_id', String(params.category_id))
  if (params.q) sp.set('q', params.q)
  if (params.sort) sp.set('sort', params.sort)
  const qs = sp.toString()
  const path = qs ? `/api/v1/products?${qs}` : '/api/v1/products'
  return apiFetch<ProductPage>(path, { method: 'GET', auth: false })
}

export async function getProduct(id: number): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(`/api/v1/products/${id}`, { method: 'GET' })
}

export async function listMyProducts(status?: string): Promise<ProductDetail[]> {
  const qs = status ? `?status_filter=${encodeURIComponent(status)}` : ''
  return apiFetch<ProductDetail[]>(`/api/v1/products/mine${qs}`, { method: 'GET', auth: true })
}

export async function createProduct(body: {
  category_id: number
  title: string
  description: string
  price: number
  condition: string
  trade_type: string
  stock: number
}): Promise<ProductDetail> {
  return apiFetch<ProductDetail>('/api/v1/products', {
    method: 'POST',
    body: JSON.stringify(body),
    auth: true,
  })
}

export async function updateProduct(
  id: number,
  body: Partial<{
    category_id: number
    title: string
    description: string
    price: number
    condition: string
    trade_type: string
    stock: number
  }>,
): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(`/api/v1/products/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
    auth: true,
  })
}

export async function offlineProduct(id: number): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(`/api/v1/products/${id}/offline`, { method: 'POST', auth: true })
}

export async function uploadProductImages(id: number, files: File[]): Promise<ProductDetail> {
  const fd = new FormData()
  for (const f of files) {
    fd.append('files', f)
  }
  return apiFetch<ProductDetail>(`/api/v1/products/${id}/images`, {
    method: 'POST',
    body: fd,
    auth: true,
  })
}

export async function favoriteProduct(id: number): Promise<ProductFavoriteState> {
  return apiFetch<ProductFavoriteState>(`/api/v1/products/${id}/favorite`, {
    method: 'POST',
    auth: true,
  })
}

export async function unfavoriteProduct(id: number): Promise<ProductFavoriteState> {
  return apiFetch<ProductFavoriteState>(`/api/v1/products/${id}/favorite`, {
    method: 'DELETE',
    auth: true,
  })
}

export async function listFavoriteProducts(): Promise<ProductFavoriteItem[]> {
  return apiFetch<ProductFavoriteItem[]>('/api/v1/products/favorites', {
    method: 'GET',
    auth: true,
  })
}
