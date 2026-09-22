import type { AccessibleCompany } from "./auth";
import { apiErrorMessage } from "./api";
import { apiBaseUrl } from "../config/api";

export type PartyType = "customer" | "supplier" | "both";
export type GstStatus = "registered" | "unregistered" | "composition" | "exempt";
export type Party = {
  id: string; display_name: string; legal_name: string | null; code: string | null; customer_code: string | null; supplier_code: string | null; party_type: PartyType;
  contact_person: string | null; mobile_number: string | null; alternate_mobile: string | null; email: string | null;
  address_line1: string | null; address_line2: string | null; city: string | null; state: string | null; postal_code: string | null; country: string | null;
  gst_status: GstStatus; gstin: string | null; pan: string | null; opening_balance: number; opening_balance_type: "debit" | "credit"; credit_limit: number | null; payment_terms_days: number | null; notes: string | null; is_active: boolean;
};
export type PartyInput = Omit<Party, "id" | "customer_code" | "supplier_code" | "is_active">;

async function request<T>(path: string, companyId: string, method = "GET", body?: object): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { method, credentials: "include", headers: { "X-Company-ID": companyId, ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(apiErrorMessage(payload, "Party data could not be updated."));
  return payload as T;
}

function path(role: "customer" | "supplier") { return `/parties/${role}s`; }
export const partiesApi = {
  list: (role: "customer" | "supplier", companyId: string, params: { search?: string; active?: string; party_type?: string } = {}) => request<Party[]>(`${path(role)}${new URLSearchParams(Object.entries(params).filter(([, value]) => value !== undefined && value !== "") as [string, string][]).toString() ? "?" + new URLSearchParams(Object.entries(params).filter(([, value]) => value !== undefined && value !== "") as [string, string][]).toString() : ""}`, companyId),
  create: (role: "customer" | "supplier", companyId: string, payload: PartyInput) => request<Party>(path(role), companyId, "POST", payload),
  update: (role: "customer" | "supplier", companyId: string, id: string, payload: PartyInput) => request<Party>(`${path(role)}/${id}`, companyId, "PUT", payload),
  setStatus: (role: "customer" | "supplier", companyId: string, id: string, is_active: boolean) => request<Party>(`${path(role)}/${id}/status`, companyId, "PATCH", { is_active }),
};
export function companyName(company?: AccessibleCompany) { return company?.business_name ?? "your company"; }
