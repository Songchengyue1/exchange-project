export interface UserAddress {
  id: number
  label: string
  contact_name: string
  phone: string
  province: string | null
  city: string | null
  district: string | null
  detail: string
  poi_name: string | null
  latitude: number | null
  longitude: number | null
  is_default: boolean
  formatted: string
  created_at: string
  updated_at: string
}

export interface UserAddressInput {
  label: string
  contact_name: string
  phone: string
  province?: string | null
  city?: string | null
  district?: string | null
  detail: string
  poi_name?: string | null
  latitude?: number | null
  longitude?: number | null
  is_default?: boolean
}
