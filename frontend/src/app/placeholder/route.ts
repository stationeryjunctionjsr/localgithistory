import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const text = searchParams.get('text') || 'Stationery';

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
    <defs>
      <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#f8fafc;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#e2e8f0;stop-opacity:1" />
      </linearGradient>
    </defs>
    
    <!-- Background -->
    <rect width="100%" height="100%" fill="url(#grad)" />
    
    <!-- Decorative geometric background elements -->
    <circle cx="400" cy="0" r="150" fill="#cbd5e1" opacity="0.15" />
    <circle cx="0" cy="400" r="200" fill="#94a3b8" opacity="0.1" />
    
    <!-- Icon/Illustration (Notebook/Pen style sketch) -->
    <g transform="translate(150, 110)" opacity="0.75">
      <!-- Notebook Back/Shadow -->
      <rect x="14" y="14" width="76" height="96" rx="8" fill="#94a3b8" opacity="0.4" />
      
      <!-- Notebook Body -->
      <rect x="10" y="10" width="76" height="96" rx="8" fill="#ffffff" stroke="#94a3b8" stroke-width="3" />
      
      <!-- Bookmark ribbon -->
      <path d="M30 10 L30 45 L40 37 L50 45 L50 10" fill="#f43f5e" opacity="0.8" />
      
      <!-- Notebook Lines -->
      <line x1="26" y1="50" x2="70" y2="50" stroke="#cbd5e1" stroke-width="2.5" stroke-linecap="round" />
      <line x1="26" y1="64" x2="70" y2="64" stroke="#cbd5e1" stroke-width="2.5" stroke-linecap="round" />
      <line x1="26" y1="78" x2="60" y2="78" stroke="#cbd5e1" stroke-width="2.5" stroke-linecap="round" />
      
      <!-- Pen/Pencil crossing -->
      <g transform="rotate(-25, 45, 60)">
        <rect x="86" y="0" width="8" height="90" rx="2" fill="#3b82f6" stroke="#1d4ed8" stroke-width="1.5" />
        <!-- Pen Tip -->
        <polygon points="86,0 90,-10 94,0" fill="#e2e8f0" stroke="#1d4ed8" stroke-width="1.5" />
        <polygon points="88,-5 90,-10 92,-5" fill="#1e293b" />
        <!-- Eraser -->
        <rect x="86" y="85" width="8" height="8" rx="1" fill="#f43f5e" />
      </g>
    </g>

    <!-- Content Branding -->
    <rect x="40" y="245" width="320" height="2" fill="#cbd5e1" opacity="0.5" />
    
    <!-- Dynamic Product Name Text -->
    <text x="50%" y="278" dominant-baseline="middle" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="700" fill="#334155">
      ${text}
    </text>
    
    <!-- Subtitle/Store name -->
    <text x="50%" y="308" dominant-baseline="middle" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" fill="#64748b" letter-spacing="1.5">
      STATIONERY JUNCTION
    </text>
  </svg>`;

  return new NextResponse(svg, {
    headers: {
      'Content-Type': 'image/svg+xml',
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
}
