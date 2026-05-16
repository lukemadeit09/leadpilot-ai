import { ArrowRight, Bot, Database, LineChart, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <section className="mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-6 py-14">
        <div className="grid gap-10 lg:grid-cols-[1.02fr_0.98fr] lg:items-center">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-md border border-line/80 bg-white/[0.035] px-3 py-1.5 text-sm text-slate-300">
              <ShieldCheck size={16} className="text-mint" />
              Enterprise-style AI sales operations
            </div>
            <h1 className="max-w-3xl text-5xl font-semibold leading-tight tracking-normal md:text-7xl">LeadPilot AI</h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              An AI-powered CRM automation platform that reads customer messages, analyzes leads, drafts replies, saves CRM data, creates follow-up tasks, and keeps sales teams moving.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/register" className="inline-flex items-center gap-2 rounded-md bg-mint px-5 py-3 text-sm font-semibold text-ink shadow-sm shadow-mint/10">
                Create workspace <ArrowRight size={16} />
              </Link>
              <Link href="/login" className="inline-flex items-center gap-2 rounded-md border border-line/80 bg-white/[0.025] px-5 py-3 text-sm font-semibold text-slate-200">
                Sign in
              </Link>
              <Link href="/pricing" className="inline-flex items-center gap-2 rounded-md border border-line/80 bg-white/[0.025] px-5 py-3 text-sm font-semibold text-slate-200">
                View pricing
              </Link>
            </div>
          </div>
          <div className="rounded-lg border border-line/80 bg-panel/95 p-5 shadow-glow">
            <div className="mb-5 flex items-center justify-between border-b border-line/70 pb-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Pipeline command center</p>
                <h2 className="mt-1 text-xl font-semibold">AI triage result</h2>
              </div>
              <div className="rounded-md border border-mint/30 bg-mint/15 px-3 py-1.5 text-sm font-semibold text-mint">85/100</div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                ["Sentiment", "Positive", Bot],
                ["Status", "Qualified", LineChart],
                ["Knowledge", "Grounded", Database]
              ].map(([label, value, Icon]) => (
                <div key={label as string} className="rounded-md border border-line/70 bg-ink/70 p-4">
                  <Icon className="mb-4 text-mint" size={18} />
                  <p className="text-xs text-slate-500">{label as string}</p>
                  <p className="mt-1 font-semibold">{value as string}</p>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded-md border border-line/70 bg-ink/70 p-4">
              <p className="text-sm text-slate-400">Suggested reply</p>
              <p className="mt-3 text-sm leading-6 text-slate-200">
                Thanks for reaching out. I can send pricing context and help schedule a demo next week so we can walk through fit with your team.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
