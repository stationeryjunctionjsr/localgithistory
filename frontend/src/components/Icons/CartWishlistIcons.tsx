'use client';

import React from 'react';

interface MyCartIconProps {
  cartCount: number;
}

export const MyCartIcon: React.FC<MyCartIconProps> = ({ cartCount }) => {
  return (
    <div className="relative">
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-gray-600 transition-colors hover:text-gray-900"
      >
        <path
          d="M9 22C9.55228 22 10 21.5523 10 21C10 20.4477 9.55228 20 9 20C8.44772 20 8 20.4477 8 21C8 21.5523 8.44772 22 9 22Z"
          fill="currentColor"
        />
        <path
          d="M20 22C20.5523 22 21 21.5523 21 21C21 20.4477 20.5523 20 20 20C19.4477 20 19 20.4477 19 21C19 21.5523 19.4477 22 20 22Z"
          fill="currentColor"
        />
        <path
          d="M1 1H5L7.68 14.39C7.77 14.85 8.17 15.18 8.64 15.18H19.32C19.79 15.18 20.19 14.85 20.28 14.39L22 6H6"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {cartCount > 0 && (
        <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
          {cartCount > 99 ? '99+' : cartCount}
        </span>
      )}
    </div>
  );
};

interface WishlistIconProps {
  count: number;
}

export const WishlistIcon: React.FC<WishlistIconProps> = ({ count }) => {
  return (
    <div className="relative">
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-gray-600 transition-colors hover:text-red-500"
      >
        <path
          d="M20.84 4.61C20.3292 4.099 19.7229 3.69365 19.0554 3.41708C18.3879 3.14052 17.673 2.99817 16.95 2.99817C16.227 2.99817 15.5121 3.14052 14.8446 3.41708C14.1771 3.69365 13.5708 4.099 13.06 4.61L12 5.67L10.94 4.61C9.9083 3.57831 8.50903 2.99871 7.05 2.99871C5.59096 2.99871 4.19169 3.57831 3.16 4.61C2.12831 5.64169 1.54871 7.04097 1.54871 8.5C1.54871 9.95903 2.12831 11.3583 3.16 12.39L4.22 13.45L12 21.23L19.78 13.45L20.84 12.39C21.351 11.8792 21.7564 11.2729 22.0329 10.6054C22.3095 9.93789 22.4518 9.22295 22.4518 8.5C22.4518 7.77704 22.3095 7.06211 22.0329 6.3946C21.7564 5.7271 21.351 5.12079 20.84 4.61Z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </svg>
      {count > 0 && (
        <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
          {count > 99 ? '99+' : count}
        </span>
      )}
    </div>
  );
};
