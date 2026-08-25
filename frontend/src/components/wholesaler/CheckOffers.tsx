'use client';

import React, { useState, useEffect } from 'react';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface CheckOffersProps {
  isOpen: boolean;
  onClose: () => void;
  product: any;
}

export default function CheckOffers({ isOpen, onClose, product }: CheckOffersProps) {
  const [offers, setOffers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && product?._id) {
      fetchOffers();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, product]);

  const fetchOffers = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/schemes/applicable/${product._id}`);
      setOffers(response.data || []);
    } catch (err) {
      logger.error('Failed to fetch applicable offers', err);
      setOffers([]);
    } finally {
      setLoading(false);
    }
  };

  const calculateEffectivePrice = (offer: any): number => {
    const mrp = product.mrp || 0;
    if (offer.typeOfDiscount === 'product_discount') {
      if (offer.discountType === 'percentage') {
        return mrp * (1 - offer.discountValue / 100);
      } else {
        return Math.max(0, mrp - offer.discountValue);
      }
    } else if (offer.typeOfDiscount === 'buy_x_get_y') {
      const buyQty = offer.minQuantityOfEligibleItems || 1;
      const getQty = offer.buyXGetYCustomerGetsQuantity || 1;

      const buyCost = mrp * buyQty;
      let getCost = 0;

      const getsDiscountType = offer.buyXGetYCustomerGetsDiscountType || 'free';
      const getsDiscountValue = offer.buyXGetYCustomerGetsDiscountValue || 0;

      if (getsDiscountType === 'percentage') {
        getCost = mrp * (1 - getsDiscountValue / 100) * getQty;
      } else if (getsDiscountType === 'amount_off') {
        getCost = Math.max(0, mrp - getsDiscountValue) * getQty;
      } else {
        getCost = 0; // free
      }

      const totalCost = buyCost + getCost;
      const totalUnits = buyQty + getQty;

      return totalCost / totalUnits;
    }
    return mrp;
  };

  const formatOfferName = (offer: any) => {
    if (offer.typeOfDiscount === 'buy_x_get_y') {
      const getQty = offer.buyXGetYCustomerGetsQuantity || 1;
      const buyQty =
        offer.minRequirementType === 'min_quantity'
          ? `Buy ${offer.minQuantityOfEligibleItems || ''}`
          : 'Buy';

      let getDesc = 'Free';
      if (offer.buyXGetYCustomerGetsDiscountType === 'percentage') {
        getDesc = `${offer.buyXGetYCustomerGetsDiscountValue}% off`;
      } else if (offer.buyXGetYCustomerGetsDiscountType === 'amount_off') {
        getDesc = `₹${offer.buyXGetYCustomerGetsDiscountValue} off`;
      }
      return `${buyQty} Get ${getQty} ${getDesc}`;
    } else {
      if (offer.discountType === 'percentage') {
        return `${offer.discountValue}% Off on Product`;
      } else {
        return `₹${offer.discountValue} Off on Product`;
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="animate-in fade-in fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm duration-300">
      <div
        className="animate-in zoom-in-95 flex w-full max-w-xl flex-col overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-2xl duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/50 p-6">
          <div>
            <h2 className="text-xl font-black text-gray-900">Check Offers</h2>
            <p className="mt-1 text-xs font-semibold text-gray-500">
              Available schemes for {product.name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full bg-white p-2 shadow-sm transition-colors hover:bg-gray-100"
          >
            <svg
              className="h-5 w-5 text-gray-500"
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

        <div className="max-h-[60vh] overflow-y-auto p-6">
          <div className="mb-6 flex items-center justify-between rounded-xl border border-gray-200 bg-gray-50 p-4">
            <span className="text-sm font-bold uppercase tracking-wider text-gray-600">
              Unit MRP
            </span>
            <span className="text-xl font-black text-gray-900">
              ₹{(product.mrp || 0).toFixed(2)}
            </span>
          </div>

          <h3 className="mb-4 text-[11px] font-bold uppercase tracking-widest text-gray-400">
            Applicable Offers
          </h3>

          {loading ? (
            <div className="flex items-center justify-center py-10">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-emerald-600"></div>
            </div>
          ) : offers.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-gray-300 bg-gray-50 py-10 text-center">
              <p className="font-medium text-gray-500">
                No special offers available for this product.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {offers.map((offer) => {
                const effectivePrice = calculateEffectivePrice(offer);
                const savings = (product.mrp || 0) - effectivePrice;
                const savingsPercent = ((savings / (product.mrp || 1)) * 100).toFixed(1);

                return (
                  <div
                    key={offer._id}
                    className="group relative overflow-hidden rounded-2xl border border-gray-200 bg-white p-5 transition-all hover:border-emerald-300 hover:shadow-md"
                  >
                    <div className="absolute right-0 top-0 -z-10 h-24 w-24 rounded-bl-full bg-gradient-to-bl from-emerald-50 to-transparent opacity-50"></div>

                    <div className="mb-3 flex items-start justify-between">
                      <div>
                        {offer.method === 'discount_code' && (
                          <span className="mb-2 inline-block rounded bg-gray-100 px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-gray-600">
                            Code: {offer.code}
                          </span>
                        )}
                        <h4 className="text-lg font-bold leading-tight text-gray-900">
                          {formatOfferName(offer)}
                        </h4>
                      </div>

                      <div className="flex-shrink-0 text-right">
                        <span className="mb-1 block text-[10px] font-bold uppercase tracking-widest text-gray-400">
                          Effective Unit Price
                        </span>
                        <div className="flex items-baseline justify-end gap-1">
                          <span className="text-xl font-black text-emerald-600">
                            ₹{effectivePrice.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between rounded-lg bg-emerald-50 p-2.5">
                      <div className="flex items-center gap-2">
                        <svg
                          className="h-4 w-4 text-emerald-500"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        <span className="text-sm font-semibold text-emerald-800">
                          You save ₹{savings.toFixed(2)} per unit
                        </span>
                      </div>
                      <span className="rounded-full bg-emerald-200 px-2 py-0.5 text-xs font-black text-emerald-800">
                        {savingsPercent}% OFF
                      </span>
                    </div>

                    {offer.minRequirementType && offer.minRequirementType !== 'none' && (
                      <p className="mt-3 flex items-center gap-1 text-xs font-medium text-gray-500">
                        <svg
                          className="h-3 w-3 text-amber-500"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        {offer.minRequirementType === 'min_quantity'
                          ? `Requires minimum ${offer.minQuantityOfEligibleItems} units`
                          : `Requires minimum order of ₹${offer.minPurchaseAmount}`}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
