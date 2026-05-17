import { apiFetch } from './client'
import type { ReviewCreate, ReviewPublic } from '../types/review'

export async function createOrderReview(orderId: number, body: ReviewCreate): Promise<ReviewPublic> {
  return apiFetch<ReviewPublic>(`/api/v1/orders/${orderId}/review`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function listMyReviews(): Promise<ReviewPublic[]> {
  return apiFetch<ReviewPublic[]>('/api/v1/reviews/mine')
}
