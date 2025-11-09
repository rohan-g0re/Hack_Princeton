'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { getOrders, OrderSummary } from '@/lib/api'
import { OrderCard } from '@/components/OrderCard'

export default function OrdersPage() {
  const { token } = useAuth()
  const [orders, setOrders] = useState<OrderSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) return

    getOrders(token).then(setOrders).finally(() => setLoading(false))
  }, [token])

  if (loading) return <div className="p-8">Loading...</div>

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Your Orders</h1>
      {orders.length === 0 ? (
        <p className="text-gray-500">No orders yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
  )
}

