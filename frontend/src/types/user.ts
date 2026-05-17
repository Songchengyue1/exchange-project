export interface UserPublic {
  id: number
  username: string
  nickname: string
  phone: string | null
  address: string | null
  avatar_url: string | null
  role: string
  rating_avg?: number | null
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserPublic
}
