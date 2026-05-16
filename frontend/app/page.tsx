import { ArrowRight, Bot, CheckCircle2, Database, LineChart, LockKeyhole, Plug, Sparkles, SquareCheckBig } from "lucide-react";
import Link from "next/link";

const stats = [
  ["85", "lead score"],
  ["4", "agents coordinated"],
  ["<2m", "from email to task"]
];

const workflow = [
  ["Analyze", "Summarize customer intent, urgency, sentiment, and buying signals."],
  ["Operationalize", "Create or update the lead, assign status, and generate a follow-up task."],
  ["Respond", "Draft a professional reply grounded in CRM context and company knowledge."]
];

export default function LandingPage() {
  return (
    <main className="min-h-screen overflow-hidden bg-ink text-white">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(54,211,153,0.14),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(125,164,178,0.14),transparent_28%)]" />
      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-lg border border-mint/30 bg-mint/15 text-mint">
            <Sparkles size={18} />
          </div>
          <div>
            <p className="font-semibold">LeadPilot AI</p>
            <p className="text-xs text-slate-500">AI revenue operations</p>
          </div>
        </div>
        <nav className="hidden items-center gap-3 text-sm text-slate-400 md:flex">
          <Link href="/pricing" className="hover:text-white">Pricing</Link>
          <Link href="/login" className="hover:text-white">Sign in</Link>
          <Link href="/register" className="rounded-md bg-mint px-4 py-2 font-semibold text-ink">Start demo</Link>
        </nav>
      </header>

      <section className="relative z-10 mx-auto grid min-h-[calc(100vh-88px)] max-w-7xl gap-12 px-6 pb-16 pt-8 lg:grid-cols-[1.02fr_0.98fr] lg:items-center">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-line/80 bg-white/[0.035] px-3 py-1.5 text-sm text-slate-300">
            <LockKeyhole size={15} className="text-mint" />
            Built for B2B sales teams handling real customer data
          </div>
          <h1 className="max-w-4xl text-5xl font-semibold leading-[0.95] tracking-[-0.04em] md:text-7xl">
            Turn inbound messages into CRM action in one AI workflow.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
            LeadPilot AI reads customer emails, scores buying intent, drafts replies, updates the pipeline, creates tasks, and keeps teams aligned across CRM, knowledge, and operations.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/register" className="inline-flex items-center gap-2 rounded-md bg-mint px-5 py-3 text-sm font-semibold text-ink shadow-sm shadow-mint/10">
              Create demo workspace <ArrowRight size={16} />
            </Link>
            <Link href="/pricing" className="inline-flex items-center gap-2 rounded-md border border-line/80 bg-white/[0.025] px-5 py-3 text-sm font-semibold text-slate-200">
              View pricing
            </Link>
          </div>
          <div className="mt-10 grid max-w-xl grid-cols-3 gap-3">
            {stats.map(([value, label]) => (
              <div key={label} className="rounded-lg border border-line/70 bg-white/[0.025] p-4">
                <p className="text-2xl font-semibold text-white">{value}</p>
                <p className="mt-1 text-xs uppercase tracking-[0.1em] text-slate-500">{label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-line/80 bg-panel/95 p-5 shadow-glow">
          <div className="mb-5 flex items-center justify-between border-b border-line/70 pb-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Live demo scenario</p>
              <h2 className="mt-1 text-xl font-semibold">Acme Operations</h2>
            </div>
            <div className="rounded-md border border-mint/30 bg-mint/15 px-3 py-1.5 text-sm font-semibold text-mint">Qualified</div>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              ["Sentiment", "Positive", Bot],
              ["Lead score", "85/100", LineChart],
              ["Task", "Demo next week", SquareCheckBig]
            ].map(([label, value, Icon]) => (
              <div key={label as string} className="rounded-md border border-line/70 bg-ink/70 p-4">
                <Icon className="mb-4 text-mint" size={18} />
                <p className="text-xs text-slate-500">{label as string}</p>
                <p className="mt-1 font-semibold">{value as string}</p>
              </div>
            ))}
          </div>
          <div className="mt-5 space-y-3">
            {workflow.map(([title, detail], index) => (
              <div key={title} className="flex gap-3 rounded-md border border-line/70 bg-ink/70 p-4">
                <div className="grid size-7 shrink-0 place-items-center rounded-md bg-mint/15 text-xs font-semibold text-mint">{index + 1}</div>
                <div>
                  <p className="text-sm font-semibold text-white">{title}</p>
                  <p className="mt-1 text-sm leading-6 text-slate-400">{detail}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-line/70 bg-ink/70 p-4">
              <Database className="mb-3 text-mint" size={18} />
              <p className="text-sm font-semibold">Knowledge-grounded answers</p>
              <p className="mt-1 text-sm text-slate-500">Upload product docs and answer customer questions with citations.</p>
            </div>
            <div className="rounded-md border border-line/70 bg-ink/70 p-4">
              <Plug className="mb-3 text-mint" size={18} />
              <p className="text-sm font-semibold">Integration-ready</p>
              <p className="mt-1 text-sm text-slate-500">Prepared for widgets, webhooks, and public lead capture APIs.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="relative z-10 mx-auto grid max-w-7xl gap-4 px-6 pb-20 md:grid-cols-3">
        {[
          ["For sales leaders", "See pipeline quality, AI usage, follow-up workload, and recent activity in one cockpit."],
          ["For operators", "Convert messy inbound emails into structured CRM records and accountable next steps."],
          ["For engineers", "A full-stack SaaS architecture with FastAPI, Next.js, PostgreSQL, Celery, Redis, RAG, and CI."]
        ].map(([title, detail]) => (
          <article key={title} className="rounded-xl border border-line/80 bg-white/[0.025] p-5">
            <CheckCircle2 className="mb-4 text-mint" size={18} />
            <h3 className="font-semibold">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">{detail}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
