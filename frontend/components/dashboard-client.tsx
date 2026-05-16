"use client";

import { useCallback } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { AppShell } from "@/components/app-shell";
import { Badge, EmptyState, LoadingRows, MetricCard } from "@/components/ui";
import { api, statusLabel } from "@/lib/api";
import { useAsyncData } from "@/hooks/use-api";
import type { DashboardMetrics } from "@/types";

export function DashboardClient() {
  const loader = useCallback(() => api<DashboardMetrics>("/dashboard/metrics"), []);
  const { data, loading, error } = useAsyncData(loader);
  const chartData = data ? Object.entries(data.pipeline).map(([name, value]) => ({ name: statusLabel(name), value })) : [];

  return (
    <AppShell>
      <div className="mb-6 flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <p className="text-sm text-mint">CRM dashboard</p>
          <h1 className="text-3xl font-semibold text-white">Revenue operations cockpit</h1>
        </div>
        <Badge tone="info">Real-time ready API</Badge>
      </div>
      {error && <p className="rounded-md border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-100">{error}</p>}
      {loading || !data ? (
        <LoadingRows />
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <MetricCard label="Total leads" value={data.total_leads} detail="All CRM records" />
            <MetricCard label="Qualified" value={data.qualified_leads} detail="Ready for sales action" />
            <MetricCard label="Average score" value={data.average_score} detail="AI lead quality" />
            <MetricCard label="Pending tasks" value={data.pending_tasks} detail="Open follow-ups" />
          </div>
          <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
            <section className="rounded-lg border border-line bg-panel p-5">
              <h2 className="mb-4 text-lg font-semibold text-white">Pipeline distribution</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid stroke="#24322e" vertical={false} />
                    <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} allowDecimals={false} />
                    <Tooltip contentStyle={{ background: "#101816", border: "1px solid #24322e", color: "#fff" }} />
                    <Bar dataKey="value" fill="#3ddc97" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
            <section className="rounded-lg border border-line bg-panel p-5">
              <h2 className="mb-4 text-lg font-semibold text-white">Recent activity</h2>
              {data.recent_activity.length === 0 ? (
                <EmptyState title="No activity yet" detail="Analyze a customer message to populate the operational timeline." />
              ) : (
                <div className="space-y-3">
                  {data.recent_activity.map((activity) => (
                    <div key={activity.id} className="rounded-md border border-line bg-ink p-3">
                      <div className="text-sm font-medium capitalize text-white">{activity.action.replace("_", " ")}</div>
                      <p className="mt-1 text-sm text-slate-400">{activity.detail}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        </div>
      )}
    </AppShell>
  );
}
