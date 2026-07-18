'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/utils/api';
import { useAuth } from '@/context/AuthContext';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { toast } from 'react-toastify';

export default function ProductDetail() {
  const { id } = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const [product, setProduct] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    if (id) {
      fetchProduct();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchProduct = async () => {
    try {
      const response = await api.get(`/products/${id}`);
      setProduct(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Product not found', error);
      router.push('/valet');
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!user) {
      toast.info('Please log in to add items to cart');
      return;
    }

    try {
      await api.post('/cart', { productId: id, quantity });
      toast.success('Product added to cart');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to add to cart');
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading...</div>;
  }

  if (!product) {
    return <div className="container mx-auto px-4 py-8">Product not found</div>;
  }

  return (
    <div className="container mx-auto max-w-6xl px-8 py-8">
      <button
        onClick={() => router.back()}
        className="mb-4 cursor-pointer rounded border border-gray-300 bg-white px-4 py-2 text-black transition-all hover:bg-gradient-to-r hover:from-red-700 hover:to-red-600 hover:text-white"
      >
        ← Back
      </button>

      <div className="grid grid-cols-1 gap-8 rounded-lg bg-white p-8 shadow-md md:grid-cols-2">
        <div className="flex flex-col gap-4">
          {product.images && product.images.length > 0 ? (
            <>
              <div className="flex h-[500px] w-full items-center justify-center overflow-hidden rounded-lg bg-gray-50">
                <img
                  src={getImageUrlWithFallback(product.images[selectedImage])}
                  alt={product.name}
                  className="h-full w-full object-contain"
                />
              </div>
              {product.images.length > 1 && (
                <div className="flex gap-2 overflow-x-auto">
                  {product.images.map((img: string, idx: number) => (
                    <img
                      key={idx}
                      src={img}
                      alt={`${product.name} ${idx + 1}`}
                      className={`h-20 w-20 cursor-pointer rounded border-2 object-cover transition-all ${selectedImage === idx ? 'border-red-600 opacity-100' : 'border-transparent opacity-70 hover:opacity-100'}`}
                      onClick={() => setSelectedImage(idx)}
                    />
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="flex h-[500px] w-full items-center justify-center rounded-lg bg-gray-50 text-xl text-gray-400">
              No Image Available
            </div>
          )}
        </div>

        <div>
          <h1 className="mb-4 text-3xl text-gray-800">{product.name}</h1>
          <p className="mb-2 text-gray-600">SKU: {product.sku || 'N/A'}</p>
          <p className="mb-4 text-gray-600">Category: {product.category || 'N/A'}</p>

          <div className="mb-6 rounded-lg bg-gray-50 p-4">
            {product.mrp && product.price < product.mrp && (
              <p className="mb-2 text-lg text-gray-400 line-through">
                MRP: ₹{product.mrp.toFixed(2)}
              </p>
            )}
            <p className="mb-2 text-2xl font-bold text-red-600">
              Price: ₹{product.price?.toFixed(2) || product.mrp?.toFixed(2) || '0.00'}
            </p>
            {product.mrp && product.price < product.mrp && (
              <p className="font-semibold text-green-600">
                Save {Math.round(((product.mrp - product.price) / product.mrp) * 100)}%
              </p>
            )}
          </div>

          {product.description && (
            <div className="mb-6">
              <h3 className="mb-2 font-semibold text-gray-800">Description</h3>
              <p className="leading-relaxed text-gray-600">{product.description}</p>
            </div>
          )}

          <div className="mb-6">
            <p className="font-semibold text-gray-800">
              Stock: {product.stock > 0 ? `${product.stock} available` : 'Out of Stock'}
            </p>
          </div>

          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-4">
              <label className="font-semibold">Quantity:</label>
              <input
                type="number"
                min="1"
                max={product.stock}
                value={quantity}
                onChange={(e) =>
                  setQuantity(Math.max(1, Math.min(product.stock, parseInt(e.target.value) || 1)))
                }
                className="w-20 rounded border border-gray-300 p-2"
              />
            </div>
            <button
              onClick={handleAddToCart}
              disabled={!product.stock || product.stock === 0}
              className={`cursor-pointer rounded-lg px-8 py-4 text-lg font-semibold transition-all ${
                product.stock > 0
                  ? 'bg-gradient-to-r from-red-600 to-red-500 text-white hover:-translate-y-0.5 hover:from-red-700 hover:to-red-600 hover:shadow-lg'
                  : 'cursor-not-allowed bg-gray-300'
              }`}
            >
              {product.stock > 0 ? '🛒 Add to Cart' : 'Out of Stock'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
