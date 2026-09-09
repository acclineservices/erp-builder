import type { AccessibleCompany } from "./auth";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type AddressFields = {
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string | null;
};

export type CompanyProfile = AddressFields & {
  id: string;
  business_name: string;
  legal_name: string | null;
  display_name: string | null;
  business_type: string;
  status: "active" | "suspended" | "closed";
  gst_status: string | null;
  gstin: string | null;
  email: string | null;
  phone: string | null;
  logo_url: string | null;
  setup_progress: number;
};

export type Branch = AddressFields & {
  id: string;
  name: string;
  code: string | null;
  email: string | null;
  phone: string | null;
  is_active: boolean;
};

export type Warehouse = AddressFields & {
  id: string;
  name: string;
  code: string | null;
  branch_id: string | null;
  contact_person: string | null;
  contact_number: string | null;
  is_active: boolean;
};

export type CompanyUpdate = Omit<CompanyProfile, "id" | "business_name" | "status" | "setup_progress">;
export type BranchInput = Omit<Branch, "id" | "is_active">;
export type WarehouseInput = Omit<Warehouse, "id" | "is_active">;

async function request<T>(path: string, companyId: string, method = "GET", body?: object): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    credentials: "include",
    headers: { "X-Company-ID": companyId, ...(body ? { "Content-Type": "application/json" } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail ?? "Organization data could not be updated.");
  return payload as T;
}

export const organizationApi = {
  company: (companyId: string) => request<CompanyProfile>("/organization/company", companyId),
  updateCompany: (companyId: string, payload: CompanyUpdate) => request<CompanyProfile>("/organization/company", companyId, "PUT", payload),
  branches: (companyId: string) => request<Branch[]>("/organization/branches", companyId),
  createBranch: (companyId: string, payload: BranchInput) => request<Branch>("/organization/branches", companyId, "POST", payload),
  updateBranch: (companyId: string, branchId: string, payload: BranchInput) => request<Branch>(`/organization/branches/${branchId}`, companyId, "PUT", payload),
  setBranchStatus: (companyId: string, branchId: string, is_active: boolean) => request<Branch>(`/organization/branches/${branchId}/status`, companyId, "PATCH", { is_active }),
  warehouses: (companyId: string) => request<Warehouse[]>("/organization/warehouses", companyId),
  createWarehouse: (companyId: string, payload: WarehouseInput) => request<Warehouse>("/organization/warehouses", companyId, "POST", payload),
  updateWarehouse: (companyId: string, warehouseId: string, payload: WarehouseInput) => request<Warehouse>(`/organization/warehouses/${warehouseId}`, companyId, "PUT", payload),
  setWarehouseStatus: (companyId: string, warehouseId: string, is_active: boolean) => request<Warehouse>(`/organization/warehouses/${warehouseId}/status`, companyId, "PATCH", { is_active }),
};

export function selectedCompanyName(company?: AccessibleCompany): string {
  return company?.business_name ?? "your company";
}
