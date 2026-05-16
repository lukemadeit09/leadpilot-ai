"use client";

import { useCallback } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, LoadingRows } from "@/components/ui";
import { api, statusLabel } from "@/lib/api";
import { useAsyncData } from "@/hooks/use-api";
import type { Lead } from "@/types";

export function LeadDetailClient({ id }: { id: string }) {
  const loader = useCallback(() => api<Lead>(`/leads/${id}`), [id]);
  const { data, loading, error } = useAsyncData(loader);
  return (
    <AppShell>
      {loading || !data ? (
        <LoadingRows />
      ) : error ? (
        <p className="text-rose-200">{error}</p>
      ) : (
        <div className="space-y-6">
          <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
            <div>
              <p className="text-sm text-mint">Lead detail</p>
              <h1 className="text-3xl font-semibold text-white">{data.name || data.company || "Lead"}</h1>
              <p className="mt-2 text-slate-400">{data.email || "No email captured"}</p>
            </div>
            <Badge tone="info">{statusLabel(data.status)}</Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-lg border border-line bg-panel p-5"><p className="text-sm text-slate-400">Score</p><p className="mt-3 text-3xl font-semibold">{data.score}</p></div>
            <div className="rounded-lg border border-line bg-panel p-5"><p className="text-sm text-slate-400">Sentiment</p><p className="mt-3 text-xl capitalize">{data.sentiment || "not set"}</p></div>
            <div className="rounded-lg border border-line bg-panel p-5"><p className="text-sm text-slate-400">Urgency</p><p className="mt-3 text-xl capitalize">{data.urgency || "not set"}</p></div>
            <div className="rounded-lg border border-line bg-panel p-5"><p className="text-sm text-slate-400">Company</p><p className="mt-3 text-xl">{data.company || "Unknown"}</p></div>
          </div>
          <section className="rounded-lg border border-line bg-panel p-5">
            <h2 className="mb-3 text-lg font-semibold">Original message</h2>
            <p className="whitespace-pre-wrap text-sm leading-6 text-slate-300">{data.message}</p>
          </section>
        </div>
      )}
    </AppShell>
  );
}
