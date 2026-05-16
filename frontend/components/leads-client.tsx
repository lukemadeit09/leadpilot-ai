"use client";

import Link from "next/link";
import { FormEvent, useCallback, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, buttonClass, EmptyState, Field, inputClass, LoadingRows } from "@/components/ui";
import { api, statusLabel } from "@/lib/api";
import { useAsyncData } from "@/hooks/use-api";
import type { Lead, LeadStatus } from "@/types";

const statusTone = (status: LeadStatus) => (status === "qualified" || status === "closed_won" ? "good" : status === "closed_lost" ? "bad" : status === "follow_up" ? "warn" : "neutral");

export function LeadsClient() {
  const [query, setQuery] = useState("");
  const loader = useCallback(() => api<Lead[]>(`/leads${query ? `?search=${encodeURIComponent(query)}` : ""}`), [query]);
  const { data, loading, error, reload } = useAsyncData(loader);
  const [creating, setCreating] = useState(false);

  async function createLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreating(true);
    const form = new FormData(event.currentTarget);
    await api<Lead>("/leads", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        email: form.get("email") || null,
        company: form.get("company"),
        message: form.get("message"),
        status: "new"
      })
    });
    event.currentTarget.reset();
    setCreating(false);
    await reload();
  }

  return (
    <AppShell>
      <div className="mb-6">
        <p className="text-sm text-mint">CRM</p>
        <h1 className="text-3xl font-semibold text-white">Leads</h1>
      </div>
      <div className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <form onSubmit={createLead} className="space-y-4 rounded-lg border border-line bg-panel p-5">
          <h2 className="text-lg font-semibold text-white">Create lead</h2>
          <Field label="Name"><input name="name" className={inputClass} /></Field>
          <Field label="Email"><input name="email" type="email" className={inputClass} /></Field>
          <Field label="Company"><input name="company" className={inputClass} /></Field>
          <Field label="Message"><textarea name="message" className={`${inputClass} min-h-28`} required /></Field>
          <button className={buttonClass} disabled={creating}>{creating ? "Creating..." : "Create lead"}</button>
        </form>
        <section className="rounded-lg border border-line bg-panel p-5">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 className="text-lg font-semibold text-white">Pipeline records</h2>
            <input className={`${inputClass} md:max-w-xs`} placeholder="Search leads" value={query} onChange={(event) => setQuery(event.target.value)} />
          </div>
          {error && <p className="text-sm text-rose-200">{error}</p>}
          {loading || !data ? (
            <LoadingRows />
          ) : data.length === 0 ? (
            <EmptyState title="No leads found" detail="Create a lead manually or analyze a customer message to populate the CRM." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-line text-slate-500">
                  <tr>
                    <th className="py-3">Lead</th>
                    <th>Company</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Urgency</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((lead) => (
                    <tr key={lead.id} className="border-b border-line/70">
                      <td className="py-3">
                        <Link href={`/leads/${lead.id}`} className="font-medium text-white hover:text-mint">{lead.name || lead.email || "Unnamed lead"}</Link>
                        <div className="text-xs text-slate-500">{lead.email}</div>
                      </td>
                      <td className="text-slate-300">{lead.company || "Unknown"}</td>
                      <td><Badge tone={statusTone(lead.status)}>{statusLabel(lead.status)}</Badge></td>
                      <td className="font-semibold text-white">{lead.score}</td>
                      <td className="capitalize text-slate-300">{lead.urgency || "not set"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
