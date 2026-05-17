import { apiFetch } from './client'
import type {
  FeedbackAdminItem,
  FeedbackAdminUpdate,
  FeedbackCreate,
  FeedbackPublic,
} from '../types/feedback'

export async function submitFeedback(body: FeedbackCreate): Promise<FeedbackPublic> {
  return apiFetch<FeedbackPublic>('/api/v1/feedback', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function listMyFeedback(): Promise<FeedbackPublic[]> {
  return apiFetch<FeedbackPublic[]>('/api/v1/feedback/mine')
}

export async function adminListFeedback(status?: string): Promise<FeedbackAdminItem[]> {
  const q = status ? `?status_filter=${encodeURIComponent(status)}` : ''
  return apiFetch<FeedbackAdminItem[]>(`/api/v1/admin/feedback${q}`)
}

export async function adminUpdateFeedback(
  id: number,
  body: FeedbackAdminUpdate,
): Promise<FeedbackPublic> {
  return apiFetch<FeedbackPublic>(`/api/v1/admin/feedback/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}
