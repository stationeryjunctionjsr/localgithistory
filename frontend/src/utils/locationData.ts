// This file is kept as a fallback. The primary data source is now the backend API at /api/pincodes.
// The data is generated from Pincodes.xlsx and served via backend/app/data/pincode_master.json.

export interface LocationRepository {
  [state: string]: {
    [district: string]: string[];
  };
}

// Empty fallback — the frontend fetches from the API dynamically
export const locationData: LocationRepository = {};
