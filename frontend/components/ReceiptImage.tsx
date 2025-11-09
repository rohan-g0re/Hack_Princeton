import Image from 'next/image'

type Props = {
  src: string | null
}

export function ReceiptImage({ src }: Props) {
  if (!src) {
    return (
      <div className="w-full max-w-md mx-auto h-96 bg-gray-100 rounded flex items-center justify-center">
        <p className="text-gray-500">Receipt not available</p>
      </div>
    )
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <Image
        src={src}
        alt="Receipt"
        width={1024}
        height={1792}
        className="rounded shadow-lg"
        style={{ objectFit: 'contain' }}
      />
    </div>
  )
}

