"use client";

import { useCallback } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, LoadingRows, MetricCard, PageHeader, Panel } from "@/components/ui";
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
          <PageHeader
            eyebrow="Lead detail"
            title={data.name || data.company || "Lead"}
            description={data.email || "No email captured"}
            action={<Badge tone="info">{statusLabel(data.status)}</Badge>}
          />
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Score" value={data.score} detail="AI quality score" />
            <MetricCard label="Sentiment" value={data.sentiment || "Not set"} detail="Customer tone" />
            <MetricCard label="Urgency" value={data.urgency || "Not set"} detail="Response priority" />
            <MetricCard label="Company" value={data.company || "Unknown"} detail="Account context" />
          </div>
          <Panel title="Original message" description="Inbound customer context">
            <div className="p-5">
              <p className="whitespace-pre-wrap rounded-md border border-line/70 bg-ink/70 p-4 text-sm leading-6 text-slate-300">{data.message}</p>
            </div>
          </Panel>
        </div>
      )}
    </AppShell>
  );
}
