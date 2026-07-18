/**
 * Page-level skeleton components used as Suspense fallbacks and in loading.tsx
 * for the products, categories, and brands routes.
 *
 * Each skeleton approximates the visual structure of its page so the layout
 * feels stable rather than flashing a blank screen during navigation.
 */

function SkeletonBar({ className, style }: { className: string; style?: React.CSSProperties }) {
  return <div className={`animate-pulse rounded bg-gray-200 ${className}`} style={style} />;
}

function ProductCardSkeleton() {
  return (
    <div className="rounded-xl bg-white p-3 shadow-sm">
      <SkeletonBar className="mb-3 h-40 w-full rounded-lg" />
      <SkeletonBar className="mb-2 h-3 w-4/5" />
      <SkeletonBar className="mb-2 h-3 w-3/5" />
      <SkeletonBar className="h-5 w-2/5" />
    </div>
  );
}

function CategoryCardSkeleton() {
  return (
    <div className="rounded-xl bg-white p-3 shadow-sm">
      <SkeletonBar className="mb-3 h-28 w-full rounded-lg" />
      <SkeletonBar className="mb-2 h-3 w-3/4" />
      <SkeletonBar className="h-3 w-1/2" />
    </div>
  );
}

function BrandCardSkeleton() {
  return (
    <div className="flex flex-col items-center rounded-xl bg-white p-4 shadow-sm">
      <SkeletonBar className="mb-3 h-14 w-14 rounded-full" />
      <SkeletonBar className="h-3 w-16" />
    </div>
  );
}

/** Skeleton for the navbar strip shown at top of all pages */
function NavbarSkeleton() {
  return (
    <div className="animate-pulse border-b border-gray-100 bg-white px-6 py-4">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <SkeletonBar className="h-7 w-36 rounded" />
        <div className="hidden gap-6 md:flex">
          {[80, 70, 90, 75].map((w, i) => (
            <SkeletonBar key={i} className={`h-4 w-${w === 80 ? '20' : w === 70 ? '16' : w === 90 ? '24' : '20'} rounded`} />
          ))}
        </div>
        <div className="flex gap-3">
          <SkeletonBar className="h-8 w-8 rounded-full" />
          <SkeletonBar className="h-8 w-8 rounded-full" />
        </div>
      </div>
    </div>
  );
}

/** Skeleton for a hero banner strip */
function HeroBannerSkeleton() {
  return <SkeletonBar className="h-40 w-full rounded-none md:h-52" />;
}

// ── Public exports ─────────────────────────────────────────────────────────────

export function ProductsPageSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <NavbarSkeleton />
      <HeroBannerSkeleton />
      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Filter bar */}
        <div className="mb-6 flex animate-pulse flex-wrap gap-3">
          <SkeletonBar className="h-10 w-64 rounded-full" />
          <SkeletonBar className="h-10 w-24 rounded-full" />
          <SkeletonBar className="h-10 w-24 rounded-full" />
          <SkeletonBar className="h-10 w-20 rounded-full" />
        </div>
        {/* Product grid — 2×2 on mobile, 4 col on desktop */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}

export function CategoriesPageSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <NavbarSkeleton />
      <HeroBannerSkeleton />
      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Tag chips */}
        <div className="mb-6 flex animate-pulse flex-wrap gap-2">
          {[60, 80, 55, 70, 65, 75].map((w, i) => (
            <SkeletonBar key={i} className={`h-8 rounded-full`} style={{ width: w }} />
          ))}
        </div>
        {/* Category card grid */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <CategoryCardSkeleton key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}

export function BrandsPageSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50">
      <NavbarSkeleton />
      <HeroBannerSkeleton />
      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Search bar */}
        <SkeletonBar className="mb-6 h-11 w-full max-w-md animate-pulse rounded-full" />
        {/* Brand grid */}
        <div className="grid grid-cols-3 gap-4 md:grid-cols-4 lg:grid-cols-6">
          {Array.from({ length: 12 }).map((_, i) => (
            <BrandCardSkeleton key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
