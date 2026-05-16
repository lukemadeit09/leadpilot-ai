"use client";

import { BarChart3, Bot, BriefcaseBusiness, Database, Home, LogOut, Menu, Settings, SquareCheckBig, Users } from "lucide-react";
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
      <aside className={`fixed inset-y-0 left-0 z-40 w-72 border-r border-line bg-[#0b1412] transition md:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex h-16 items-center gap-3 border-b border-line px-5">
          <div className="grid size-9 place-items-center rounded-md bg-mint text-ink">
            <BriefcaseBusiness size={18} />
          </div>
          <div>
            <div className="font-semibold text-white">LeadPilot AI</div>
            <div className="text-xs text-slate-500">Revenue operations cockpit</div>
          </div>
        </div>
        <nav className="space-y-1 p-3">
          {items.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition ${active ? "bg-white text-ink" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}
                onClick={() => setOpen(false)}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-4 left-3 right-3">
          <button onClick={logout} className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white">
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>

      <div className="md:pl-72">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-line bg-ink/90 px-4 backdrop-blur md:px-8">
          <button className="rounded-md border border-line p-2 md:hidden" onClick={() => setOpen(true)} aria-label="Open navigation">
            <Menu size={18} />
          </button>
          <div className="hidden items-center gap-2 text-sm text-slate-500 md:flex">
            <BarChart3 size={16} />
            Live CRM workspace
          </div>
          <div className="rounded-md border border-line px-3 py-1.5 text-xs text-slate-400">JWT protected</div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}
