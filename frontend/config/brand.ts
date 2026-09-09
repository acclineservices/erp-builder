export const applicationBrand = {
  productName: "ERP Builder",
  shortName: "EB",
  supportLabel: "Help & support",
  assistantLabel: "Assistant",
};

export const supportedLanguages = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
  { code: "mr", label: "Marathi" },
] as const;

export type LanguageCode = (typeof supportedLanguages)[number]["code"];
export type ThemeMode = "light" | "dark" | "system";
