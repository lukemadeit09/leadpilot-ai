"use client";

import { useCallback } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { AppShell } from "@/components/app-shell";
import { Badge, EmptyState, LoadingRows, MetricCard, PageHeader, Panel } from "@/components/ui";
import { api, statusLabel } from "@/lib/api";
import { useAsyncData } from "@/hooks/use-api";
import type { DashboardMetrics } from "@/types";

export function DashboardClient() {
  const loader = useCallback(() => api<DashboardMetrics>("/dashboard/metrics"), []);
  const { data, loading, error } = useAsyncData(loader);
  const chartData = data ? Object.entries(data.pipeline).map(([name, value]) => ({ name: statusLabel(name), value })) : [];

  return (
    <AppShell>
      <PageHeader
        eyebrow="CRM dashboard"
        title="Revenue operations cockpit"
        description="Monitor lead quality, pipeline movement, task load, and recent AI-driven sales activity from one workspace."
        action={<Badge tone="info">Real-time ready API</Badge>}
      />
      {error && <p className="rounded-md border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-100">{error}</p>}
      {loading || !data ? (
        <LoadingRows />
      ) : (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Total leads" value={data.total_leads} detail="All CRM records" />
            <MetricCard label="Qualified" value={data.qualified_leads} detail="Ready for sales action" />
            <MetricCard label="Average score" value={data.average_score} detail="AI lead quality" />
            <MetricCard label="Pending tasks" value={data.pending_tasks} detail="Open follow-ups" />
          </div>
          <div className="grid gap-5 lg:grid-cols-[1.35fr_0.65fr]">
            <Panel title="Pipeline distribution" description="Current lead count by sales stage">
              <div className="h-80 px-3 py-5">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ left: -16, right: 12, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#22302c" vertical={false} />
                    <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} allowDecimals={false} />
                    <Tooltip cursor={{ fill: "rgba(255,255,255,0.03)" }} contentStyle={{ background: "#0f1614", border: "1px solid #22302c", borderRadius: 8, color: "#fff" }} />
                    <Bar dataKey="value" fill="#36d399" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Panel>
            <Panel title="Recent activity" description="Audit trail across AI and CRM actions" className="overflow-hidden">
              <div className="p-5">
              {data.recent_activity.length === 0 ? (
                <EmptyState title="No activity yet" detail="Analyze a customer message to populate the operational timeline." />
              ) : (
                <div className="space-y-2">
                  {data.recent_activity.map((activity) => (
                    <div key={activity.id} className="rounded-md border border-line/70 bg-ink/70 p-3">
                      <div className="text-xs font-medium uppercase tracking-[0.1em] text-slate-500">{activity.action.replace("_", " ")}</div>
                      <p className="mt-1 text-sm leading-5 text-slate-300">{activity.detail}</p>
                    </div>
                  ))}
                </div>
              )}
              </div>
            </Panel>
          </div>
        </div>
      )}
    </AppShell>
  );
}
