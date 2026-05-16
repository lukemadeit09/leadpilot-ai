"use client";

import { Upload } from "lucide-react";
import { FormEvent, useCallback, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { buttonClass, EmptyState, Field, inputClass, LoadingRows, PageHeader, Panel } from "@/components/ui";
import { api } from "@/lib/api";
import { useAsyncData } from "@/hooks/use-api";
import type { KnowledgeDocument } from "@/types";

export function KnowledgeClient() {
  const loader = useCallback(() => api<KnowledgeDocument[]>("/knowledge/documents"), []);
  const { data, loading, reload } = useAsyncData(loader);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = new FormData(event.currentTarget);
    setBusy(true);
    await api<KnowledgeDocument>("/knowledge/upload", { method: "POST", body: file });
    event.currentTarget.reset();
    setBusy(false);
    await reload();
  }

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    const response = await api<{ answer: string; sources: string[] }>("/knowledge/ask", {
      method: "POST",
      body: JSON.stringify({ question: form.get("question") })
    });
    setAnswer(`${response.answer}${response.sources.length ? `\n\nSources: ${response.sources.join(", ")}` : ""}`);
    setBusy(false);
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="RAG knowledge base"
        title="Company knowledge"
        description="Upload sales enablement documents and answer customer questions with grounded company context."
      />
      <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
        <section className="space-y-5 rounded-lg border border-line/80 bg-panel/95 p-5 shadow-sm shadow-black/20">
          <form onSubmit={upload} className="space-y-4">
            <div>
              <h2 className="text-sm font-semibold">Upload document</h2>
              <p className="mt-1 text-sm text-slate-500">PDF, text, and markdown files are supported.</p>
            </div>
            <input name="file" type="file" accept=".pdf,.txt,.md" required className="w-full rounded-md border border-line/90 bg-[#09110f] p-3 text-sm text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-white/[0.06] file:px-3 file:py-2 file:text-sm file:text-slate-200" />
            <button className={`${buttonClass} w-full`} disabled={busy}><Upload size={16} />Upload</button>
          </form>
          <div>
            <h2 className="mb-3 text-sm font-semibold">Documents</h2>
            {loading || !data ? <LoadingRows /> : data.length === 0 ? <EmptyState title="No documents" detail="Upload pricing, product, FAQ, or onboarding documents." /> : (
              <div className="space-y-2">
                {data.map((doc) => <div key={doc.id} className="rounded-md border border-line/70 bg-ink/70 p-3 text-sm text-slate-200">{doc.filename}</div>)}
              </div>
            )}
          </div>
        </section>
        <Panel title="Ask knowledge base" description="Responses use uploaded company context when available">
          <div className="p-5">
          <form onSubmit={ask} className="space-y-4">
            <Field label="Ask about company knowledge">
              <input name="question" className={inputClass} placeholder="What should I tell customers asking about pricing?" required />
            </Field>
            <button className={buttonClass} disabled={busy}>{busy ? "Working..." : "Ask knowledge base"}</button>
          </form>
          <div className="mt-6 rounded-md border border-line/70 bg-ink/70 p-4">
            <p className="text-sm text-slate-500">Answer</p>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-200">{answer || "Answers will appear here after you upload documents and ask a question."}</p>
          </div>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
