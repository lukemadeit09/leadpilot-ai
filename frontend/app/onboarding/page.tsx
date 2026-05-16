import { ArrowRight, Bot, Database, LineChart, Mail, UploadCloud } from "lucide-react";
import Link from "next/link";

const steps = [
  {
    title: "Create your workspace",
    detail: "Register a demo account. A workspace and owner role are created automatically.",
    href: "/register",
    icon: LineChart
  },
  {
    title: "Analyze a sample lead",
    detail: "Paste the demo email into the AI Analyzer to create a lead, analysis, task, and activity log.",
    href: "/analyzer",
    icon: Bot
  },
  {
    title: "Review the CRM dashboard",
    detail: "Inspect pipeline metrics, AI usage, recent activity, and the task queue.",
    href: "/dashboard",
    icon: Mail
  },
  {
    title: "Upload company knowledge",
    detail: "Add a pricing, FAQ, or product document and ask a grounded question with citations.",
    href: "/knowledge",
    icon: UploadCloud
  }
];

const sampleEmail = "Hi, we are a 45-person operations team and are interested in your software. Can you send pricing and schedule a demo next week?";

export default function OnboardingPage() {
  return (
    <main className="min-h-screen bg-ink px-6 py-14 text-white">
      <section className="mx-auto max-w-5xl">
        <Link href="/" className="text-sm text-slate-400 hover:text-white">Back to home</Link>
        <div className="mt-10 max-w-3xl">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-steel">First-run guide</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-[-0.03em] md:text-6xl">Run a complete LeadPilot AI demo in under ten minutes.</h1>
          <p className="mt-4 text-sm leading-6 text-slate-400">
            Follow this path to show the full business workflow: inbound message, AI analysis, CRM update, follow-up task, usage tracking, and knowledge-base retrieval.
          </p>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <Link key={step.title} href={step.href} className="group rounded-xl border border-line/80 bg-panel/95 p-5 transition hover:border-mint/40 hover:bg-mint/5">
                <div className="flex items-start gap-4">
                  <div className="grid size-10 shrink-0 place-items-center rounded-lg border border-mint/30 bg-mint/15 text-mint">
                    <Icon size={18} />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Step {index + 1}</p>
                    <h2 className="mt-1 font-semibold group-hover:text-mint">{step.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-400">{step.detail}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-xl border border-line/80 bg-panel/95 p-5">
            <div className="mb-4 flex items-center gap-2">
              <Database className="text-mint" size={18} />
              <h2 className="font-semibold">Sample inbound email</h2>
            </div>
            <p className="rounded-md border border-line/70 bg-ink/70 p-4 text-sm leading-6 text-slate-300">{sampleEmail}</p>
          </div>
          <div className="rounded-xl border border-line/80 bg-panel/95 p-5">
            <h2 className="font-semibold">Expected demo outcome</h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-400">
              <li>Lead score around 85 with qualified status.</li>
              <li>Positive sentiment and medium/high urgency.</li>
              <li>Professional reply draft for pricing and demo scheduling.</li>
              <li>Follow-up task appears in Tasks and dashboard activity.</li>
            </ul>
            <Link href="/register" className="mt-5 inline-flex items-center gap-2 rounded-md bg-mint px-4 py-2.5 text-sm font-semibold text-ink">
              Start onboarding <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
