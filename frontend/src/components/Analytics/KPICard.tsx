'use client';


interface KPICardProps {
  title: string;
  value: string;
  trend: number;
  startDate: Date | null;
  endDate: Date | null;
}

// eslint-disable-next-line unused-imports/no-unused-vars
export default function KPICard({ title, value, trend }: KPICardProps) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-2 text-sm font-medium text-gray-600">{title}</h3>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {/* Placeholder for trend chart */}
      <div className="mt-4 h-12 rounded bg-gray-100">
        <svg className="h-full w-full" viewBox="0 0 100 50" preserveAspectRatio="none">
          <polyline
            points="0,50 20,45 40,40 60,35 80,30 100,25"
            fill="none"
            stroke="#3B82F6"
            strokeWidth="2"
          />
        </svg>
      </div>
    </div>
  );
}
