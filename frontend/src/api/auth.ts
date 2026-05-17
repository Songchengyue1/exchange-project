import type { TokenResponse, UserPublic } from '../types/user'
import { apiFetch } from './client'

export async function register(username: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    auth: false,
  })
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    auth: false,
  })
}

export async function fetchMe(): Promise<UserPublic> {
  return apiFetch<UserPublic>('/api/v1/users/me', { method: 'GET', auth: true })
}

export async function updateMe(payload: {
  nickname?: string
  phone?: string
  address?: string
}): Promise<UserPublic> {
  return apiFetch<UserPublic>('/api/v1/users/me', {
    method: 'PATCH',
    body: JSON.stringify(payload),
    auth: true,
  })
}

export async function uploadAvatar(file: File): Promise<UserPublic> {
  const fd = new FormData()
  fd.append('file', file)
  return apiFetch<UserPublic>('/api/v1/users/me/avatar', {
    method: 'POST',
    body: fd,
    auth: true,
  })
}
