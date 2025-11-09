'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Header } from '@/components/Header'
import { Navigation } from '@/components/Navigation'

// Mock KPI data structure - will be replaced with real API data
interface KPIData {
  totalOrders: number;
  totalSpent: number;
  averageOrderValue: number;
  favoriteStore: string;
  mostOrderedItem: string;
  savingsFromComparison: number;
}

export default function ProfilePage() {
  const { token } = useAuth()
  const [loading, setLoading] = useState(true)
  const [kpis, setKpis] = useState<KPIData>({
    totalOrders: 0,
    totalSpent: 0,
    averageOrderValue: 0,
    favoriteStore: 'N/A',
    mostOrderedItem: 'N/A',
    savingsFromComparison: 0
  })

  useEffect(() => {
    if (!token) return

    // TODO: Replace with actual API call to get user statistics
    // For now, using mock data
    setTimeout(() => {
      setKpis({
        totalOrders: 24,
        totalSpent: 487.65,
        averageOrderValue: 20.32,
        favoriteStore: 'Uber Eats',
        mostOrderedItem: 'Organic Eggs',
        savingsFromComparison: 73.20
      })
      setLoading(false)
    }, 500)
  }, [token])

  return (
    <div className="min-h-screen py-12 px-4" style={{ background: '#F5F5F5' }}>
      <div className="max-w-6xl mx-auto">
        <Header />
        <Navigation />
        
        <div className="card">
          <h1 className="text-3xl font-bold mb-2" style={{ color: '#3E2723' }}>
            Your Profile & Statistics
          </h1>
          <p className="text-gray-600 mb-8">
            Track your ordering patterns and savings
          </p>
          
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 mx-auto mb-4" style={{ borderColor: '#C9915C' }}></div>
              <p className="text-gray-600">Loading statistics...</p>
            </div>
          ) : (
            <>
              {/* Bento Box Grid - 4 KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {/* KPI 1: Total Orders */}
                <div className="bg-gradient-to-br from-[#C9915C] to-[#B5824E] rounded-xl p-6 text-white">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-5xl">📦</span>
                    <div className="text-right">
                      <div className="text-4xl font-bold">{kpis.totalOrders}</div>
                      <div className="text-sm opacity-90">orders</div>
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold">Total Orders</h3>
                  <p className="text-sm opacity-90 mt-1">Lifetime order count</p>
                </div>

                {/* KPI 2: Total Spent */}
                <div className="bg-gradient-to-br from-[#06C167] to-[#05A857] rounded-xl p-6 text-white">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-5xl">💰</span>
                    <div className="text-right">
                      <div className="text-4xl font-bold">${kpis.totalSpent.toFixed(2)}</div>
                      <div className="text-sm opacity-90">spent</div>
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold">Total Spent</h3>
                  <p className="text-sm opacity-90 mt-1">All-time spending</p>
                </div>

                {/* KPI 3: Average Order Value */}
                <div className="bg-gradient-to-br from-[#FF6B35] to-[#E55A2B] rounded-xl p-6 text-white">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-5xl">📊</span>
                    <div className="text-right">
                      <div className="text-4xl font-bold">${kpis.averageOrderValue.toFixed(2)}</div>
                      <div className="text-sm opacity-90">average</div>
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold">Average Order</h3>
                  <p className="text-sm opacity-90 mt-1">Per order spending</p>
                </div>

                {/* KPI 4: Total Savings */}
                <div className="bg-gradient-to-br from-[#4CAF50] to-[#43A047] rounded-xl p-6 text-white">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-5xl">💵</span>
                    <div className="text-right">
                      <div className="text-4xl font-bold">${kpis.savingsFromComparison.toFixed(2)}</div>
                      <div className="text-sm opacity-90">saved</div>
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold">Total Savings</h3>
                  <p className="text-sm opacity-90 mt-1">From price comparison</p>
                </div>
              </div>

              {/* Additional Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-3xl">⭐</span>
                    <h3 className="text-xl font-semibold" style={{ color: '#3E2723' }}>
                      Favorite Store
                    </h3>
                  </div>
                  <p className="text-3xl font-bold" style={{ color: '#C9915C' }}>
                    {kpis.favoriteStore}
                  </p>
                  <p className="text-sm text-gray-600 mt-2">Most frequently ordered from</p>
                </div>

                <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-3xl">🥇</span>
                    <h3 className="text-xl font-semibold" style={{ color: '#3E2723' }}>
                      Top Item
                    </h3>
                  </div>
                  <p className="text-3xl font-bold" style={{ color: '#C9915C' }}>
                    {kpis.mostOrderedItem}
                  </p>
                  <p className="text-sm text-gray-600 mt-2">Most ordered ingredient</p>
                </div>
              </div>
            </>
          )}
        </div>
        
        <footer className="text-center mt-12 text-gray-500 text-sm">
          © 2025 MealPilot
        </footer>
      </div>
    </div>
  )
}

