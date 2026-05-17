export interface ReviewPublic {
  id: number
  order_id: number
  product_id: number
  rating: number
  comment: string | null
  buyer_nickname: string
  created_at: string
}

export interface ReviewCreate {
  rating: number
  comment?: string
}
