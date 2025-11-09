'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { getOrderDetail, OrderDetailResponse } from '@/lib/api'
import { ReceiptImage } from '@/components/ReceiptImage'
import { OrdersTable } from '@/components/OrdersTable'

export default function OrderDetailPage() {
  const { orderId } = useParams()
  const { token } = useAuth()
  const [orderData, setOrderData] = useState<OrderDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token || !orderId) return

    getOrderDetail(orderId as string, token)
      .then(setOrderData)
      .finally(() => setLoading(false))
  }, [token, orderId])

  if (loading) return <div className="p-8">Loading...</div>
  if (!orderData) return <div className="p-8">Order not found</div>

  const { order, items } = orderData

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Order Details</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Receipt Image */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Receipt</h2>
          <ReceiptImage src={order.receipt_image_url} />
        </div>

        {/* Order Info */}
        <div>
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h3 className="font-semibold text-lg mb-2">{order.store_name}</h3>
            <p className="text-gray-600 text-sm">{new Date(order.created_at).toLocaleString()}</p>
          </div>

          <h2 className="text-xl font-semibold mb-4">Items</h2>
          <OrdersTable
            items={items}
            subtotal={order.subtotal}
            tax={order.tax}
            total={order.total}
            currency={order.currency}
          />
        </div>
      </div>
    </div>
  )
}

