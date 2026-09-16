const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type Permission = { code: string; description: string | null };
export type Role = { id: string; name: string; description: string | null; is_active: boolean; is_system_managed: boolean; permission_codes: string[] };
export type Location = { id: string; name: string; is_active: boolean; branch_id?: string | null };
export type CompanyUser = {
  id: string; name: string; email: string; mobile_number: string; account_state: string; email_verified: boolean; mobile_verified: boolean;
  company_access_active: boolean; role_ids: string[]; role_names: string[]; default_branch_id: string | null; default_warehouse_id: string | null; has_active_session: boolean;
};
export type AuditEvent = { id: string; action: string; actor_user_id: string | null; target_user_id: string | null; details: string | null; created_at: string };
export type Bootstrap = { users: CompanyUser[]; roles: Role[]; permissions: Permission[]; branches: Location[]; warehouses: Location[]; audit_events: AuditEvent[]; effective_permissions: string[] };
export type UserPayload = { name: string; email?: string; mobile_number?: string; role_ids: string[]; default_branch_id: string | null; default_warehouse_id: string | null };
export type RolePayload = { name: string; description: string | null; permission_codes: string[]; is_active: boolean };

async function request<T>(path: string, companyId: string, method = "GET", body?: object): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { method, credentials: "include", headers: { "X-Company-ID": companyId, ...(body ? { "Content-Type": "application/json" } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail ?? "Unable to complete this administration action.");
  return payload as T;
}

export const administrationApi = {
  bootstrap: (companyId: string) => request<Bootstrap>("/administration/bootstrap", companyId),
  invite: (companyId: string, payload: UserPayload) => request<CompanyUser>("/administration/users", companyId, "POST", payload),
  updateUser: (companyId: string, userId: string, payload: UserPayload) => request<CompanyUser>(`/administration/users/${userId}`, companyId, "PUT", payload),
  setUserStatus: (companyId: string, userId: string, is_active: boolean) => request<CompanyUser>(`/administration/users/${userId}/status`, companyId, "PATCH", { is_active }),
  forceLogout: (companyId: string, userId: string) => request<{ message: string }>(`/administration/users/${userId}/force-logout`, companyId, "POST", {}),
  reset: (companyId: string, userId: string) => request<{ message: string }>(`/administration/users/${userId}/reset`, companyId, "POST", {}),
  createRole: (companyId: string, payload: RolePayload) => request<Role>("/administration/roles", companyId, "POST", payload),
  updateRole: (companyId: string, roleId: string, payload: RolePayload) => request<Role>(`/administration/roles/${roleId}`, companyId, "PUT", payload),
  cloneRole: (companyId: string, roleId: string, payload: RolePayload) => request<Role>(`/administration/roles/${roleId}/clone`, companyId, "POST", payload),
};
