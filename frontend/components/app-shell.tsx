"use client";

import { BarChart3, Bot, BriefcaseBusiness, Database, Home, LogOut, Menu, Plug, Settings, SquareCheckBig, Users, X } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { clearToken, getToken } from "@/lib/api";

const items = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/leads", label: "Leads", icon: Users },
  { href: "/analyzer", label: "AI Analyzer", icon: Bot },
  { href: "/tasks", label: "Tasks", icon: SquareCheckBig },
  { href: "/knowledge", label: "Knowledge", icon: Database },
  { href: "/integrations", label: "Integrations", icon: Plug },
  { href: "/settings", label: "Settings", icon: Settings }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!getToken()) router.push("/login");
  }, [router]);

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-ink text-slate-100">
      {open && <button aria-label="Close navigation overlay" className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm md:hidden" onClick={() => setOpen(false)} />}
      <aside className={`fixed inset-y-0 left-0 z-40 w-[18rem] border-r border-line/80 bg-[#0a100f]/98 shadow-2xl shadow-black/30 transition md:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex h-16 items-center justify-between border-b border-line/80 px-4">
          <div className="flex items-center gap-3">
          <div className="grid size-9 place-items-center rounded-md border border-mint/30 bg-mint/15 text-mint">
            <BriefcaseBusiness size={18} />
          </div>
          <div>
            <div className="font-semibold text-white">LeadPilot AI</div>
            <div className="text-xs text-slate-500">Revenue operations cockpit</div>
          </div>
          </div>
          <button className="rounded-md border border-line p-2 text-slate-400 md:hidden" onClick={() => setOpen(false)} aria-label="Close navigation">
            <X size={16} />
          </button>
        </div>
        <nav className="space-y-1 p-3">
          {items.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition ${active ? "border border-mint/25 bg-mint/10 text-mint" : "border border-transparent text-slate-400 hover:border-line hover:bg-white/[0.035] hover:text-slate-100"}`}
                onClick={() => setOpen(false)}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-4 left-3 right-3 space-y-3">
          <div className="rounded-lg border border-line/80 bg-white/[0.025] p-3">
            <div className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Workspace</div>
            <div className="mt-2 text-sm text-slate-200">Sales operations</div>
          </div>
          <button onClick={logout} className="flex w-full items-center gap-3 rounded-md border border-transparent px-3 py-2.5 text-sm text-slate-400 transition hover:border-line hover:bg-white/[0.035] hover:text-white">
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>

      <div className="md:pl-[18rem]">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line/70 bg-ink/86 px-4 backdrop-blur-xl md:px-8">
          <button className="rounded-md border border-line p-2 text-slate-300 md:hidden" onClick={() => setOpen(true)} aria-label="Open navigation">
            <Menu size={18} />
          </button>
          <div className="hidden items-center gap-2 text-sm text-slate-500 md:flex">
            <BarChart3 size={16} />
            Live CRM workspace
          </div>
          <div className="rounded-md border border-line/80 bg-white/[0.025] px-3 py-1.5 text-xs text-slate-400">JWT protected</div>
        </header>
        <main className="mx-auto max-w-[1440px] px-4 py-7 md:px-8">{children}</main>
      </div>
    </div>
  );
}
