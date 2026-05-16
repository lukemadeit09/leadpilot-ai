import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="mb-6">
        <p className="text-sm text-mint">Workspace</p>
        <h1 className="text-3xl font-semibold text-white">Settings</h1>
      </div>
      <section className="rounded-lg border border-line bg-panel p-5">
        <h2 className="text-lg font-semibold">Deployment readiness</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <div className="rounded-md border border-line bg-ink p-4"><Badge tone="good">Configured</Badge><p className="mt-3 text-sm text-slate-300">JWT authentication</p></div>
          <div className="rounded-md border border-line bg-ink p-4"><Badge tone="good">Configured</Badge><p className="mt-3 text-sm text-slate-300">API environment variables</p></div>
          <div className="rounded-md border border-line bg-ink p-4"><Badge tone="info">Optional</Badge><p className="mt-3 text-sm text-slate-300">OpenAI key for live AI calls</p></div>
        </div>
      </section>
    </AppShell>
  );
}
