import { MetadataRoute } from 'next';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://www.stationeryjunction.com';
const baseURL = process.env.NEXT_PUBLIC_API_URL;

async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url, { next: { revalidate: 3600 } });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Static high-priority pages
  const staticPages: MetadataRoute.Sitemap = [
    { url: siteUrl,                      lastModified: new Date(), changeFrequency: 'daily',   priority: 1.0 },
    { url: `${siteUrl}/products`,        lastModified: new Date(), changeFrequency: 'daily',   priority: 0.9 },
    { url: `${siteUrl}/categories`,      lastModified: new Date(), changeFrequency: 'weekly',  priority: 0.8 },
    { url: `${siteUrl}/brands`,          lastModified: new Date(), changeFrequency: 'weekly',  priority: 0.7 },
    { url: `${siteUrl}/customer`,        lastModified: new Date(), changeFrequency: 'daily',   priority: 0.9 },
  ];

  // Dynamic product URLs
  const productsData = await fetchJson<any>(`${baseURL}/products/public/`);
  const products: any[] = Array.isArray(productsData) ? productsData : (productsData?.data || []);
  const productURLs: MetadataRoute.Sitemap = products.map((product) => ({
    url: `${siteUrl}/customer/product/${product._id}`,
    lastModified: new Date(product.updatedAt || new Date()),
    changeFrequency: 'daily',
    priority: 0.8,
  }));

  // Dynamic category URLs
  const categories = await fetchJson<any[]>(`${baseURL}/categories/public`);
  const categoryURLs: MetadataRoute.Sitemap = (categories || []).map((cat: any) => ({
    url: `${siteUrl}/categories/${encodeURIComponent(cat.slug || cat.name)}`,
    lastModified: new Date(),
    changeFrequency: 'weekly',
    priority: 0.7,
  }));

  // Dynamic brand URLs
  const brandsData = await fetchJson<any[]>(`${baseURL}/categories/public/tags/all/brands`);
  const brandURLs: MetadataRoute.Sitemap = (brandsData || []).map((brand: any) => ({
    url: `${siteUrl}/brands/${encodeURIComponent(brand.slug || brand.name)}`,
    lastModified: new Date(),
    changeFrequency: 'weekly',
    priority: 0.6,
  }));

  // Dynamic collection URLs
  const collectionsData = await fetchJson<any>(`${baseURL}/collections/public`);
  const collections: any[] = Array.isArray(collectionsData)
    ? collectionsData
    : collectionsData?.collections || collectionsData?.data || [];
  const collectionURLs: MetadataRoute.Sitemap = collections.map((col: any) => ({
    url: `${siteUrl}/collections/${encodeURIComponent(col.slug || col.name)}`,
    lastModified: new Date(col.updatedAt || new Date()),
    changeFrequency: 'weekly',
    priority: 0.6,
  }));

  return [...staticPages, ...productURLs, ...categoryURLs, ...brandURLs, ...collectionURLs];
}
