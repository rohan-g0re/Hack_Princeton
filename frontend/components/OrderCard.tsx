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
  const date = new Date(createdAt).toLocaleDateString()

  return (
    <Link href={`/orders/${id}`}>
      <div className="flex items-center gap-4 p-4 border rounded-lg hover:shadow-md transition cursor-pointer">
        {thumbnailUrl ? (
          <Image src={thumbnailUrl} alt="Receipt" width={80} height={140} className="rounded" />
        ) : (
          <div className="w-20 h-36 bg-gray-200 rounded flex items-center justify-center text-xs text-gray-500">
            No receipt
          </div>
        )}
        <div className="flex-1">
          <h3 className="font-semibold text-lg">{storeName}</h3>
          <p className="text-gray-600 text-sm">{date}</p>
          <p className="text-xl font-bold mt-1">{currency} {total.toFixed(2)}</p>
        </div>
      </div>
    </Link>
  )
}

