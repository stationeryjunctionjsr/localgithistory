'use client';

import React, { useState } from 'react';
import { toast } from 'react-toastify';

// eslint-disable-next-line unused-imports/no-unused-vars
interface Variant {
  id: string;
  type: string;
  value: string;
  mrp: number;
  price: number;
  stock: number;
  images?: string[];
}

interface QuickVariantModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: {
    id: string;
    name: string;
    price: number;
    variants?: any[];
  };
  onAddToCart: (variant: any, quantity: number) => void;
}

export default function QuickVariantModal({
  isOpen,
  onClose,
  product,
  onAddToCart,
}: QuickVariantModalProps) {
  const [selectedVariant, setSelectedVariant] = useState<any>(null);
  const [quantity, setQuantity] = useState(1);

  if (!isOpen) return null;

  const handleAdd = () => {
    if (!selectedVariant && product.variants && product.variants.length > 0) {
      toast.warn('Please select a variant');
      return;
    }
    onAddToCart(selectedVariant, quantity);
    onClose();
  };

  // Group variants by type if needed, but for simplicity we list them
  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="animate-in fade-in zoom-in w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-xl duration-200">
        <div className="flex items-center justify-between border-b border-slate-100 p-6">
          <h2 className="text-xl font-bold text-slate-800">Select Options</h2>
          <button onClick={onClose} className="text-2xl text-slate-400 hover:text-slate-600">
            ×
          </button>
        </div>

        <div className="space-y-6 p-6">
          <div>
            <div className="mb-1 text-sm font-semibold uppercase tracking-wider text-slate-500">
              {product.name}
            </div>
            <div className="text-2xl font-bold text-slate-900">
              ₹{selectedVariant?.price || product.price}
            </div>
          </div>

          <div className="space-y-3">
            <label className="block text-sm font-semibold text-slate-700">Available Options</label>
            <div className="flex flex-wrap gap-2">
              {product.variants?.map((v: any) => (
                <button
                  key={v.id}
                  onClick={() => setSelectedVariant(v)}
                  className={`rounded-lg border px-4 py-2 text-sm font-medium transition-all ${
                    selectedVariant?.id === v.id
                      ? 'border-indigo-600 bg-indigo-600 text-white shadow-md ring-2 ring-indigo-200'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-indigo-300'
                  }`}
                >
                  {v.value} ({v.type})
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-slate-100 pt-4">
            <div className="flex items-center overflow-hidden rounded-lg border border-slate-200">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="bg-slate-50 px-3 py-1 text-slate-600 hover:bg-slate-100"
              >
                -
              </button>
              <span className="w-10 px-4 py-1 text-center font-semibold text-slate-800">
                {quantity}
              </span>
              <button
                onClick={() => setQuantity(quantity + 1)}
                className="bg-slate-50 px-3 py-1 text-slate-600 hover:bg-slate-100"
              >
                +
              </button>
            </div>

            <button
              onClick={handleAdd}
              disabled={!selectedVariant && product.variants && product.variants.length > 0}
              className="rounded-lg bg-indigo-600 px-8 py-2 font-bold text-white shadow-lg transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Add to Cart
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
