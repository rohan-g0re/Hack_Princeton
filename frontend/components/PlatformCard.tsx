'use client';

import { PlatformSummary } from '@/lib/types';

interface Props {
  platform: PlatformSummary;
}

export function PlatformCard({ platform }: Props) {
  const logoColors: Record<string, string> = {
    instacart: 'bg-green-50',
    ubereats: 'bg-green-100',
    doordash: 'bg-red-50',
  };
  
  const bgColor = logoColors[platform.logo] || 'bg-gray-50';
  
  return (
    <div className={`${bgColor} border border-gray-200 rounded-lg p-6 shadow-md`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold capitalize">{platform.name}</h3>
        {platform.best_deal && (
          <span className="px-2 py-1 text-xs font-semibold text-green-700 bg-green-100 rounded">
            Best Deal Option
          </span>
        )}
      </div>
      
      {/* Summary */}
      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Your last {platform.name} order was placed on {platform.date} for ${platform.total.toFixed(2)}.
        </p>
      </div>
      
      {/* Items */}
      <div className="mb-4">
        <p className="font-semibold mb-2">You ordered:</p>
        <ul className="list-disc list-inside space-y-1">
          {platform.items.map((item, idx) => (
            <li key={idx} className="text-sm">
              {item.name} ({item.quantity} {item.quantity > 1 ? 'units' : 'unit'})
            </li>
          ))}
        </ul>
      </div>
      
      {/* Total */}
      <div className="border-t pt-3 mt-3">
        <p className="text-lg font-bold">
          Total: ${platform.total.toFixed(2)}
        </p>
      </div>
    </div>
  );
}

