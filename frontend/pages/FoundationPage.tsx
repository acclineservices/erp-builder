import { useEffect, useState } from "react";

import { checkBackendHealth, type BackendHealthState } from "../services/health";

const stateCopy: Record<BackendHealthState, { label: string; detail: string }> = {
  checking: { label: "Checking connection", detail: "Connecting to the ERP Builder API." },
  available: { label: "Backend connected", detail: "The ERP Builder API is available." },
  unavailable: { label: "Backend unavailable", detail: "Start the backend to enable API connectivity." },
};

export function FoundationPage() {
  const [backendState, setBackendState] = useState<BackendHealthState>("checking");

  useEffect(() => {
    const controller = new AbortController();

    checkBackendHealth(controller.signal)
      .then(() => setBackendState("available"))
      .catch(() => {
        if (!controller.signal.aborted) {
          setBackendState("unavailable");
        }
      });

    return () => controller.abort();
  }, []);

  const status = stateCopy[backendState];

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8 text-slate-950 dark:bg-slate-950 dark:text-slate-50 sm:px-10 lg:px-16">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl flex-col">
        <header className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-blue-700 font-semibold text-white shadow-sm">EB</div>
          <span className="text-lg font-semibold tracking-tight">ERP Builder</span>
        </header>

        <section className="flex flex-1 items-center py-16 sm:py-24">
          <div className="grid w-full gap-10 lg:grid-cols-[1fr_22rem] lg:items-end">
            <div>
              <p className="mb-4 text-sm font-semibold uppercase tracking-[0.16em] text-blue-700 dark:text-blue-400">Business Management Platform</p>
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">A clearer foundation for everyday business operations.</h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-300">
                ERP Builder is being prepared to bring the confidence of familiar ERP workflows into a focused, modern SaaS experience.
              </p>
            </div>

            <aside aria-live="polite" className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center gap-3">
                <span aria-hidden="true" className={`size-2.5 rounded-full ${backendState === "available" ? "bg-emerald-500" : backendState === "unavailable" ? "bg-amber-500" : "bg-slate-400"}`} />
                <p className="font-medium">{status.label}</p>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{status.detail}</p>
            </aside>
          </div>
        </section>

        <footer className="text-sm text-slate-500 dark:text-slate-400">Application foundation</footer>
      </div>
    </main>
  );
}
