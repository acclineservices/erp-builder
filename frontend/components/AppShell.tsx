import { useEffect, useState, type ReactNode } from "react";

import { applicationBrand, supportedLanguages, type LanguageCode, type ThemeMode } from "../config/brand";
import { navigationForPath, navigationItems, type NavigationItem } from "../config/navigation";
import { authApi, type AccessibleCompany, type AuthUser } from "../services/auth";
import { OrganizationPage } from "../pages/OrganizationPage";

type AppShellProps = {
  user: AuthUser;
  path: string;
  navigate: (path: string, replace?: boolean) => void;
  onLogout: () => Promise<void>;
};

type IconName = NavigationItem["icon"] | "menu" | "search" | "bell" | "bolt" | "chevron" | "help" | "logout" | "assistant";

const iconLabels: Record<IconName, string> = {
  home: "⌂", sales: "↗", purchases: "↓", inventory: "□", accounting: "#", reports: "▥", setup: "◇", users: "♙", settings: "⚙",
  menu: "☰", search: "⌕", bell: "◌", bolt: "+", chevron: "⌄", help: "?", logout: "→", assistant: "✦",
};

export function Icon({ name }: { name: IconName }) {
  return <span aria-hidden="true" className={"icon icon-" + name}>{iconLabels[name]}</span>;
}

function storedValue(key: string, fallback: string): string {
  return window.localStorage.getItem(key) ?? fallback;
}

export function AppShell({ user, path, navigate, onLogout }: AppShellProps) {
  const [collapsed, setCollapsed] = useState(() => storedValue("erp-shell-collapsed", "false") === "true");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>(() => storedValue("erp-theme", "system") as ThemeMode);
  const [language, setLanguage] = useState<LanguageCode>(() => storedValue("erp-language", "en") as LanguageCode);
  const [companies, setCompanies] = useState<AccessibleCompany[]>([]);
  const [companiesLoading, setCompaniesLoading] = useState(true);
  const [companiesError, setCompaniesError] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState("");
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => { window.localStorage.setItem("erp-shell-collapsed", String(collapsed)); }, [collapsed]);
  useEffect(() => { window.localStorage.setItem("erp-theme", theme); document.documentElement.dataset.theme = theme; }, [theme]);
  useEffect(() => { window.localStorage.setItem("erp-language", language); document.documentElement.lang = language; }, [language]);
  useEffect(() => {
    let mounted = true;
    authApi.companies().then((available) => {
      if (!mounted) return;
      setCompanies(available);
      const storedCompany = window.localStorage.getItem("erp-last-company-" + user.id);
      setSelectedCompanyId(available.some((company) => company.id === storedCompany) ? storedCompany ?? "" : available[0]?.id ?? "");
    }).catch(() => mounted && setCompaniesError(true)).finally(() => mounted && setCompaniesLoading(false));
    return () => { mounted = false; };
  }, [user.id]);
  useEffect(() => { if (selectedCompanyId) window.localStorage.setItem("erp-last-company-" + user.id, selectedCompanyId); }, [selectedCompanyId, user.id]);
  useEffect(() => {
    const openSearch = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setShowSearch(true);
      }
    };
    window.addEventListener("keydown", openSearch);
    return () => window.removeEventListener("keydown", openSearch);
  }, []);

  const company = companies.find((item) => item.id === selectedCompanyId);
  const item = navigationForPath(path);
  const go = (destination: string) => { setMobileOpen(false); navigate(destination); };

  return <div className={"app-shell " + (collapsed ? "sidebar-collapsed" : "")}>
    <Sidebar collapsed={collapsed} mobileOpen={mobileOpen} currentPath={item.path} onNavigate={go} onCollapse={() => setCollapsed((value) => !value)} />
    {mobileOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    <section className="shell-content">
      <Header user={user} company={company} companies={companies} loading={companiesLoading} failed={companiesError} selectedCompanyId={selectedCompanyId} theme={theme} language={language} onMobileMenu={() => setMobileOpen(true)} onSelectCompany={setSelectedCompanyId} onThemeChange={setTheme} onLanguageChange={setLanguage} onSearch={() => setShowSearch(true)} onNavigate={go} onLogout={onLogout} />
      <main className="workspace"><Breadcrumbs current={item.label} onNavigate={go} />{item.path === "/app/dashboard" ? <Dashboard user={user} company={company} loading={companiesLoading} /> : item.path === "/app/setup" ? <OrganizationPage key={selectedCompanyId} company={company} /> : <PlaceholderPage item={item} company={company} />}</main>
    </section>
    {showSearch && <SearchDialog onClose={() => setShowSearch(false)} onNavigate={go} />}
  </div>;
}

export function Sidebar({ collapsed, mobileOpen, currentPath, onNavigate, onCollapse }: { collapsed: boolean; mobileOpen: boolean; currentPath: string; onNavigate: (path: string) => void; onCollapse: () => void }) {
  return <aside className={"sidebar " + (mobileOpen ? "sidebar-mobile-open" : "")} aria-label="Primary navigation">
    <div className="sidebar-brand"><div className="brand-mark">{applicationBrand.shortName}</div><span className="brand-name">{applicationBrand.productName}</span><button className="icon-button sidebar-collapse" aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} onClick={onCollapse}><Icon name="menu" /></button></div>
    <nav className="sidebar-nav">{navigationItems.map((item) => <button key={item.path} className={"nav-item " + (currentPath === item.path ? "nav-item-active" : "")} onClick={() => onNavigate(item.path)} title={collapsed ? item.label : undefined}><Icon name={item.icon} /><span>{item.label}</span></button>)}</nav>
    <div className="sidebar-footer"><button className="nav-item assistant-placeholder" disabled title="AI assistant is planned for a future release"><span className="assistant-text">AI</span><span>{applicationBrand.assistantLabel}</span></button><p>Application shell foundation</p></div>
  </aside>;
}

export function Header(props: {
  user: AuthUser; company?: AccessibleCompany; companies: AccessibleCompany[]; loading: boolean; failed: boolean; selectedCompanyId: string; theme: ThemeMode; language: LanguageCode;
  onMobileMenu: () => void; onSelectCompany: (id: string) => void; onThemeChange: (theme: ThemeMode) => void; onLanguageChange: (language: LanguageCode) => void; onSearch: () => void; onNavigate: (path: string) => void; onLogout: () => Promise<void>;
}) {
  const [quickOpen, setQuickOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const initials = props.user.name.split(" ").map((name) => name[0]).join("").slice(0, 2).toUpperCase();
  return <header className="topbar">
    <button className="icon-button mobile-menu-button" aria-label="Open navigation" onClick={props.onMobileMenu}><Icon name="menu" /></button>
    <CompanySwitcher company={props.company} companies={props.companies} loading={props.loading} failed={props.failed} selectedCompanyId={props.selectedCompanyId} onSelectCompany={props.onSelectCompany} />
    <div className="topbar-actions">
      <button className="search-trigger" onClick={props.onSearch}><Icon name="search" /><span>Search</span><kbd>Ctrl K</kbd></button>
      <div className="menu-anchor"><button className="icon-button" aria-label="Quick actions" onClick={() => { setQuickOpen((value) => !value); setNotificationsOpen(false); setProfileOpen(false); }}><Icon name="bolt" /></button>{quickOpen && <div className="popover quick-actions"><p className="popover-title">Quick actions</p><button disabled>New sale <small>Coming soon</small></button><button disabled>Add customer <small>Coming soon</small></button><button onClick={() => props.onNavigate("/app/setup")}>Open setup</button></div>}</div>
      <div className="menu-anchor"><button className="icon-button notification-button" aria-label="Notifications" onClick={() => { setNotificationsOpen((value) => !value); setQuickOpen(false); setProfileOpen(false); }}><Icon name="bell" /></button>{notificationsOpen && <div className="popover notifications"><p className="popover-title">Notifications</p><p>There are no operational notifications yet.</p><small>This entry point is ready for future alerts.</small></div>}</div>
      <UserMenu user={props.user} initials={initials} open={profileOpen} theme={props.theme} language={props.language} onToggle={() => { setProfileOpen((value) => !value); setQuickOpen(false); setNotificationsOpen(false); }} onThemeChange={props.onThemeChange} onLanguageChange={props.onLanguageChange} onNavigate={props.onNavigate} onLogout={props.onLogout} />
    </div>
  </header>;
}

export function CompanySwitcher({ company, companies, loading, failed, selectedCompanyId, onSelectCompany }: { company?: AccessibleCompany; companies: AccessibleCompany[]; loading: boolean; failed: boolean; selectedCompanyId: string; onSelectCompany: (id: string) => void }) {
  if (loading) return <div className="company-switcher loading-context">Loading workspace...</div>;
  if (failed) return <div className="company-switcher context-error">Company context unavailable</div>;
  if (!companies.length) return <div className="company-switcher context-error">No company access</div>;
  if (companies.length === 1) return <div className="company-switcher single-company"><span>{applicationBrand.productName}</span><strong>{company?.business_name}</strong></div>;
  return <label className="company-switcher"><span>{applicationBrand.productName}</span><select aria-label="Switch company" value={selectedCompanyId} onChange={(event) => onSelectCompany(event.target.value)}>{companies.map((item) => <option key={item.id} value={item.id}>{item.business_name}</option>)}</select></label>;
}

export function UserMenu({ user, initials, open, theme, language, onToggle, onThemeChange, onLanguageChange, onNavigate, onLogout }: {
  user: AuthUser; initials: string; open: boolean; theme: ThemeMode; language: LanguageCode; onToggle: () => void; onThemeChange: (theme: ThemeMode) => void; onLanguageChange: (language: LanguageCode) => void; onNavigate: (path: string) => void; onLogout: () => Promise<void>;
}) {
  const [loggingOut, setLoggingOut] = useState(false);
  async function logout() { setLoggingOut(true); await onLogout(); }
  return <div className="menu-anchor user-menu"><button className="profile-button" aria-label="Open user menu" onClick={onToggle}><span className="avatar">{initials}</span><span className="profile-name">{user.name}</span><Icon name="chevron" /></button>
    {open && <div className="popover profile-popover"><div className="profile-summary"><span className="avatar">{initials}</span><div><strong>{user.name}</strong><small>{user.email ?? user.mobile_number}</small></div></div><button onClick={() => onNavigate("/app/settings")}><Icon name="settings" />Settings</button><button onClick={() => window.alert("Support is not configured yet.")}><Icon name="help" />{applicationBrand.supportLabel}</button><label className="preference-row"><span>Theme</span><select value={theme} onChange={(event) => onThemeChange(event.target.value as ThemeMode)}><option value="light">Light</option><option value="dark">Dark</option><option value="system">System default</option></select></label><label className="preference-row"><span>Language</span><select value={language} onChange={(event) => onLanguageChange(event.target.value as LanguageCode)}>{supportedLanguages.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label><button className="logout-button" disabled={loggingOut} onClick={() => void logout()}><Icon name="logout" />{loggingOut ? "Signing out..." : "Sign out"}</button></div>}
  </div>;
}

export function Breadcrumbs({ current, onNavigate }: { current: string; onNavigate: (path: string) => void }) {
  return <nav className="breadcrumbs" aria-label="Breadcrumb"><button onClick={() => onNavigate("/app/dashboard")}>Workspace</button><span>/</span><strong>{current}</strong></nav>;
}

function Dashboard({ user, company, loading }: { user: AuthUser; company?: AccessibleCompany; loading: boolean }) {
  const role = user.is_platform_admin ? "Platform administrator" : "Team member";
  return <div className="page-stack"><section className="welcome-panel"><div><p className="section-kicker">Dashboard</p><h1>Good to see you, {user.name.split(" ")[0]}.</h1><p>{loading ? "Preparing your authorized workspace..." : company ? "You are working in " + company.business_name + "." : "Choose or request access to a company workspace."}</p></div><span className="role-badge">{role}</span></section><section className="foundation-notice"><Icon name="bolt" /><div><strong>Foundation dashboard</strong><p>This space is ready for future operational data. No financial or transactional figures are shown here.</p></div></section><div className="dashboard-grid"><DashboardCard title="Workspace status" eyebrow="Company context"><p>{company ? company.business_name + " is selected for this browser." : "No company is selected."}</p><small>Last-used selection is stored locally and always checked against your authorized company list.</small></DashboardCard><DashboardCard title="Getting started" eyebrow="Suggested next steps"><ul><li>Review your company context</li><li>Set personal preferences</li><li>Preview planned areas</li></ul></DashboardCard><DashboardCard title="Activity space" eyebrow="Coming later"><p>Tasks, approvals, and operational notifications will appear here with future modules.</p><small>There is no fabricated activity data.</small></DashboardCard></div></div>;
}

function DashboardCard({ title, eyebrow, children }: { title: string; eyebrow: string; children: ReactNode }) {
  return <section className="dashboard-card"><p className="section-kicker">{eyebrow}</p><h2>{title}</h2>{children}</section>;
}

function PlaceholderPage({ item, company }: { item: NavigationItem; company?: AccessibleCompany }) {
  return <div className="page-stack"><section className="placeholder-page"><p className="section-kicker">Planned area</p><h1>{item.label}</h1><p>{item.description}</p><div className="placeholder-divider" /><strong>No business functionality has been implemented in this area.</strong><p className="muted-copy">{company ? "When introduced, this module will use the active " + company.business_name + " context." : "Future modules will require an authorized company context."}</p></section></div>;
}

function SearchDialog({ onClose, onNavigate }: { onClose: () => void; onNavigate: (path: string) => void }) {
  const [query, setQuery] = useState("");
  const results = navigationItems.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()));
  return <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}><section className="search-dialog" role="dialog" aria-modal="true" aria-label="Global search" onMouseDown={(event) => event.stopPropagation()}><div className="search-input-wrap"><Icon name="search" /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search navigation and future records" /><button onClick={onClose}>Esc</button></div><p className="search-hint">Navigation is available now. Record search will be added with future modules.</p>{results.map((item) => <button key={item.path} className="search-result" onClick={() => { onNavigate(item.path); onClose(); }}><Icon name={item.icon} /><span>{item.label}</span><small>{item.description}</small></button>)}</section></div>;
}
