"use client";

import { Send } from "lucide-react";
import { FormEvent, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, buttonClass, Field, inputClass } from "@/components/ui";
import { api } from "@/lib/api";
import type { AnalyzeLeadResponse } from "@/types";

export function AnalyzerClient() {
  const [result, setResult] = useState<AnalyzeLeadResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      const response = await api<AnalyzeLeadResponse>("/ai/analyze-lead", {
        method: "POST",
        body: JSON.stringify({
          name: form.get("name") || null,
          email: form.get("email") || null,
          company: form.get("company") || null,
          message: form.get("message")
        })
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="mb-6">
        <p className="text-sm text-mint">AI operations</p>
        <h1 className="text-3xl font-semibold text-white">Email analyzer</h1>
      </div>
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <form onSubmit={submit} className="space-y-4 rounded-lg border border-line bg-panel p-5">
          <Field label="Lead name"><input name="name" className={inputClass} placeholder="Jordan Lee" /></Field>
          <Field label="Email"><input name="email" type="email" className={inputClass} placeholder="jordan@company.com" /></Field>
          <Field label="Company"><input name="company" className={inputClass} placeholder="Acme Operations" /></Field>
          <Field label="Customer message">
            <textarea
              name="message"
              required
              className={`${inputClass} min-h-64`}
              defaultValue="Hi, we are a company with 45 employees and we are interested in your software. Can you send pricing and maybe schedule a demo next week?"
            />
          </Field>
          {error && <p className="rounded-md border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-100">{error}</p>}
          <button className={buttonClass} disabled={loading}>
            <Send size={16} />
            {loading ? "Analyzing..." : "Run agentic workflow"}
          </button>
        </form>
        <section className="rounded-lg border border-line bg-panel p-5">
          {!result ? (
            <div className="grid h-full min-h-96 place-items-center rounded-md border border-dashed border-line text-center">
              <div>
                <p className="font-semibold text-white">Awaiting customer message</p>
                <p className="mt-2 max-w-md text-sm text-slate-400">The workflow will analyze the lead, update CRM status, save the analysis, create a task, and log activity.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white">Analysis result</h2>
                <div className="rounded-md bg-mint px-3 py-1 text-sm font-semibold text-ink">{result.analysis.lead_score}/100</div>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <Badge tone="good">{result.analysis.sentiment}</Badge>
                <Badge tone="warn">{result.analysis.urgency}</Badge>
                <Badge tone="info">{result.analysis.category}</Badge>
              </div>
              <div className="rounded-md border border-line bg-ink p-4">
                <p className="text-sm text-slate-500">Summary</p>
                <p className="mt-2 text-sm leading-6">{result.analysis.summary}</p>
              </div>
              <div className="rounded-md border border-line bg-ink p-4">
                <p className="text-sm text-slate-500">Recommended action</p>
                <p className="mt-2 text-sm leading-6">{result.analysis.recommended_action}</p>
              </div>
              <div className="rounded-md border border-line bg-ink p-4">
                <p className="text-sm text-slate-500">Suggested reply</p>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{result.analysis.suggested_reply}</p>
              </div>
              <div className="rounded-md border border-line bg-ink p-4">
                <p className="text-sm text-slate-500">Created task</p>
                <p className="mt-2 text-sm leading-6">{result.task.title}</p>
              </div>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
