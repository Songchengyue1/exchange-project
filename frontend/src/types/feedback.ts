export type FeedbackStatus = 'pending' | 'processing' | 'resolved'

export interface FeedbackPublic {
  id: number
  subject: string
  content: string
  status: FeedbackStatus | string
  admin_reply: string | null
  created_at: string
  updated_at: string
}

export interface FeedbackCreate {
  subject: string
  content: string
}

export interface FeedbackAdminItem extends FeedbackPublic {
  user_id: number
  username: string
  nickname: string
}

export interface FeedbackAdminUpdate {
  status: FeedbackStatus
  admin_reply?: string
}
