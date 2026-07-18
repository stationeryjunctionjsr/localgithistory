import CollectionDetailClient from '@/components/CollectionDetailClient';
import { Metadata } from 'next';
import { Suspense } from 'react';

export const revalidate = 300; // 5 minutes caching

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const decodedSlug = decodeURIComponent(params.slug);
  const canonicalUrl = `https://www.stationeryjunction.com/collections/${encodeURIComponent(params.slug)}`;
  return {
    title: `${decodedSlug} | Collections | Stationery Junction`,
    description: `Shop our curated collection: ${decodedSlug}.`,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: `${decodedSlug} | Stationery Junction`,
      description: `Shop our curated collection: ${decodedSlug}.`,
      url: canonicalUrl,
      type: 'website',
    },
  };
}

export default async function CollectionDetailPage({ params }: { params: { slug: string } }) {
  const baseURL = process.env.NEXT_PUBLIC_API_URL;
  if (!baseURL) {
    throw new Error('NEXT_PUBLIC_API_URL is not defined');
  }
  const slug = decodeURIComponent(params.slug);
  const fetchOptions: RequestInit = {
    next: { revalidate: 300 },
    headers: { 'Content-Type': 'application/json' },
  };

  const [colsRes, bannersRes] = await Promise.all([
    fetch(`${baseURL}/collections/public`, fetchOptions).catch(() => null),
    fetch(
      `${baseURL}/banners/public?pageType=Collection&pageId=${encodeURIComponent(slug)}&userRole=guest`,
      fetchOptions
    ).catch(() => null),
  ]);

  const extractJson = async (res: Response | null) =>
    res?.ok ? res.json().catch(() => null) : null;

  const [colsRaw, bannersRaw] = await Promise.all([extractJson(colsRes), extractJson(bannersRes)]);

  let collectionInfo = null;
  if (colsRaw) {
    const list = Array.isArray(colsRaw) ? colsRaw : colsRaw?.data || [];
    const match = list.find(
      (c: any) => c?._id === slug || (c?.name || '').toLowerCase() === slug.toLowerCase()
    );
    if (match) {
      collectionInfo = {
        _id: match._id,
        name: match.name || slug,
        description: match.description,
        imageUrl: match.imageUrl,
        image: match.image,
      };
    }
  }

  const initialBanners = Array.isArray(bannersRaw) ? bannersRaw.filter((b: any) => b.isActive) : [];

  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-white text-xs uppercase tracking-widest text-gray-400">
          Loading Collection...
        </div>
      }
    >
      <CollectionDetailClient
        initialCollectionInfo={collectionInfo || { name: slug }}
        initialBanners={initialBanners}
      />
    </Suspense>
  );
}
