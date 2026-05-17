import type { UserAddress, UserAddressInput } from '../types/address'
import { apiFetch } from './client'

export function listAddresses() {
  return apiFetch<UserAddress[]>('/api/v1/users/me/addresses', { method: 'GET', auth: true })
}

export function createAddress(body: UserAddressInput) {
  return apiFetch<UserAddress>('/api/v1/users/me/addresses', {
    method: 'POST',
    body: JSON.stringify(body),
    auth: true,
  })
}

export function updateAddress(id: number, body: Partial<UserAddressInput>) {
  return apiFetch<UserAddress>(`/api/v1/users/me/addresses/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
    auth: true,
  })
}

export function deleteAddress(id: number) {
  return apiFetch<void>(`/api/v1/users/me/addresses/${id}`, { method: 'DELETE', auth: true })
}

export function setDefaultAddress(id: number) {
  return apiFetch<UserAddress>(`/api/v1/users/me/addresses/${id}/default`, {
    method: 'POST',
    auth: true,
  })
}
