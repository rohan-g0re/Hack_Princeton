'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { getOrderDetail, OrderDetailResponse } from '@/lib/api'
import { Header } from '@/components/Header'

export default function OrderDetailPage() {
  const { orderId } = useParams()
  const { token } = useAuth()
  const router = useRouter()
  const [orderData, setOrderData] = useState<OrderDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token || !orderId) return

    getOrderDetail(orderId as string, token)
      .then(setOrderData)
      .finally(() => setLoading(false))
  }, [token, orderId])

  if (loading) return (
    <div className="min-h-screen py-12 px-4" style={{ background: '#F5F5F5' }}>
      <div className="card text-center">Loading...</div>
    </div>
  )
  
  if (!orderData) return (
    <div className="min-h-screen py-12 px-4" style={{ background: '#F5F5F5' }}>
      <div className="card text-center">Order not found</div>
    </div>
  )

  const { order, items } = orderData

  return (
    <div className="min-h-screen py-12 px-4" style={{ background: '#F5F5F5' }}>
      <div className="max-w-4xl mx-auto">
        <Header />
        
        <div className="card max-w-2xl mx-auto">
          {/* Success Icon */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-4">
              <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold mb-2" style={{ color: '#3E2723' }}>
              Order Confirmed!
            </h2>
            <p className="text-gray-600 mb-4">
              Your items have been added to your {order.store_name} cart.
            </p>
            
            {/* Platform Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg font-semibold mb-6">
              <span className="text-xl">🚗</span>
              <span>{order.store_name}</span>
            </div>
          </div>
          
          {/* Order Summary */}
          <div className="mb-6">
            <h3 className="font-bold text-lg mb-4" style={{ color: '#3E2723' }}>
              Order Summary
            </h3>
            
            <div className="space-y-3 mb-4">
              {items.map((item, idx) => (
                <div key={idx} className="flex justify-between text-sm">
                  <div className="flex-1">
                    <div className="font-medium text-gray-800">{idx + 1}. {item.name}</div>
                    <div className="text-xs text-gray-500">{item.quantity || '1'} {item.unit || ''}</div>
                  </div>
                  <div className="font-semibold text-gray-700">
                    ${item.price?.toFixed(2) || '0.00'}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Totals */}
            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between font-bold text-lg">
                <span>Total:</span>
                <span>${order.total?.toFixed(2) || '0.00'}</span>
              </div>
              <div className="text-xs text-gray-500">
                Date: {new Date(order.created_at).toLocaleString('en-US', {
                  month: 'numeric',
                  day: 'numeric',
                  year: 'numeric',
                  hour: 'numeric',
                  minute: '2-digit',
                  hour12: true
                })}
              </div>
              {order.payment_method && (
                <div className="text-xs text-gray-500">
                  Payment: {order.payment_method}
                </div>
              )}
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex gap-3 justify-center">
            <button className="btn-primary flex items-center gap-2">
              <span>📥</span>
              <span>Download Receipt</span>
            </button>
            <button 
              onClick={() => router.push('/')}
              className="px-6 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50"
            >
              ← Back to Home
            </button>
          </div>
        </div>
        
        {/* Footer */}
        <footer className="text-center mt-12 text-gray-500 text-sm">
          © 2025 MealPilot
        </footer>
      </div>
    </div>
  )
}

