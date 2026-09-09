import { useEffect, useState } from "react";

import { AppShell } from "./components/AppShell";
import { applicationBrand } from "./config/brand";
import { navigationItems } from "./config/navigation";
import { AuthPage } from "./pages/AuthPage";
import { authApi, type AuthUser } from "./services/auth";

function currentPath() {
  const normalized = window.location.pathname.replace(/\/+$/, "") || "/auth";
  return normalized === "/" ? "/auth" : normalized;
}

export function App() {
  const [path, setPath] = useState(currentPath);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handlePopState = () => setPath(currentPath());
    window.addEventListener("popstate", handlePopState);
    authApi.me().then(({ user: authenticatedUser }) => setUser(authenticatedUser)).catch(() => undefined).finally(() => setLoading(false));
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    document.title = applicationBrand.productName;
  }, []);

  function navigate(destination: string, replace = false) {
    if (currentPath() === destination) return;
    window.history[replace ? "replaceState" : "pushState"]({}, "", destination);
    setPath(destination);
  }

  useEffect(() => {
    if (loading) return;
    if (!user && path.startsWith("/app")) navigate("/auth", true);
    if (user && (path === "/auth" || path === "/")) navigate("/app/dashboard", true);
    if (user && path.startsWith("/app") && !navigationItems.some((item) => item.path === path)) navigate("/app/dashboard", true);
  }, [loading, path, user]);

  async function logout() {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      navigate("/auth", true);
    }
  }

  if (loading) return <main className="app-loading"><span className="loading-mark">EB</span><p>Preparing your workspace...</p></main>;
  if (!user) return <AuthPage onAuthenticated={(authenticatedUser) => { setUser(authenticatedUser); navigate("/app/dashboard", true); }} />;
  return <AppShell user={user} path={path.startsWith("/app") ? path : "/app/dashboard"} navigate={navigate} onLogout={logout} />;
}
