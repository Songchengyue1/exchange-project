export interface CategoryPublic {
  id: number
  name: string
  sort_order: number
}

export interface SellerBrief {
  id: number
  nickname: string
  avatar_url: string | null
  rating_avg: number | null
}

export interface ProductListItem {
  id: number
  title: string
  price: number
  condition: string
  trade_type: string
  stock: number
  category_id: number
  category_name: string
  cover_image: string | null
  is_hot: boolean
  seller: SellerBrief
  created_at: string
}

export interface ProductImageOut {
  id: number
  path: string
  sort_order: number
}

export interface ProductDetail {
  id: number
  title: string
  description: string
  price: number
  condition: string
  trade_type: string
  stock: number
  status: string
  reject_reason: string | null
  category_id: number
  category_name: string
  images: ProductImageOut[]
  is_hot: boolean
  seller: SellerBrief
  created_at: string
  updated_at: string
}

export interface ProductPage {
  items: ProductListItem[]
  total: number
  page: number
  page_size: number
}
