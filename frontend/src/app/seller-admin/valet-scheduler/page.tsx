'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateIST } from '@/utils/dateUtils';
import ZoneMeshGraph from '@/components/SellerAdmin/ZoneMeshGraph';

interface ValetAvailability {
  _id: string;
  valetId: string;
  valetName: string;
  valetPhone: string;
  date: string;
  availabilityType: 'full_day' | 'custom';
  slots: string[];
  serviceAreaZones?: string[];
}

export default function ValetScheduler() {
  const { user } = useAuth();
  const [availabilities, setAvailabilities] = useState<ValetAvailability[]>([]);
  const [activeOrders, setActiveOrders] = useState<any[]>([]);
  const [zones, setZones] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [availRes, ordersRes, zonesRes] = await Promise.all([
        api.get('/valet-availability'),
        api.get('/seller-orders?status=pending_valet,accepted,shipped,out_for_delivery'),
        api.get('/delivery-zones')
      ]);
      setAvailabilities(availRes.data || []);
      setZones(zonesRes.data || []);
      const liveStatuses = ['pending', 'pending_valet', 'accepted', 'processing', 'shipped', 'out_for_delivery'];
      const orders = ordersRes.data?.subOrders || [];
      setActiveOrders(orders.filter((o: any) => liveStatuses.includes(o.status)));
    } catch (err: any) {
      toast.error('Failed to load data.');
    } finally {
      setLoading(false);
    }
  };

  const getUpcomingDates = () => {
    const dates = [];
    const today = new Date();
    for (let i = 0; i < 7; i++) {
      const d = new Date(today);
      d.setDate(d.getDate() + i);
      dates.push(d.toISOString().split('T')[0]);
    }
    return dates;
  };

  const upcomingDates = getUpcomingDates();
  
  // Group by valetId
  const valetsMap: Record<string, { id: string; name: string; phone: string; zones: string[]; schedule: Record<string, ValetAvailability> }> = {};
  
  availabilities.forEach(a => {
    if (!valetsMap[a.valetId]) {
      valetsMap[a.valetId] = {
        id: a.valetId,
        name: a.valetName || 'Unknown Valet',
        phone: a.valetPhone || 'N/A',
        zones: a.serviceAreaZones || [],
        schedule: {}
      };
    }
    valetsMap[a.valetId].schedule[a.date] = a;
  });

  const valetList = Object.values(valetsMap);
  const sellerPincodes = user?.sellerPermissions?.serviceablePincodes || [];
  
  const sellerZonesSet = new Set<string>();
  sellerPincodes.forEach((pin: string) => {
    const z = zones.find(zone => zone.pincodes?.includes(pin));
    if (z) sellerZonesSet.add(z.id || z._id);
  });
  const sellerZones = Array.from(sellerZonesSet);
  
  const sellerName = user?.name || user?.companyName || 'Seller';

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Valet Scheduler</h1>
          <p className="text-sm text-slate-500 mt-1">
            View the availability of valets servicing your area.
          </p>
        </div>
        <button
          onClick={fetchData}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Refresh Schedule
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">Loading schedule...</div>
        ) : valetList.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No valets have marked availability in your service area yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500">
                  <th className="px-6 py-4 font-semibold">Valet</th>
                  {upcomingDates.map(date => (
                    <th key={date} className="px-6 py-4 font-semibold whitespace-nowrap text-center">
                      {formatDateIST(date)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {valetList.map((valet, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{valet.name}</div>
                      <div className="text-slate-500 text-xs mt-0.5">{valet.phone}</div>
                    </td>
                    {upcomingDates.map(date => {
                      const avail = valet.schedule[date];
                      return (
                        <td key={date} className="px-6 py-4 text-center">
                          {!avail ? (
                            <span className="inline-block px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                              Not Set
                            </span>
                          ) : avail.availabilityType === 'full_day' ? (
                            <span className="inline-block px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                              Available
                            </span>
                          ) : (
                            <span className="inline-block px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700" title={avail.slots.join(', ')}>
                              Custom Slots
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {!loading && valetList.length > 0 && (
        <div className="mt-8">
          <ZoneMeshGraph 
            sellerName={sellerName}
            sellerZones={sellerZones}
            valets={valetList.map(v => ({ id: v.id, name: v.name, zones: v.zones }))}
            activeOrders={activeOrders}
          />
        </div>
      )}
    </div>
  );
}
