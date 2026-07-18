import { notFound } from 'next/navigation';
import ProductDetailClient from '@/components/ProductDetailClient';
import { Metadata } from 'next';

export const revalidate = 300;

const baseURL = process.env.NEXT_PUBLIC_API_URL;
const apiBase = process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 'https://api.stationeryjunction.com';

async function getProduct(id: string) {
  try {
    const res = await fetch(`${baseURL}/products/public/${id}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    return res.json();
  // eslint-disable-next-line unused-imports/no-unused-vars
  } catch (e) {
    return null;
  }
}

export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const product = await getProduct(params.id);
  if (!product) return { title: 'Product Not Found | Stationery Junction' };

  const firstImage = product.images?.[0] ? 
    (product.images[0].startsWith('http') ? product.images[0] : `${apiBase}${product.images[0]}`) 
    : 'https://www.stationeryjunction.com/og-image.jpg';

  const canonicalUrl = `https://www.stationeryjunction.com/customer/product/${params.id}`;
  return {
    title: `${product.name} | ${product.brand || 'Stationery Junction'}`,
    description: product.description?.substring(0, 160) || `Buy ${product.name} at Stationery Junction`,
    metadataBase: new URL('https://www.stationeryjunction.com'),
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: product.name,
      description: product.description?.substring(0, 160),
      url: canonicalUrl,
      siteName: 'Stationery Junction',
      images: [{ url: firstImage, width: 800, height: 600, alt: product.name }],
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: product.name,
      description: product.description?.substring(0, 160),
      images: [firstImage],
    },
  };
}

export default async function CustomerProductPage({ params }: { params: { id: string } }) {
  const product = await getProduct(params.id);

  if (!product) {
    notFound();
  }

  // Generate JSON-LD Schema
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    image: product.images?.map((img: string) => img.startsWith('http') ? img : `${apiBase}${img}`) || [],
    description: product.description,
    sku: product.sku || product._id,
    brand: {
      '@type': 'Brand',
      name: product.brand || 'Stationery Junction',
    },
    offers: {
      '@type': 'Offer',
      url: `https://www.stationeryjunction.com/customer/product/${params.id}`,
      priceCurrency: 'INR',
      price: product.price,
      itemCondition: 'https://schema.org/NewCondition',
      availability: product.stock > 0 ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
    },
    ...(product.rating ? {
      aggregateRating: {
        '@type': 'AggregateRating',
        ratingValue: product.rating,
        reviewCount: product.reviews || 1,
      }
    } : {})
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <ProductDetailClient initialProduct={product} />
    </>
  );
}
