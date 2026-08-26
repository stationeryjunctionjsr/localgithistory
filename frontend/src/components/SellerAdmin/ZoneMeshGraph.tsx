import React, { useState } from 'react';

interface ZoneMeshGraphProps {
  sellerName: string;
  sellerZones: string[];
  valets: { id: string; name: string; zones: string[] }[];
  activeOrders?: any[]; // Orders related to this seller
}

export default function ZoneMeshGraph({ sellerName, sellerZones, valets, activeOrders = [] }: ZoneMeshGraphProps) {
  const [selectedValetId, setSelectedValetId] = useState<string | 'ALL'>('ALL');

  const activeValets = selectedValetId === 'ALL' ? valets : valets.filter((v) => v.id === selectedValetId);

  // Collect all unique zones involved
  const allValetZonesSet = new Set<string>();
  activeValets.forEach((v) => v.zones.forEach((p) => allValetZonesSet.add(p)));

  const allzonesList = Array.from(new Set([...sellerZones, ...Array.from(allValetZonesSet)])).sort();

  // Compute live order counts
  const zoneOrderCounts: Record<string, number> = {};
  const valetOrderCounts: Record<string, number> = {};
  
  activeOrders.forEach(order => {
    const zone = order.shippingAddress?.pincode; // Note: For this to work perfectly with zones, the backend needs to attach zoneId to the order. But for now we just fallback to the pincode or a populated zone.
    if (zone) {
      zoneOrderCounts[zone] = (zoneOrderCounts[zone] || 0) + 1;
    }
    const valetId = order.assignedValet;
    if (valetId) {
      valetOrderCounts[valetId] = (valetOrderCounts[valetId] || 0) + 1;
    }
  });

  // Dimensions
  const width = 800;
  const height = Math.max(500, allzonesList.length * 40 + 100);
  
  // Node positions
  const sellerNode = { id: 'seller', x: 100, y: height / 2, label: sellerName, type: 'seller' };
  
  const zoneNodes = allzonesList.map((zone, i) => {
    const spacing = (height - 100) / Math.max(1, allzonesList.length - 1);
    const startY = allzonesList.length === 1 ? height / 2 : 50;
    return {
      id: zone,
      x: 400,
      y: startY + i * spacing,
      label: zone,
      inSeller: sellerZones.includes(zone),
      inValet: activeValets.some(v => v.zones.includes(zone)),
    };
  });

  const valetNodes = activeValets.map((v, i) => {
    const spacing = (height - 100) / Math.max(1, activeValets.length - 1);
    const startY = activeValets.length === 1 ? height / 2 : 50;
    return {
      ...v,
      x: 700,
      y: startY + i * spacing,
      type: 'valet'
    };
  });

  return (
    <div className="w-full flex flex-col items-center bg-slate-50 p-6 rounded-xl border border-slate-200">
      <div className="mb-4 flex gap-4 items-center w-full justify-between">
        <h3 className="text-lg font-semibold text-slate-800">Coverage Mesh Viewer</h3>
        <select 
          className="border border-slate-300 rounded-md px-3 py-1.5 text-sm bg-white"
          value={selectedValetId}
          onChange={(e) => setSelectedValetId(e.target.value)}
        >
          <option value="ALL">All Valets</option>
          {valets.map(v => (
            <option key={v.id} value={v.id}>{v.name}</option>
          ))}
        </select>
      </div>

      <div className="relative overflow-x-auto w-full flex justify-center bg-white border border-slate-200 rounded-lg shadow-inner p-4">
        <svg width={width} height={height} className="max-w-full h-auto">
          <defs>
            <marker id="arrowHeadGreen" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#22c55e" />
            </marker>
            <marker id="arrowHeadGray" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#cbd5e1" />
            </marker>
          </defs>

          {/* Edges: Seller -> zone */}
          {zoneNodes.map(zoneNode => {
            if (!zoneNode.inSeller) return null;
            const isMatched = zoneNode.inSeller && zoneNode.inValet;
            return (
              <line
                key={`s-${zoneNode.id}`}
                x1={sellerNode.x + 40}
                y1={sellerNode.y}
                x2={zoneNode.x - 40}
                y2={zoneNode.y}
                stroke={isMatched ? '#22c55e' : '#cbd5e1'}
                strokeWidth={isMatched ? 2 : 1.5}
                markerEnd={isMatched ? 'url(#arrowHeadGreen)' : 'url(#arrowHeadGray)'}
                className="transition-all duration-300"
              />
            );
          })}

          {/* Edges: Valet -> zone */}
          {valetNodes.map(valetNode => {
            return zoneNodes.map(zoneNode => {
              if (!valetNode.zones.includes(zoneNode.id)) return null;
              const isMatched = zoneNode.inSeller && zoneNode.inValet;
              return (
                <line
                  key={`v-${valetNode.id}-${zoneNode.id}`}
                  x1={valetNode.x - 40}
                  y1={valetNode.y}
                  x2={zoneNode.x + 40}
                  y2={zoneNode.y}
                  stroke={isMatched ? '#22c55e' : '#cbd5e1'}
                  strokeWidth={isMatched ? 2 : 1.5}
                  strokeDasharray={isMatched ? "none" : "4 4"}
                  className="transition-all duration-300"
                />
              );
            });
          })}

          {/* Seller Node */}
          <g transform={`translate(${sellerNode.x}, ${sellerNode.y})`}>
            <circle r="40" fill="#4f46e5" className="shadow-lg" />
            <text textAnchor="middle" y="5" fill="white" fontSize="12" fontWeight="bold">Seller</text>
            <text textAnchor="middle" y="20" fill="#e0e7ff" fontSize="10">{sellerNode.label.substring(0, 12)}</text>
          </g>

          {/* zone Nodes */}
          {zoneNodes.map(zoneNode => {
            const isMatched = zoneNode.inSeller && zoneNode.inValet;
            const ordersCount = zoneOrderCounts[zoneNode.id] || 0;
            return (
              <g key={zoneNode.id} transform={`translate(${zoneNode.x}, ${zoneNode.y})`}>
                <rect x="-35" y="-15" width="70" height="30" rx="15" 
                  fill={isMatched ? '#dcfce7' : '#f1f5f9'}
                  stroke={isMatched ? '#22c55e' : '#94a3b8'} 
                  strokeWidth="2"
                  className="transition-colors duration-300"
                />
                <text textAnchor="middle" y="4" fill={isMatched ? '#166534' : '#475569'} fontSize="12" fontWeight="bold">
                  {zoneNode.label}
                </text>
                {ordersCount > 0 && (
                  <g transform="translate(25, -15)">
                    <circle r="10" fill="#ef4444" />
                    <text textAnchor="middle" y="3.5" fill="white" fontSize="9" fontWeight="bold">{ordersCount}</text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Valet Nodes */}
          {valetNodes.map(valetNode => {
            const ordersCount = valetOrderCounts[valetNode.id] || 0;
            return (
              <g key={valetNode.id} transform={`translate(${valetNode.x}, ${valetNode.y})`}>
                <circle r="35" fill="#f59e0b" />
                <text textAnchor="middle" y="5" fill="white" fontSize="12" fontWeight="bold">Valet</text>
                <text textAnchor="middle" y="20" fill="#fef3c7" fontSize="10">{valetNode.name.substring(0, 10)}</text>
                {ordersCount > 0 && (
                  <g transform="translate(25, -25)">
                    <rect x="-20" y="-8" width="40" height="16" rx="8" fill="#ef4444" />
                    <text textAnchor="middle" y="3" fill="white" fontSize="9" fontWeight="bold">{ordersCount} assigned</text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </div>
      
      <div className="mt-4 flex gap-6 text-sm flex-wrap">
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 bg-green-500 rounded"></div>
          <span className="text-slate-600">Matched Route (Serviceable)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 bg-slate-300 rounded"></div>
          <span className="text-slate-600">Unmatched / Out of Network</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
          <span className="text-slate-600">Live Orders</span>
        </div>
      </div>
    </div>
  );
}
