export interface AdminUserItem {
  id: number
  username: string
  nickname: string
  role: string
  is_disabled: boolean
  phone: string | null
  rating_avg: number | null
  created_at: string
}

export interface AdminOrderItem {
  id: number
  product_id: number
  product_title: string
  amount: number
  quantity: number
  status: string
  trade_type: string
  refund_reason: string | null
  buyer_id: number
  buyer_nickname: string
  seller_id: number
  seller_nickname: string
  created_at: string
  updated_at: string
}

export interface AdminAuditLogItem {
  id: number
  admin_id: number
  admin_username: string
  action: string
  target_type: string
  target_id: number
  detail: string | null
  created_at: string
}
