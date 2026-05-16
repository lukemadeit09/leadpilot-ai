"use client";

import { Send } from "lucide-react";
import { FormEvent, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, buttonClass, EmptyState, Field, inputClass, PageHeader, Panel } from "@/components/ui";
import { api } from "@/lib/api";
import type { AIJob, AnalyzeLeadResponse } from "@/types";

const pollDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function AnalyzerClient() {
  const [result, setResult] = useState<AnalyzeLeadResponse | null>(null);
  const [job, setJob] = useState<AIJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true);
    setError("");
    setResult(null);
    setJob(null);
    try {
      const created = await api<AIJob>("/ai/analyze-lead/jobs", {
        method: "POST",
        body: JSON.stringify({
          name: form.get("name") || null,
          email: form.get("email") || null,
          company: form.get("company") || null,
          message: form.get("message")
        })
      });
      setJob(created);
      let current = created;
      for (let attempt = 0; attempt < 30 && current.status !== "succeeded" && current.status !== "failed"; attempt += 1) {
        await pollDelay(1500);
        current = await api<AIJob>(`/ai/jobs/${created.id}`);
        setJob(current);
      }
      if (current.status === "succeeded" && current.result_payload) {
        setResult(current.result_payload);
        return;
      }
      if (current.status === "failed") {
        throw new Error(current.error_message || "Analysis job failed");
      }
      throw new Error("Analysis is still running. Check the dashboard shortly.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="AI operations"
        title="Email analyzer"
        description="Submit an inbound customer message and let the agent workflow update the CRM, draft a reply, create a task, and log activity."
      />
      <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
        <form onSubmit={submit} className="space-y-4 rounded-lg border border-line/80 bg-panel/95 p-5 shadow-sm shadow-black/20">
          <div>
            <h2 className="text-sm font-semibold text-white">Inbound message</h2>
            <p className="mt-1 text-sm text-slate-500">Capture context before running the agent workflow.</p>
          </div>
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
          {job && !result && !error && (
            <p className="rounded-md border border-steel/30 bg-steel/10 p-3 text-sm text-sky-100">
              Job {job.status}. Attempt {job.attempts || 1} of {job.max_attempts}.
            </p>
          )}
          <button className={`${buttonClass} w-full`} disabled={loading}>
            <Send size={16} />
            {loading ? "Queued in worker..." : "Run agentic workflow"}
          </button>
        </form>
        <Panel title="Workflow output" description="Validated AI analysis and CRM side effects">
          <div className="p-5">
          {!result ? (
            <EmptyState title="Awaiting customer message" detail="The workflow will analyze the lead, update CRM status, save the analysis, create a task, and log activity." />
          ) : (
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Analysis result</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">{result.lead.company || result.lead.name || "Analyzed lead"}</h2>
                </div>
                <div className="rounded-md border border-mint/30 bg-mint/15 px-3 py-1.5 text-sm font-semibold text-mint">{result.analysis.lead_score}/100</div>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <Badge tone="good">{result.analysis.sentiment}</Badge>
                <Badge tone="warn">{result.analysis.urgency}</Badge>
                <Badge tone="info">{result.analysis.category}</Badge>
              </div>
              <div className="rounded-md border border-line/70 bg-ink/70 p-4">
                <p className="text-sm text-slate-500">Summary</p>
                <p className="mt-2 text-sm leading-6">{result.analysis.summary}</p>
              </div>
              <div className="rounded-md border border-line/70 bg-ink/70 p-4">
                <p className="text-sm text-slate-500">Recommended action</p>
                <p className="mt-2 text-sm leading-6">{result.analysis.recommended_action}</p>
              </div>
              <div className="rounded-md border border-line/70 bg-ink/70 p-4">
                <p className="text-sm text-slate-500">Suggested reply</p>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{result.analysis.suggested_reply}</p>
              </div>
              <div className="rounded-md border border-line/70 bg-ink/70 p-4">
                <p className="text-sm text-slate-500">Created task</p>
                <p className="mt-2 text-sm leading-6">{result.task.title}</p>
              </div>
            </div>
          )}
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
