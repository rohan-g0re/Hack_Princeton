type Item = {
  platform: string
  item_name: string
  quantity: number
  unit: string | null
  unit_price: number
  total: number
}

type Props = {
  items: Item[]
  subtotal: number
  tax: number
  total: number
  currency: string
}

export function OrdersTable({ items, subtotal, tax, total, currency }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse border border-gray-300">
        <thead className="bg-gray-100">
          <tr>
            <th className="border border-gray-300 px-4 py-2 text-left">Platform</th>
            <th className="border border-gray-300 px-4 py-2 text-left">Item</th>
            <th className="border border-gray-300 px-4 py-2 text-right">Qty</th>
            <th className="border border-gray-300 px-4 py-2 text-right">Unit Price</th>
            <th className="border border-gray-300 px-4 py-2 text-right">Total</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              <td className="border border-gray-300 px-4 py-2">{item.platform}</td>
              <td className="border border-gray-300 px-4 py-2">{item.item_name}</td>
              <td className="border border-gray-300 px-4 py-2 text-right">{item.quantity}</td>
              <td className="border border-gray-300 px-4 py-2 text-right">{currency} {item.unit_price.toFixed(2)}</td>
              <td className="border border-gray-300 px-4 py-2 text-right font-semibold">{currency} {item.total.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot className="bg-gray-50 font-bold">
          <tr>
            <td colSpan={4} className="border border-gray-300 px-4 py-2 text-right">Subtotal:</td>
            <td className="border border-gray-300 px-4 py-2 text-right">{currency} {subtotal.toFixed(2)}</td>
          </tr>
          <tr>
            <td colSpan={4} className="border border-gray-300 px-4 py-2 text-right">Tax:</td>
            <td className="border border-gray-300 px-4 py-2 text-right">{currency} {tax.toFixed(2)}</td>
          </tr>
          <tr>
            <td colSpan={4} className="border border-gray-300 px-4 py-2 text-right">Total:</td>
            <td className="border border-gray-300 px-4 py-2 text-right text-lg">{currency} {total.toFixed(2)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}

