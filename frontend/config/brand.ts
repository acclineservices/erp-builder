export const applicationBrand = {
  companyName: "Pruvian Technologies",
  productName: "Pruvian",
  shortName: "P",
  tagline: "Run Better. Grow Smarter.",
  description: "Cloud Accounting & Business Management Platform",
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
