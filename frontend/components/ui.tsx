import clsx from "clsx";
import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  action
}: {
  eyebrow: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-7 flex flex-col gap-4 border-b border-line/70 pb-6 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-steel">{eyebrow}</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-normal text-white md:text-3xl">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">{description}</p>}
      </div>
      {action && <div className="flex shrink-0 items-center gap-2">{action}</div>}
    </div>
  );
}

export function Panel({
  children,
  className,
  title,
  description,
  action
}: {
  children: ReactNode;
  className?: string;
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <section className={clsx("rounded-lg border border-line/80 bg-panel/95 shadow-sm shadow-black/20", className)}>
      {(title || description || action) && (
        <div className="flex flex-col gap-3 border-b border-line/70 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            {title && <h2 className="text-sm font-semibold text-white">{title}</h2>}
            {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "good" | "warn" | "bad" | "info" }) {
  const tones = {
    neutral: "border-line bg-slate-400/5 text-slate-300",
    good: "border-emerald-400/25 bg-emerald-400/10 text-emerald-200",
    warn: "border-amber-300/25 bg-amber-300/10 text-amber-100",
    bad: "border-rose-400/25 bg-rose-400/10 text-rose-100",
    info: "border-steel/40 bg-steel/10 text-sky-100"
  };
  return <span className={clsx("inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-medium capitalize leading-none", tones[tone])}>{children}</span>;
}

export function MetricCard({ label, value, detail }: { label: string; value: string | number; detail: string }) {
  return (
    <div className="rounded-lg border border-line/80 bg-panel/95 p-4 shadow-sm shadow-black/20">
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{label}</p>
      <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
      <p className="mt-1 text-sm text-slate-500">{detail}</p>
    </div>
  );
}

export function Alert({ children, tone = "bad" }: { children: ReactNode; tone?: "bad" | "info" | "good" }) {
  const tones = {
    bad: "border-rose-400/30 bg-rose-400/10 text-rose-100",
    info: "border-steel/30 bg-steel/10 text-sky-100",
    good: "border-emerald-400/30 bg-emerald-400/10 text-emerald-100"
  };
  return <p className={clsx("rounded-md border p-3 text-sm", tones[tone])}>{children}</p>;
}

export function EmptyState({ title, detail, action }: { title: string; detail: string; action?: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-line/90 bg-ink/55 p-8 text-center shadow-inner shadow-black/20">
      <div className="mx-auto mb-4 grid size-10 place-items-center rounded-md border border-line bg-white/[0.03]">
        <div className="size-2 rounded-full bg-mint" />
      </div>
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">{detail}</p>
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  );
}

export function LoadingRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-14 animate-pulse rounded-md border border-line/60 bg-gradient-to-r from-white/[0.025] via-white/[0.055] to-white/[0.025]" />
      ))}
    </div>
  );
}

export function LoadingCards({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="h-32 animate-pulse rounded-lg border border-line/70 bg-gradient-to-br from-white/[0.045] to-transparent" />
      ))}
    </div>
  );
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-medium uppercase tracking-[0.1em] text-slate-500">{label}</span>
      {children}
      {hint && <span className="mt-2 block text-xs text-slate-500">{hint}</span>}
    </label>
  );
}

export const inputClass =
  "w-full rounded-md border border-line/90 bg-[#09110f] px-3 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 hover:border-slate-600 focus:border-mint focus:ring-2 focus:ring-mint/10";

export const buttonClass =
  "inline-flex items-center justify-center gap-2 rounded-md bg-mint px-4 py-2.5 text-sm font-semibold text-ink shadow-sm shadow-mint/10 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60";

export const secondaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-md border border-line bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-slate-600 hover:bg-white/[0.06]";

export const tableHeaderClass = "border-b border-line/80 bg-white/[0.025] text-left text-xs font-medium uppercase tracking-[0.11em] text-slate-500";

export const tableCellClass = "px-4 py-3 align-middle";
