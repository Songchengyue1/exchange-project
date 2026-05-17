export interface OrderUserBrief {
  id: number
  nickname: string
  avatar_url: string | null
}

export interface OrderProductBrief {
  id: number
  title: string
  cover_image: string | null
  trade_type: string
}

import type { ReviewPublic } from './review'

export interface OrderDetail {
  id: number
  product_id: number
  quantity: number
  unit_price: number
  amount: number
  product_title: string
  trade_type: string
  status: string
  remark: string | null
  shipping_address_snapshot: string | null
  payment_ref: string | null
  buyer: OrderUserBrief
  seller: OrderUserBrief
  product: OrderProductBrief
  created_at: string
  updated_at: string
  paid_at: string | null
  completed_at: string | null
  refund_reason: string | null
  buyer_has_reviewed: boolean
  review: ReviewPublic | null
  payment_expires_at: string | null
}

export interface OrderListItem {
  id: number
  product_id: number
  product_title: string
  amount: number
  quantity: number
  trade_type: string
  status: string
  cover_image: string | null
  counterparty_nickname: string
  created_at: string
  payment_expires_at: string | null
}
