'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';

interface BusinessCalculatorProps {
  isOpen: boolean;
  onClose: () => void;
  initialMrp?: number;
}

export default function BusinessCalculator({
  isOpen,
  onClose,
  initialMrp = 100,
}: BusinessCalculatorProps) {
  const { theme } = useTheme();
  const [mrp, setMrp] = useState<number>(initialMrp);
  const [quantity, setQuantity] = useState<number>(100);

  useEffect(() => {
    if (isOpen) {
      setMrp(initialMrp);
    }
  }, [isOpen, initialMrp]);

  // Amount off products
  const [amountOffType, setAmountOffType] = useState<'fixed' | 'percentage'>('fixed');
  const [amountOffValue, setAmountOffValue] = useState<number>(0);
  const [amountOffMinQty, setAmountOffMinQty] = useState<number>(1);

  // Buy X Get Y
  const [buyX, setBuyX] = useState<number>(0);
  const [getY, setGetY] = useState<number>(0);
  const [getsDiscountType, setGetsDiscountType] = useState<'free' | 'percentage' | 'amount_off'>(
    'free'
  );
  const [getsDiscountValue, setGetsDiscountValue] = useState<number>(0);

  // Results
  const [results, setResults] = useState({
    totalCost: 0,
    totalUnits: 0,
    effectivePrice: 0,
    totalSavings: 0,
    savingsPercentage: 0,
  });

  useEffect(() => {
    calculateResults();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    mrp,
    quantity,
    amountOffType,
    amountOffValue,
    amountOffMinQty,
    buyX,
    getY,
    getsDiscountType,
    getsDiscountValue,
  ]);

  const calculateResults = () => {
    // baseDiscountedPrice is removed, we start from MRP
    let totalCost = quantity * mrp;

    // Apply Amount Off Products
    if (quantity >= amountOffMinQty) {
      if (amountOffType === 'fixed') {
        totalCost = Math.max(0, totalCost - amountOffValue);
      } else {
        totalCost = totalCost * (1 - amountOffValue / 100);
      }
    }

    // Handle Buy X Get Y
    let bonusUnits = 0;
    let bonusCost = 0;

    if (buyX > 0 && getY > 0) {
      const sets = Math.floor(quantity / buyX);
      bonusUnits = sets * getY;

      if (getsDiscountType === 'percentage') {
        bonusCost = bonusUnits * mrp * (1 - getsDiscountValue / 100);
      } else if (getsDiscountType === 'amount_off') {
        bonusCost = bonusUnits * Math.max(0, mrp - getsDiscountValue);
      } else {
        // Free
        bonusCost = 0;
      }
    }

    const finalTotalCost = totalCost + bonusCost;
    const finalTotalUnits = quantity + bonusUnits;
    const effectivePrice = finalTotalUnits > 0 ? finalTotalCost / finalTotalUnits : 0;
    const totalSavings = finalTotalUnits * mrp - finalTotalCost;
    const savingsPercentage =
      finalTotalUnits * mrp > 0 ? (totalSavings / (finalTotalUnits * mrp)) * 100 : 0;

    setResults({
      totalCost: finalTotalCost,
      totalUnits: finalTotalUnits,
      effectivePrice: effectivePrice,
      totalSavings: totalSavings,
      savingsPercentage: savingsPercentage,
    });
  };

  if (!isOpen) return null;

  return (
    <div className="animate-in fade-in fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm duration-300">
      <div
        className="animate-in zoom-in-95 flex w-full max-w-4xl flex-col overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-2xl duration-300 md:flex-row"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Left Side: Inputs */}
        <div className="max-h-[80vh] flex-1 overflow-y-auto p-8 md:max-h-none">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-800">Business Pricing Calculator</h2>
            <button
              onClick={onClose}
              className="rounded-full p-2 transition-colors hover:bg-gray-100"
            >
              <svg
                className="h-6 w-6 text-gray-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div className="space-y-6">
            {/* Order Details */}
            <section className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
              <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-gray-500">
                Order Details
              </h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-gray-600">
                    MRP per Unit/Case
                  </label>
                  <input
                    type="number"
                    value={mrp}
                    onChange={(e) => setMrp(Number(e.target.value))}
                    className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 font-semibold transition-all focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-gray-600">
                    Quantity to Purchase
                  </label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 font-semibold transition-all focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            </section>

            {/* Amount Off Products Promotion */}
            <section className="rounded-2xl border border-blue-100 bg-blue-50/30 p-5">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-blue-600">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Amount Off Products
              </h3>
              <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-gray-600">
                    Discount Type
                  </label>
                  <select
                    value={amountOffType}
                    onChange={(e) => setAmountOffType(e.target.value as 'fixed' | 'percentage')}
                    className="w-full rounded-xl border-2 border-gray-200 bg-white px-4 py-2 font-semibold transition-all focus:border-blue-500 focus:outline-none"
                  >
                    <option value="fixed">Fixed Amount (₹)</option>
                    <option value="percentage">Percentage (%)</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-gray-600">
                    Discount Value
                  </label>
                  <input
                    type="number"
                    value={amountOffValue}
                    onChange={(e) => setAmountOffValue(Number(e.target.value))}
                    className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 font-semibold transition-all focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-gray-600">
                  Minimum Quantity Required
                </label>
                <input
                  type="number"
                  value={amountOffMinQty}
                  onChange={(e) => setAmountOffMinQty(Number(e.target.value))}
                  className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 font-semibold transition-all focus:border-blue-500 focus:outline-none"
                />
              </div>
            </section>

            {/* Buy X Get Y Promotion */}
            <section className="rounded-2xl border border-emerald-100 bg-emerald-50/30 p-5">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-emerald-600">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  />
                </svg>
                Buy X Get Y
              </h3>
              <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-gray-600">
                    Buy Quantity (X)
                  </label>
                  <input
                    type="number"
                    value={buyX}
                    onChange={(e) => setBuyX(Number(e.target.value))}
                    className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 font-semibold transition-all focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-gray-600">
                    Get Quantity (Y)
                  </label>
                  <input
                    type="number"
                    value={getY}
                    onChange={(e) => setGetY(Number(e.target.value))}
                    className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 font-semibold transition-all focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-gray-600">
                    Bonus Item Price
                  </label>
                  <select
                    value={getsDiscountType}
                    onChange={(e) =>
                      setGetsDiscountType(e.target.value as 'free' | 'percentage' | 'amount_off')
                    }
                    className="w-full rounded-xl border-2 border-gray-200 bg-white px-4 py-2 font-semibold transition-all focus:border-blue-500 focus:outline-none"
                  >
                    <option value="free">Free</option>
                    <option value="percentage">Discounted (%)</option>
                    <option value="amount_off">Discounted (₹ OffEach)</option>
                  </select>
                </div>
                {getsDiscountType !== 'free' && (
                  <div>
                    <label className="mb-1 block text-xs font-semibold text-gray-600">
                      Discount Value
                    </label>
                    <input
                      type="number"
                      value={getsDiscountValue}
                      onChange={(e) => setGetsDiscountValue(Number(e.target.value))}
                      className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 font-semibold transition-all focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>

        {/* Right Side: Results */}
        <div
          className="flex w-full flex-col justify-center p-8 text-white md:w-[350px]"
          style={{
            background: theme.gradient || 'linear-gradient(135deg, #1a4d33 0%, #0d2a1c 100%)',
          }}
        >
          <h3 className="mb-8 text-xl font-bold opacity-90">Analysis Summary</h3>

          <div className="space-y-8">
            <div>
              <p className="mb-1 text-xs font-bold uppercase tracking-widest opacity-60">
                Effective Price per Unit
              </p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-black">₹{results.effectivePrice.toFixed(2)}</span>
                <span className="text-sm line-through opacity-60">₹{mrp.toFixed(2)}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="mb-1 text-[10px] font-bold uppercase tracking-widest opacity-60">
                  Total Units
                </p>
                <p className="text-xl font-bold">{results.totalUnits}</p>
              </div>
              <div>
                <p className="mb-1 text-[10px] font-bold uppercase tracking-widest opacity-60">
                  Total Cost
                </p>
                <p className="text-xl font-bold">₹{results.totalCost.toLocaleString()}</p>
              </div>
            </div>

            <div className="border-t border-white/10 pt-6">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs font-bold uppercase tracking-widest opacity-60">
                  Total Savings
                </p>
                <span className="rounded-full bg-emerald-500 px-2 py-0.5 text-[10px] font-black text-white">
                  {results.savingsPercentage.toFixed(1)}% OFF
                </span>
              </div>
              <p className="text-3xl font-black text-emerald-400">
                ₹{results.totalSavings.toLocaleString()}
              </p>
              <p className="mt-1 text-[10px] opacity-50">Based on standard MRP valuation</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="group mt-12 flex w-full items-center justify-center gap-2 rounded-2xl bg-white py-4 font-black text-gray-900 shadow-xl transition-all hover:bg-gray-100"
          >
            Apply Selection
            <svg
              className="h-5 w-5 transition-transform group-hover:translate-x-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={3}
                d="M17 8l4 4m0 0l-4 4m4-4H3"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
