/**
 * Route-level loading skeleton for /wholesaler
 * Shown by Next.js App Router during navigation while server data fetches resolve.
 */
export default function WholesalerLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Banner skeleton */}
      <div className="h-64 w-full animate-pulse bg-gray-200 md:h-80" />

      {/* Stats bar skeleton */}
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl gap-8 px-4 py-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-1">
              <div className="h-5 w-20 animate-pulse rounded bg-gray-200" />
              <div className="h-4 w-14 animate-pulse rounded bg-gray-100" />
            </div>
          ))}
        </div>
      </div>

      {/* Products grid skeleton */}
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-4 h-6 w-48 animate-pulse rounded bg-gray-200" />
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
