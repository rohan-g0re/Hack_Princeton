'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { getOrders, OrderSummary } from '@/lib/api'
import { OrderCard } from '@/components/OrderCard'
import { Header } from '@/components/Header'
import { Navigation } from '@/components/Navigation'

export default function OrdersPage() {
  const { token } = useAuth()
  const [orders, setOrders] = useState<OrderSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) return

    getOrders(token).then(setOrders).finally(() => setLoading(false))
  }, [token])

  return (
    <div className="min-h-screen py-12 px-4" style={{ background: '#F5F5F5' }}>
      <div className="max-w-6xl mx-auto">
        <Header />
        <Navigation />
        
        <div className="card">
          <h1 className="text-3xl font-bold mb-6" style={{ color: '#3E2723' }}>
            Your Orders
          </h1>
          
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 mx-auto mb-4" style={{ borderColor: '#C9915C' }}></div>
              <p className="text-gray-600">Loading orders...</p>
            </div>
          ) : orders.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📦</div>
              <p className="text-gray-600 text-lg mb-2">No orders yet</p>
              <p className="text-gray-500 text-sm">Your order history will appear here</p>
            </div>
          ) : (
            <div className="space-y-4">
              {orders.map((order) => (
                <OrderCard 
                  key={order.id}
                  id={order.id}
                  storeName={order.store_name}
                  total={order.total}
                  currency={order.currency}
                  thumbnailUrl={order.receipt_thumbnail_url}
                  createdAt={order.created_at}
                />
              ))}
            </div>
          )}
        </div>
        
        <footer className="text-center mt-12 text-gray-500 text-sm">
          © 2025 MealPilot
        </footer>
      </div>
    </div>
  )
}

