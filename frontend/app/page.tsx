import { ArrowRight, Bot, Database, LineChart, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <section className="mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-6 py-16">
        <div className="grid gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-md border border-line bg-white/5 px-3 py-1 text-sm text-slate-300">
              <ShieldCheck size={16} className="text-mint" />
              Enterprise-style AI sales operations
            </div>
            <h1 className="max-w-3xl text-5xl font-semibold leading-tight tracking-normal md:text-7xl">LeadPilot AI</h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              An AI-powered CRM automation platform that reads customer messages, analyzes leads, drafts replies, saves CRM data, creates follow-up tasks, and keeps sales teams moving.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/register" className="inline-flex items-center gap-2 rounded-md bg-mint px-5 py-3 text-sm font-semibold text-ink">
                Create workspace <ArrowRight size={16} />
              </Link>
              <Link href="/login" className="inline-flex items-center gap-2 rounded-md border border-line px-5 py-3 text-sm font-semibold text-slate-200">
                Sign in
              </Link>
            </div>
          </div>
          <div className="rounded-lg border border-line bg-panel p-5 shadow-glow">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Pipeline command center</p>
                <h2 className="text-xl font-semibold">AI triage result</h2>
              </div>
              <div className="rounded-md bg-mint px-3 py-1 text-sm font-semibold text-ink">85/100</div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                ["Sentiment", "Positive", Bot],
                ["Status", "Qualified", LineChart],
                ["Knowledge", "Grounded", Database]
              ].map(([label, value, Icon]) => (
                <div key={label as string} className="rounded-md border border-line bg-ink p-4">
                  <Icon className="mb-4 text-mint" size={18} />
                  <p className="text-xs text-slate-500">{label as string}</p>
                  <p className="mt-1 font-semibold">{value as string}</p>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded-md border border-line bg-ink p-4">
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
