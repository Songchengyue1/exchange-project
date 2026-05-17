import type { CategoryPublic } from '../types/product'
import { apiFetch } from './client'

export async function listCategories(): Promise<CategoryPublic[]> {
  return apiFetch<CategoryPublic[]>('/api/v1/categories', { method: 'GET', auth: false })
}
