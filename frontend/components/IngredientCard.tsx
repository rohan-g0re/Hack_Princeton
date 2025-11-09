'use client';

import { Ingredient } from '@/lib/types';
import { useState } from 'react';

interface Props {
  ingredient: Ingredient;
  onChange: (updated: Ingredient) => void;
  onDelete: () => void;
}

export function IngredientCard({ ingredient, onChange, onDelete }: Props) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editName, setEditName] = useState(ingredient.name);
  
  const handleNameSave = () => {
    if (editName.trim()) {
      onChange({ ...ingredient, name: editName.trim() });
    }
    setIsEditingName(false);
  };
  
  const handleQtyChange = (delta: number) => {
    const newQty = Math.max(0, Math.min(999, ingredient.quantity + delta));
    onChange({ ...ingredient, quantity: newQty });
  };
  
  return (
    <div className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Name */}
      <div className="flex-1 min-w-0">
        {isEditingName ? (
          <input
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onBlur={handleNameSave}
            onKeyDown={(e) => e.key === 'Enter' && handleNameSave()}
            className="w-full px-2 py-1 border rounded"
            autoFocus
          />
        ) : (
          <button
            onClick={() => setIsEditingName(true)}
            className="text-left font-medium text-gray-900 hover:text-primary"
          >
            {ingredient.name}
          </button>
        )}
      </div>
      
      {/* Quantity controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => handleQtyChange(-1)}
          className="w-8 h-8 flex items-center justify-center border rounded-full hover:bg-gray-100"
          aria-label="Decrease quantity"
        >
          −
        </button>
        <span className="w-12 text-center font-semibold">
          {ingredient.quantity}
        </span>
        <button
          onClick={() => handleQtyChange(1)}
          className="w-8 h-8 flex items-center justify-center border rounded-full hover:bg-gray-100"
          aria-label="Increase quantity"
        >
          +
        </button>
        {ingredient.unit && (
          <span className="text-sm text-gray-600 ml-1">{ingredient.unit}</span>
        )}
      </div>
      
      {/* Delete */}
      <button
        onClick={onDelete}
        className="text-red-500 hover:text-red-700 font-bold text-xl"
        aria-label="Delete ingredient"
      >
        ×
      </button>
    </div>
  );
}

