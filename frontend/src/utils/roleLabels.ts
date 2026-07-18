/**
 * Terminology: Retail Customer (default) and Business Customer.
 * Internal roles: customer, wholesaler, valet, super_admin.
 */

export const ROLE_LABELS: Record<string, string> = {
  customer: 'Retail Customer',
  wholesaler: 'Business Customer',
  valet: 'Delivery Valet',
  super_admin: 'Super Admin',
};

export function getRoleDisplayLabel(role: string | undefined | null): string {
  if (!role) return 'Retail Customer';
  return ROLE_LABELS[role] ?? 'Retail Customer';
}

export function isBusinessRole(role: string | undefined | null): boolean {
  return role === 'wholesaler';
}

export function isRetailRole(role: string | undefined | null): boolean {
  return role === 'customer';
}
