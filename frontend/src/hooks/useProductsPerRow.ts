/**
 * useProductsPerRow
 *
 * Returns the number of product cards that fit in one row of the recommendation
 * section grid at the current viewport width.
 *
 * Grid definition (must match CustomerClient / WholesalerClient):
 *   default (< 640px)  → 2 cols
 *   sm      (≥ 640px)  → 3 cols
 *   md      (≥ 768px)  → 4 cols
 *   lg      (≥ 1024px) → 5 cols
 *   xl      (≥ 1280px) → 6 cols
 *
 * Tiering logic (derived from productsPerRow = R):
 *   count < R            → hide section entirely
 *   R  ≤ count < 2R      → show 1 row, no "Show more"
 *   2R ≤ count < 3R      → show 1 row initially; "Show more" reveals 1 more row  (total 2R)
 *   3R ≤ count < 4R      → show 1 row initially; "Show more" reveals 2 more rows (total 3R)
 *   count ≥ 4R           → show 1 row initially; "Show more" reveals 3 more rows (total 4R)
 */

import { useState, useEffect } from 'react';

// Breakpoints must stay in sync with the Tailwind grid class on the recommendation section:
//   grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6
const BREAKPOINTS: [number, number][] = [
  [1280, 6], // xl → 6 cols
  [1024, 5], // lg → 5 cols
  [768,  4], // md → 4 cols
  [640,  3], // sm → 3 cols
  [0,    2], // default → 2 cols
];

function getColsForWidth(width: number): number {
  for (const [bp, cols] of BREAKPOINTS) {
    if (width >= bp) return cols;
  }
  return 2;
}

export function useProductsPerRow(): number {
  const [cols, setCols] = useState<number>(() =>
    typeof window !== 'undefined' ? getColsForWidth(window.innerWidth) : 2
  );

  useEffect(() => {
    const update = () => setCols(getColsForWidth(window.innerWidth));
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  return cols;
}

/**
 * Given the total number of items and products-per-row, returns:
 *   - visible:  how many to show in the collapsed state (always 1 row = R items)
 *   - expanded: how many to show when expanded (up to 4 rows = 4R items)
 *   - showButton: whether to render the "Show more" button at all
 *   - hide:     true when there aren't enough items to fill even one row
 *
 * The frontend should:
 *   - Skip rendering the entire section when `hide` is true
 *   - Skip rendering the "Show more" button when `showButton` is false
 *   - Use `.slice(0, isExpanded ? expanded : visible)` on the items array
 */
export function getSectionDisplayConfig(
  count: number,
  productsPerRow: number
): {
  visible: number;
  expanded: number;
  showButton: boolean;
  hide: boolean;
} {
  const R = productsPerRow;

  if (count < R) {
    return { visible: R, expanded: R, showButton: false, hide: true };
  }
  if (count < 2 * R) {
    // 1 row, no Show more
    return { visible: R, expanded: R, showButton: false, hide: false };
  }
  if (count < 3 * R) {
    // Show more reveals 1 extra row (total 2 rows)
    return { visible: R, expanded: 2 * R, showButton: true, hide: false };
  }
  if (count < 4 * R) {
    // Show more reveals 2 extra rows (total 3 rows)
    return { visible: R, expanded: 3 * R, showButton: true, hide: false };
  }
  // Show more reveals 3 extra rows (total 4 rows = max 24 @ 6 cols)
  return { visible: R, expanded: 4 * R, showButton: true, hide: false };
}
