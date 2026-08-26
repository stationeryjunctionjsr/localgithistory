'use client';

import { useState, useEffect } from 'react';
import api from '@/utils/api';
import ZoneMeshGraph from '@/components/SellerAdmin/ZoneMeshGraph';
import { toast } from 'react-toastify';

export default function AdminCoverage() {
  const [sellers, setSellers] = useState<any[]>([]);
  const [valets, setValets] = useState<any[]>([]);
  const [zones, setZones] = useState<any[]>([]);
  const [selectedSeller, setSelectedSeller] = useState<string>('');
  const [activeOrders, setActiveOrders] = useState<any[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [sellersRes, valetsRes, zonesRes] = await Promise.all([
        api.get('/users?role=wholesaler'),
        api.get('/users?role=valet'),
        api.get('/delivery-zones')
      ]);
      setSellers(sellersRes.data.filter((s: any) => s.isSellerAdmin));
      setValets(valetsRes.data);
      setZones(zonesRes.data || []);
    } catch (e) {
      toast.error('Failed to load coverage data');
    }
  };

  const seller = sellers.find(s => s._id === selectedSeller || s.id === selectedSeller);
  const sellerPincodes = seller?.sellerPermissions?.serviceablePincodes || [];
  
  // Map seller pincodes to zones
  const sellerZonesSet = new Set<string>();
  sellerPincodes.forEach((pin: string) => {
    const z = zones.find(zone => zone.pincodes?.includes(pin));
    if (z) sellerZonesSet.add(z.id || z._id);
  });
  const sellerZones = Array.from(sellerZonesSet);
  
  const mappedValets = valets.map(v => ({
    id: v._id || v.id,
    name: v.name || 'Valet',
    zones: v.serviceAreaZones || []
  }));

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Network Coverage Mesh</h1>
      
      <div className="mb-6 bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <label className="block text-sm font-medium text-slate-700 mb-2">Select Seller to View Mesh</label>
        <select 
          className="border border-slate-300 rounded-md px-3 py-2 w-full max-w-md bg-white"
          value={selectedSeller}
          onChange={e => setSelectedSeller(e.target.value)}
        >
          <option value="">-- Choose a Seller --</option>
          {sellers.map(s => (
            <option key={s._id || s.id} value={s._id || s.id}>{s.name} ({s.companyName})</option>
          ))}
        </select>
      </div>

      {seller ? (
        <ZoneMeshGraph 
          sellerName={seller.name}
          sellerZones={sellerZones}
          valets={mappedValets}
          activeOrders={activeOrders}
        />
      ) : (
        <div className="p-12 text-center text-slate-500 bg-slate-50 rounded-lg border border-slate-200">
          Please select a seller to visualize their valet coverage mesh.
        </div>
      )}
    </div>
  );
}
