import { FormEvent, useEffect, useState } from "react";

import { authApi, type AuthUser } from "../services/auth";

type View = "email" | "mobile" | "activate" | "verify" | "forgot" | "reset" | "mobileReset";

const inputClass = "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-950 outline-none focus:border-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-white";

export function AuthPage() {
  const [view, setView] = useState<View>("email");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [email, setEmail] = useState("");
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [code, setCode] = useState("");
  const [remember, setRemember] = useState(false);
  const [mobileLoginRequested, setMobileLoginRequested] = useState(false);
  const [mobileVerificationRequested, setMobileVerificationRequested] = useState(false);
  const [mobileResetRequested, setMobileResetRequested] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    authApi.me().then(({ user: currentUser }) => setUser(currentUser)).catch(() => undefined);
  }, []);

  async function submit(action: () => Promise<{ message?: string; user?: AuthUser }>) {
    setError("");
    setMessage("");
    try {
      const result = await action();
      if (result.user) setUser(result.user);
      setMessage(result.message ?? "You are signed in.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Something went wrong.");
    }
  }

  function form(handler: () => Promise<{ message?: string; user?: AuthUser }>) {
    return (event: FormEvent) => {
      event.preventDefault();
      void submit(handler);
    };
  }

  if (user) {
    return <main className="auth-page"><section className="auth-card"><p className="eyebrow">Signed in</p><h1>Welcome, {user.name}</h1><p>You have an active server-side session.</p><button onClick={() => void submit(async () => { const result = await authApi.logout(); setUser(null); return result; })}>Sign out</button></section></main>;
  }

  return <main className="auth-page"><section className="auth-card">
    <header><p className="eyebrow">ERP Builder</p><h1>Sign in</h1><p className="muted">Use your email and password, or your mobile number and a one-time code.</p></header>
    <nav className="auth-tabs" aria-label="Authentication options">
      <button className={view === "email" ? "selected" : ""} onClick={() => setView("email")}>Email</button>
      <button className={view === "mobile" ? "selected" : ""} onClick={() => setView("mobile")}>Mobile OTP</button>
      <button className={view === "activate" ? "selected" : ""} onClick={() => setView("activate")}>Activate</button>
    </nav>
    {view === "email" && <form onSubmit={form(async () => authApi.emailLogin(email, password, remember))}>
      <label>Email<input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} type="email" required /></label>
      <label>Password<input className={inputClass} value={password} onChange={(event) => setPassword(event.target.value)} type="password" minLength={8} required /></label>
      <label className="checkbox"><input checked={remember} onChange={(event) => setRemember(event.target.checked)} type="checkbox" /> Remember me</label>
      <button type="submit">Sign in</button><button className="link" type="button" onClick={() => setView("forgot")}>Forgot password?</button>
    </form>}
    {view === "mobile" && <form onSubmit={form(async () => {
      if (mobileLoginRequested) return authApi.verifyMobileLogin(mobile, code, remember);
      const result = await authApi.requestMobileLogin(mobile);
      setMobileLoginRequested(true);
      return result;
    })}>
      <label>Mobile number<input className={inputClass} value={mobile} onChange={(event) => setMobile(event.target.value)} placeholder="+91..." required /></label>
      {mobileLoginRequested && <label>One-time code<input className={inputClass} value={code} onChange={(event) => setCode(event.target.value)} inputMode="numeric" minLength={6} maxLength={6} required /></label>}
      <label className="checkbox"><input checked={remember} onChange={(event) => setRemember(event.target.checked)} type="checkbox" /> Remember me</label>
      <button type="submit">{mobileLoginRequested ? "Verify and sign in" : "Send code"}</button>
    </form>}
    {view === "activate" && <form onSubmit={form(async () => token ? authApi.completeActivation(token, password) : authApi.requestActivation(email))}>
      {!token && <label>Email<input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} type="email" required /></label>}
      <label>Activation token<input className={inputClass} value={token} onChange={(event) => setToken(event.target.value)} /></label>
      {token && <label>Set password<input className={inputClass} value={password} onChange={(event) => setPassword(event.target.value)} type="password" minLength={8} required /></label>}
      <button type="submit">{token ? "Activate account" : "Request activation"}</button><button className="link" type="button" onClick={() => setView("verify")}>Verify account</button>
    </form>}
    {view === "verify" && <form onSubmit={form(async () => {
      if (token) return authApi.verifyEmail(token);
      if (mobileVerificationRequested) return authApi.verifyMobile(mobile, code);
      const result = await authApi.requestMobileVerification(mobile);
      setMobileVerificationRequested(true);
      return result;
    })}>
      <label>Email verification token<input className={inputClass} value={token} onChange={(event) => setToken(event.target.value)} /></label>
      <label>Mobile number<input className={inputClass} value={mobile} onChange={(event) => setMobile(event.target.value)} /></label>
      {mobileVerificationRequested && <label>Mobile code<input className={inputClass} value={code} onChange={(event) => setCode(event.target.value)} inputMode="numeric" minLength={6} maxLength={6} required /></label>}
      <button type="submit">{token ? "Verify email" : mobileVerificationRequested ? "Verify mobile" : "Send mobile code"}</button>
    </form>}
    {view === "forgot" && <form onSubmit={form(async () => authApi.forgotPassword(email))}>
      <label>Email<input className={inputClass} value={email} onChange={(event) => setEmail(event.target.value)} type="email" required /></label>
      <button type="submit">Send reset instructions</button><button className="link" type="button" onClick={() => setView("reset")}>Have a reset token?</button><button className="link" type="button" onClick={() => setView("mobileReset")}>Reset with mobile OTP</button>
    </form>}
    {view === "reset" && <form onSubmit={form(async () => authApi.resetPassword(token, password))}>
      <label>Reset token<input className={inputClass} value={token} onChange={(event) => setToken(event.target.value)} required /></label>
      <label>New password<input className={inputClass} value={password} onChange={(event) => setPassword(event.target.value)} type="password" minLength={8} required /></label><button type="submit">Reset password</button>
    </form>}
    {view === "mobileReset" && <form onSubmit={form(async () => {
      if (mobileResetRequested) return authApi.resetMobilePassword(mobile, code, password);
      const result = await authApi.requestMobileReset(mobile);
      setMobileResetRequested(true);
      return result;
    })}>
      <label>Mobile number<input className={inputClass} value={mobile} onChange={(event) => setMobile(event.target.value)} placeholder="+91..." required /></label>
      {mobileResetRequested && <><label>One-time code<input className={inputClass} value={code} onChange={(event) => setCode(event.target.value)} inputMode="numeric" minLength={6} maxLength={6} required /></label><label>New password<input className={inputClass} value={password} onChange={(event) => setPassword(event.target.value)} type="password" minLength={8} required /></label></>}
      <button type="submit">{mobileResetRequested ? "Reset password" : "Send code"}</button><button className="link" type="button" onClick={() => setView("forgot")}>Reset with email instead</button>
    </form>}
    {message && <p className="notice success">{message}</p>}{error && <p className="notice error">{error}</p>}
  </section></main>;
}
