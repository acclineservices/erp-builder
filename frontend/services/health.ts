export type BackendHealthState = "checking" | "available" | "unavailable";

interface HealthResponse {
  status: "ok";
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export async function checkBackendHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/health`, { signal });

  if (!response.ok) {
    throw new Error(`Health endpoint returned ${response.status}.`);
  }

  const data: unknown = await response.json();

  if (typeof data !== "object" || data === null || !("status" in data) || (data as { status?: unknown }).status !== "ok") {
    throw new Error("Health endpoint returned an unexpected response.");
  }

  return data as HealthResponse;
}
