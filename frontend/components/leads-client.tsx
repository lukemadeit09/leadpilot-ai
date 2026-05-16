"use client";

import Link from "next/link";
import { Plus, Search } from "lucide-react";
import { FormEvent, useCallback, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Alert, Badge, buttonClass, EmptyState, Field, inputClass, LoadingRows, PageHeader, Panel, secondaryButtonClass, tableCellClass, tableHeaderClass } from "@/components/ui";
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
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setCreating(true);
    try {
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
      formElement.reset();
      await reload();
    } finally {
      setCreating(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="CRM"
        title="Leads"
        description="Create, qualify, search, and inspect inbound opportunities as they move through the AI-assisted pipeline."
      />
      <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <form onSubmit={createLead} className="space-y-4 rounded-lg border border-line/80 bg-panel/95 p-5 shadow-sm shadow-black/20">
          <div>
            <h2 className="text-sm font-semibold text-white">Create lead</h2>
            <p className="mt-1 text-sm text-slate-500">Add a lead manually before analysis.</p>
          </div>
          <Field label="Name"><input name="name" className={inputClass} /></Field>
          <Field label="Email"><input name="email" type="email" className={inputClass} /></Field>
          <Field label="Company"><input name="company" className={inputClass} /></Field>
          <Field label="Message"><textarea name="message" className={`${inputClass} min-h-28`} required /></Field>
          <button className={`${buttonClass} w-full`} disabled={creating}>
            <Plus size={16} />
            {creating ? "Creating..." : "Create lead"}
          </button>
        </form>
        <Panel
          title="Pipeline records"
          description="Sorted by most recent activity"
          action={
            <div className="relative w-full sm:w-80">
              <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" size={16} />
              <input className={`${inputClass} pl-9`} placeholder="Search name, company, email" value={query} onChange={(event) => setQuery(event.target.value)} />
            </div>
          }
        >
          <div className="p-5">
          {error && <Alert>{error}</Alert>}
          {loading || !data ? (
            <LoadingRows />
          ) : data.length === 0 ? (
            <EmptyState
              title={query ? "No matching leads" : "No leads yet"}
              detail={query ? "Try a broader search or clear the filter to view all pipeline records." : "Create a lead manually or run the AI analyzer sample to populate the CRM."}
              action={!query && <Link className={secondaryButtonClass} href="/analyzer">Run sample analysis</Link>}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className={tableHeaderClass}>
                  <tr>
                    <th className={tableCellClass}>Lead</th>
                    <th className={tableCellClass}>Company</th>
                    <th className={tableCellClass}>Status</th>
                    <th className={tableCellClass}>Score</th>
                    <th className={tableCellClass}>Urgency</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((lead) => (
                    <tr key={lead.id} className="border-b border-line/60 transition hover:bg-white/[0.025]">
                      <td className={tableCellClass}>
                        <Link href={`/leads/${lead.id}`} className="font-medium text-white hover:text-mint">{lead.name || lead.email || "Unnamed lead"}</Link>
                        <div className="text-xs text-slate-500">{lead.email}</div>
                      </td>
                      <td className={`${tableCellClass} text-slate-300`}>{lead.company || "Unknown"}</td>
                      <td className={tableCellClass}><Badge tone={statusTone(lead.status)}>{statusLabel(lead.status)}</Badge></td>
                      <td className={`${tableCellClass} font-semibold text-white`}>{lead.score}</td>
                      <td className={`${tableCellClass} capitalize text-slate-300`}>{lead.urgency || "not set"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
