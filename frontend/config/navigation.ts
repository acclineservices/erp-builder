export type NavigationItem = {
  label: string;
  path: string;
  icon: "home" | "sales" | "purchases" | "inventory" | "accounting" | "reports" | "setup" | "users" | "settings" | "customers" | "suppliers" | "items";
  description: string;
};

export const navigationItems: NavigationItem[] = [
  { label: "Dashboard", path: "/app/dashboard", icon: "home", description: "Your workspace overview." },
  { label: "Customers", path: "/app/customers", icon: "customers", description: "Company customer master data." },
  { label: "Suppliers", path: "/app/suppliers", icon: "suppliers", description: "Company supplier master data." },
  { label: "Items", path: "/app/items", icon: "items", description: "Company item and service master data." },
  { label: "Item Categories", path: "/app/items/categories", icon: "items", description: "Company item categories." },
  { label: "Sales", path: "/app/sales", icon: "sales", description: "Sales workflows will be introduced in a future module." },
  { label: "Purchases", path: "/app/purchases", icon: "purchases", description: "Purchase workflows will be introduced in a future module." },
  { label: "Inventory", path: "/app/inventory", icon: "inventory", description: "Inventory workflows will be introduced in a future module." },
  { label: "Accounting", path: "/app/accounting", icon: "accounting", description: "Accounting workflows will be introduced in a future module." },
  { label: "Reports", path: "/app/reports", icon: "reports", description: "Report workflows will be introduced in a future module." },
  { label: "Masters / Setup", path: "/app/setup", icon: "setup", description: "Company profile, branches, and warehouses." },
  { label: "Users & Roles", path: "/app/users", icon: "users", description: "Company user, role, and permission administration." },
  { label: "Settings", path: "/app/settings", icon: "settings", description: "Personal and company settings will be introduced in a future module." },
];

export function navigationForPath(path: string): NavigationItem {
  return navigationItems.find((item) => item.path === path) ?? navigationItems[0];
}
