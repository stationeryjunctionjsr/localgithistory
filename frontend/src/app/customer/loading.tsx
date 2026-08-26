/**
 * Route-level loading skeleton for /customer
 * Shown by Next.js App Router during navigation while server data fetches resolve.
 * The page itself uses Promise.all + revalidate:60, so this only shows on cold cache.
 */
export default function CustomerLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Banner skeleton */}
      <div className="h-64 w-full animate-pulse bg-gray-200 md:h-80" />

      {/* Category tags skeleton */}
      <div className="mx-auto max-w-7xl px-4 py-6">
        <div className="flex gap-3 overflow-hidden">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-9 w-24 flex-shrink-0 animate-pulse rounded-full bg-gray-200"
            />
          ))}
        </div>
      </div>

      {/* Products grid skeleton */}
      <div className="mx-auto max-w-7xl px-4 pb-12">
        <div className="mb-4 h-6 w-40 animate-pulse rounded bg-gray-200" />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-2">
              <div className="aspect-square w-full animate-pulse rounded-xl bg-gray-200" />
              <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-gray-200" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
