const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type AuthUser = {
  id: string;
  name: string;
  email: string | null;
  mobile_number: string | null;
  account_state: string;
  is_platform_admin: boolean;
};

export type AccessibleCompany = {
  id: string;
  business_name: string;
};

type SessionResponse = { user: AuthUser; expires_at: string };

async function request<T>(path: string, body?: object): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: body ? "POST" : "GET",
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail ?? "Something went wrong. Please try again.");
  return payload as T;
}

export const authApi = {
  me: () => request<SessionResponse>("/auth/me"),
  companies: () => request<AccessibleCompany[]>("/auth/companies"),
  emailLogin: (email: string, password: string, remember_me: boolean) => request<SessionResponse>("/auth/login/email", { email, password, remember_me }),
  requestMobileLogin: (mobile_number: string) => request<{ message: string }>("/auth/login/mobile/request", { mobile_number }),
  verifyMobileLogin: (mobile_number: string, code: string, remember_me: boolean) => request<SessionResponse>("/auth/login/mobile/verify", { mobile_number, code, remember_me }),
  requestActivation: (email: string) => request<{ message: string }>("/auth/activation/request", { email }),
  completeActivation: (token: string, password: string) => request<{ message: string }>("/auth/activation/complete", { token, password }),
  verifyEmail: (token: string) => request<{ message: string }>("/auth/verify/email", { token }),
  requestMobileVerification: (mobile_number: string) => request<{ message: string }>("/auth/verify/mobile/request", { mobile_number }),
  verifyMobile: (mobile_number: string, code: string) => request<{ message: string }>("/auth/verify/mobile", { mobile_number, code }),
  forgotPassword: (email: string) => request<{ message: string }>("/auth/password/forgot", { email }),
  resetPassword: (token: string, new_password: string) => request<{ message: string }>("/auth/password/reset", { token, new_password }),
  requestMobileReset: (mobile_number: string) => request<{ message: string }>("/auth/password/mobile/request", { mobile_number }),
  resetMobilePassword: (mobile_number: string, code: string, new_password: string) => request<{ message: string }>("/auth/password/mobile/reset", { mobile_number, code, new_password }),
  logout: () => request<{ message: string }>("/auth/logout", {}),
};
