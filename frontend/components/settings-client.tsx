"use client";

import { useCallback } from "react";

import { AppShell } from "@/components/app-shell";
import { Alert, Badge, LoadingRows, PageHeader, Panel } from "@/components/ui";
import { useAsyncData } from "@/hooks/use-api";
import { api } from "@/lib/api";
import type { BillingUsage } from "@/types";

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export function SettingsClient() {
  const loader = useCallback(() => api<BillingUsage>("/billing/usage"), []);
  const { data, loading, error } = useAsyncData(loader);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Workspace"
        title="Settings"
        description="Operational readiness, plan limits, and deployment-sensitive configuration for the LeadPilot AI workspace."
      />
      <div className="space-y-5">
        {error && <Alert>{error}</Alert>}
        <Panel title="AI usage and plan" description="Monthly quota protection for AI workflows">
          <div className="p-5">
            {loading || !data ? (
              <LoadingRows />
            ) : (
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-md border border-line/70 bg-ink/70 p-4">
                  <Badge tone="info">{data.plan_label}</Badge>
                  <p className="mt-3 text-sm text-slate-300">Active pricing plan</p>
                  <p className="mt-1 text-xs text-slate-500">Admin endpoint can change this before Stripe is added.</p>
                </div>
                <div className="rounded-md border border-line/70 bg-ink/70 p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.1em] text-slate-500">Remaining credits</p>
                  <p className="mt-3 text-2xl font-semibold text-white">{currency.format(data.remaining)}</p>
                  <p className="mt-1 text-xs text-slate-500">{currency.format(data.organization_used)} used of {currency.format(data.monthly_limit)}</p>
                </div>
                <div className="rounded-md border border-line/70 bg-ink/70 p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.1em] text-slate-500">Your usage</p>
                  <p className="mt-3 text-2xl font-semibold text-white">{currency.format(data.user_used)}</p>
                  <p className="mt-1 text-xs text-slate-500">{data.requests} org AI requests this month</p>
                </div>
              </div>
            )}
          </div>
        </Panel>
        <Panel title="Deployment readiness" description="Security and runtime checks for local and hosted environments">
          <div className="grid gap-3 p-5 md:grid-cols-3">
            <div className="rounded-md border border-line/70 bg-ink/70 p-4"><Badge tone="good">Configured</Badge><p className="mt-3 text-sm text-slate-300">JWT authentication</p></div>
            <div className="rounded-md border border-line/70 bg-ink/70 p-4"><Badge tone="good">Configured</Badge><p className="mt-3 text-sm text-slate-300">API environment variables</p></div>
            <div className="rounded-md border border-line/70 bg-ink/70 p-4"><Badge tone="info">Optional</Badge><p className="mt-3 text-sm text-slate-300">OpenAI key for live AI calls</p></div>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
