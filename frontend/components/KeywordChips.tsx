type Props = {
  keywords: string[]
}

export function KeywordChips({ keywords }: Props) {
  if (!keywords.length) return null

  return (
    <div className="flex flex-wrap gap-2 my-4">
      {keywords.map((keyword, idx) => (
        <span
          key={idx}
          className="px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
        >
          {keyword}
        </span>
      ))}
    </div>
  )
}

