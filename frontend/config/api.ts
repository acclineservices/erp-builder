/** API endpoint selected at Vite build time; local development remains the default. */
export const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
