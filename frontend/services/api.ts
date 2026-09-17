type ApiError = {
  detail?: unknown;
  message?: unknown;
};

type ValidationError = {
  loc?: unknown;
  msg?: unknown;
};

const fieldLabels: Record<string, string> = {
  gstin: "GSTIN",
  pan: "PAN",
  mobile_number: "Mobile number",
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function fieldLabel(location: unknown): string | null {
  if (!Array.isArray(location)) return null;
  const field = [...location].reverse().find((item): item is string => typeof item === "string" && item !== "body");
  if (!field) return null;
  return fieldLabels[field] ?? field.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function readableValidationMessage(error: ValidationError): string {
  const message = typeof error.msg === "string" ? error.msg.replace(/^Value error,\s*/i, "") : "The submitted value is invalid.";
  if (/GSTIN is required/i.test(message)) return "GSTIN is required for a registered business.";
  if (/valid GSTIN format/i.test(message)) return "GSTIN format is invalid.";
  if (/valid PAN format/i.test(message)) return "PAN format is invalid.";
  const label = fieldLabel(error.loc);
  if (/Field required/i.test(message)) return `${label ?? "This field"} is required.`;
  return label ? `${label}: ${message}` : message;
}

/** Convert API and network failures into safe, human-readable UI messages. */
export function apiErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === "string" && payload.trim()) return payload;
  if (Array.isArray(payload)) return payload.map((item) => readableValidationMessage(isRecord(item) ? item : {})).join(" ");
  if (isRecord(payload)) {
    const error = payload as ApiError;
    if (typeof error.detail === "string" && error.detail.trim()) return error.detail;
    if (Array.isArray(error.detail)) return apiErrorMessage(error.detail, fallback);
    if (typeof error.message === "string" && error.message.trim()) return error.message;
  }
  return fallback;
}

export function caughtErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message.trim() ? error.message : fallback;
}
