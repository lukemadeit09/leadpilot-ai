import { AppShell } from "@/components/app-shell";
import { Badge, PageHeader, Panel } from "@/components/ui";

export default function SettingsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Workspace"
        title="Settings"
        description="Operational readiness and deployment-sensitive configuration for the LeadPilot AI workspace."
      />
      <Panel title="Deployment readiness" description="Security and runtime checks for local and hosted environments">
        <div className="grid gap-3 p-5 md:grid-cols-3">
          <div className="rounded-md border border-line/70 bg-ink/70 p-4"><Badge tone="good">Configured</Badge><p className="mt-3 text-sm text-slate-300">JWT authentication</p></div>
          <div className="rounded-md border border-line/70 bg-ink/70 p-4"><Badge tone="good">Configured</Badge><p className="mt-3 text-sm text-slate-300">API environment variables</p></div>
          <div className="rounded-md border border-line/70 bg-ink/70 p-4"><Badge tone="info">Optional</Badge><p className="mt-3 text-sm text-slate-300">OpenAI key for live AI calls</p></div>
        </div>
      </Panel>
    </AppShell>
  );
}
