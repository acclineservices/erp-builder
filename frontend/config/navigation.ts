export type NavigationItem = {
  label: string;
  path: string;
  icon: "home" | "sales" | "purchases" | "inventory" | "accounting" | "reports" | "setup" | "users" | "settings";
  description: string;
};

export const navigationItems: NavigationItem[] = [
  { label: "Dashboard", path: "/app/dashboard", icon: "home", description: "Your workspace overview." },
  { label: "Sales", path: "/app/sales", icon: "sales", description: "Sales workflows will be introduced in a future module." },
  { label: "Purchases", path: "/app/purchases", icon: "purchases", description: "Purchase workflows will be introduced in a future module." },
  { label: "Inventory", path: "/app/inventory", icon: "inventory", description: "Inventory workflows will be introduced in a future module." },
  { label: "Accounting", path: "/app/accounting", icon: "accounting", description: "Accounting workflows will be introduced in a future module." },
  { label: "Reports", path: "/app/reports", icon: "reports", description: "Report workflows will be introduced in a future module." },
  { label: "Masters / Setup", path: "/app/setup", icon: "setup", description: "Master data and setup will be introduced in a future module." },
  { label: "Users & Roles", path: "/app/users", icon: "users", description: "Administration workflows remain intentionally deferred." },
  { label: "Settings", path: "/app/settings", icon: "settings", description: "Personal and company settings will be introduced in a future module." },
];

export function navigationForPath(path: string): NavigationItem {
  return navigationItems.find((item) => item.path === path) ?? navigationItems[0];
}
