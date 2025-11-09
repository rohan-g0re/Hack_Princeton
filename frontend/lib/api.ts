/**
 * Backend API Client
 * Handles communication with FastAPI backend for Phase 3 features
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export type OrderSummary = {
  id: string
  store_name: string
  total: number
  currency: string
  receipt_thumbnail_url: string | null
  created_at: string
}

export type OrderDetail = {
  id: string
  store_name: string
  subtotal: number
  tax: number
  total: number
  currency: string
  receipt_image_url: string | null
  created_at: string
}

export type OrderItem = {
  platform: string
  item_name: string
  quantity: number
  unit: string | null
  unit_price: number
  total: number
}

export type OrderDetailResponse = {
  order: OrderDetail
  items: OrderItem[]
}

async function fetchAPI(endpoint: string, token: string, options?: RequestInit) {
  const res = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `API error: ${res.status}`)
  }

  return res.json()
}

export async function importKnotJSONs(token: string) {
  return fetchAPI('/api/orders/import-knot', token, { method: 'POST' })
}

export async function getOrders(token: string, limit = 50, offset = 0): Promise<OrderSummary[]> {
  return fetchAPI(`/api/orders?limit=${limit}&offset=${offset}`, token)
}

export async function getOrderDetail(orderId: string, token: string): Promise<OrderDetailResponse> {
  return fetchAPI(`/api/orders/${orderId}`, token)
}

export async function generateReceipt(orderId: string, token: string) {
  return fetchAPI(`/api/receipts/generate/${orderId}`, token, { method: 'POST' })
}

export async function refreshProfiling(token: string) {
  return fetchAPI('/api/profiling/refresh', token, { method: 'POST' })
}

export async function getPreferences(token: string): Promise<string[]> {
  return fetchAPI('/api/profiling/preferences', token)
}

