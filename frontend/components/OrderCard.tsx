import Link from 'next/link'
import Image from 'next/image'

type Props = {
  id: string
  storeName: string
  total: number
  currency: string
  thumbnailUrl: string | null
  createdAt: string
}

export function OrderCard({ id, storeName, total, currency, thumbnailUrl, createdAt }: Props) {
  const date = new Date(createdAt).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  })
  
  const platformIcon = storeName.toLowerCase().includes('instacart') ? '🛒' : 
                       storeName.toLowerCase().includes('uber') ? '🚗' : '📦';
  const platformColor = storeName.toLowerCase().includes('instacart') ? '#FF6B35' : 
                        storeName.toLowerCase().includes('uber') ? '#06C167' : '#C9915C';

  return (
    <Link href={`/orders/${id}`}>
      <div className="flex items-center gap-4 p-5 bg-white rounded-lg border-2 border-gray-200 hover:border-[#C9915C] transition-all cursor-pointer hover:shadow-md">
        {thumbnailUrl ? (
          <Image src={thumbnailUrl} alt="Receipt" width={80} height={100} className="rounded-lg object-cover" />
        ) : (
          <div className="w-20 h-24 bg-gray-100 rounded-lg flex items-center justify-center text-4xl">
            {platformIcon}
          </div>
        )}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{platformIcon}</span>
            <h3 className="font-bold text-lg" style={{ color: '#3E2723' }}>{storeName}</h3>
          </div>
          <p className="text-gray-600 text-sm mb-2">{date}</p>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold" style={{ color: platformColor }}>
              {currency}{total.toFixed(2)}
            </span>
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded">
              COMPLETED
            </span>
          </div>
        </div>
        <div className="text-gray-400">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </Link>
  )
}

