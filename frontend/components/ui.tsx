import clsx from "clsx";
import type { ReactNode } from "react";

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "good" | "warn" | "bad" | "info" }) {
  const tones = {
    neutral: "border-line bg-white/5 text-slate-300",
    good: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200",
    warn: "border-amber-300/30 bg-amber-300/10 text-amber-100",
    bad: "border-rose-400/30 bg-rose-400/10 text-rose-100",
    info: "border-sky-300/30 bg-sky-300/10 text-sky-100"
  };
  return <span className={clsx("inline-flex items-center rounded-md border px-2 py-1 text-xs capitalize", tones[tone])}>{children}</span>;
}

export function MetricCard({ label, value, detail }: { label: string; value: string | number; detail: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel p-5 shadow-glow">
      <p className="text-sm text-slate-400">{label}</p>
      <div className="mt-3 text-3xl font-semibold text-white">{value}</div>
      <p className="mt-2 text-sm text-slate-500">{detail}</p>
    </div>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-white/[0.03] p-8 text-center">
      <h3 className="text-base font-semibold text-white">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">{detail}</p>
    </div>
  );
}

export function LoadingRows() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="h-14 animate-pulse rounded-lg border border-line bg-white/[0.04]" />
      ))}
    </div>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm text-slate-300">{label}</span>
      {children}
    </label>
  );
}

export const inputClass =
  "w-full rounded-md border border-line bg-ink px-3 py-2 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-mint";

export const buttonClass =
  "inline-flex items-center justify-center gap-2 rounded-md bg-mint px-4 py-2 text-sm font-semibold text-ink transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60";
