"use client";

import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, EmptyState, Field, LoadingRows, PageHeader, Panel, buttonClass, inputClass, secondaryButtonClass, tableCellClass, tableHeaderClass } from "@/components/ui";
import { useAsyncData } from "@/hooks/use-api";
import { api } from "@/lib/api";
import type { APIKey, APIKeyCreated, IntegrationUsage, WidgetConfig } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function IntegrationsClient() {
  const [newKey, setNewKey] = useState<APIKeyCreated | null>(null);
  const [keyName, setKeyName] = useState("Website lead form");
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [config, setConfig] = useState<WidgetConfig | null>(null);

  const loadKeys = useCallback(() => api<APIKey[]>("/integrations/api-keys"), []);
  const loadUsage = useCallback(() => api<IntegrationUsage[]>("/integrations/usage"), []);
  const { data: keys, loading: keysLoading, error: keysError, reload: reloadKeys } = useAsyncData(loadKeys);
  const { data: usage, loading: usageLoading, error: usageError, reload: reloadUsage } = useAsyncData(loadUsage);

  useEffect(() => {
    api<WidgetConfig>("/integrations/widget-config").then(setConfig).catch(() => undefined);
  }, []);

  const createKey = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      const created = await api<APIKeyCreated>("/integrations/api-keys", {
        method: "POST",
        body: JSON.stringify({ name: keyName })
      });
      setNewKey(created);
      await reloadKeys();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to create API key");
    } finally {
      setSubmitting(false);
    }
  };

  const saveConfig = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!config) return;
    setSubmitting(true);
    setMessage(null);
    try {
      const updated = await api<WidgetConfig>("/integrations/widget-config", {
        method: "PATCH",
        body: JSON.stringify(config)
      });
      setConfig(updated);
      setMessage("Widget configuration saved.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to save widget configuration");
    } finally {
      setSubmitting(false);
    }
  };

  const copy = async (value: string) => {
    await navigator.clipboard.writeText(value);
    setMessage("Copied to clipboard.");
  };

  const exampleKey = newKey?.api_key || "lp_live_YOUR_API_KEY";
  const widgetSnippet = `<script src="${API_URL}/integrations/widget.js" data-leadpilot-key="${exampleKey}" data-api-base="${API_URL}" async></script>`;
  const webhookExample = `curl -X POST ${API_URL}/integrations/public/webhook \\
  -H "Content-Type: application/json" \\
  -H "X-LeadPilot-Key: ${exampleKey}" \\
  -d '{"event":"contact_form.submitted","lead":{"name":"Alex Buyer","email":"alex@example.com","company":"Acme","message":"We need pricing and a demo next week."}}'`;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Connections"
        title="Business integrations"
        description="Connect LeadPilot AI to websites, contact forms, and external systems without exposing internal credentials."
      />
      <div className="space-y-5">
        {(message || keysError || usageError) && (
          <p className="rounded-md border border-line/80 bg-white/[0.035] p-3 text-sm text-slate-200">{message || keysError || usageError}</p>
        )}

        <Panel title="Organization API keys" description="Keys are shown once and then stored only as SHA-256 hashes">
          <div className="grid gap-5 p-5 lg:grid-cols-[0.9fr_1.1fr]">
            <form className="space-y-4" onSubmit={createKey}>
              <Field label="Key name">
                <input className={inputClass} value={keyName} onChange={(event) => setKeyName(event.target.value)} minLength={2} maxLength={120} />
              </Field>
              <button className={buttonClass} disabled={submitting} type="submit">
                {submitting ? "Creating..." : "Create API key"}
              </button>
              {newKey && (
                <div className="rounded-md border border-amber-300/25 bg-amber-300/10 p-3">
                  <Badge tone="warn">Shown once</Badge>
                  <p className="mt-3 break-all font-mono text-xs text-amber-50">{newKey.api_key}</p>
                  <button className={secondaryButtonClass} type="button" onClick={() => copy(newKey.api_key)}>
                    Copy raw key
                  </button>
                </div>
              )}
            </form>
            <div className="overflow-hidden rounded-md border border-line/70">
              {keysLoading ? (
                <div className="p-4"><LoadingRows /></div>
              ) : !keys?.length ? (
                <div className="p-4"><EmptyState title="No API keys yet" detail="Create a key to connect a website form or widget." /></div>
              ) : (
                <table className="w-full text-sm">
                  <thead className={tableHeaderClass}><tr><th className={tableCellClass}>Name</th><th className={tableCellClass}>Prefix</th><th className={tableCellClass}>Last used</th></tr></thead>
                  <tbody>
                    {keys.map((key) => (
                      <tr key={key.id} className="border-t border-line/70">
                        <td className={tableCellClass}>{key.name}</td>
                        <td className={`${tableCellClass} font-mono text-xs text-slate-400`}>{key.key_prefix}</td>
                        <td className={tableCellClass}>{key.last_used_at ? new Date(key.last_used_at).toLocaleString() : "Never"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </Panel>

        <Panel title="Embeddable website widget" description="Framework-agnostic JavaScript lead capture">
          <div className="grid gap-5 p-5 lg:grid-cols-2">
            <form className="space-y-4" onSubmit={saveConfig}>
              <Field label="Widget title">
                <input className={inputClass} value={config?.widget_title || ""} onChange={(event) => setConfig((current) => current && { ...current, widget_title: event.target.value })} />
              </Field>
              <Field label="Accent color">
                <input className={inputClass} value={config?.widget_accent_color || "#34d399"} onChange={(event) => setConfig((current) => current && { ...current, widget_accent_color: event.target.value })} />
              </Field>
              <label className="flex items-center gap-2 text-sm text-slate-300">
                <input type="checkbox" checked={config?.widget_enabled ?? true} onChange={(event) => setConfig((current) => current && { ...current, widget_enabled: event.target.checked })} />
                Enable public widget
              </label>
              <button className={buttonClass} disabled={submitting || !config} type="submit">Save widget settings</button>
            </form>
            <div className="space-y-3">
              <pre className="overflow-x-auto rounded-md border border-line/70 bg-ink/80 p-4 text-xs text-slate-300">{widgetSnippet}</pre>
              <button className={secondaryButtonClass} type="button" onClick={() => copy(widgetSnippet)}>Copy widget snippet</button>
            </div>
          </div>
        </Panel>

        <Panel title="Webhook endpoint" description="Send contact form submissions from external systems">
          <div className="space-y-3 p-5">
            <pre className="overflow-x-auto rounded-md border border-line/70 bg-ink/80 p-4 text-xs text-slate-300">{webhookExample}</pre>
            <button className={secondaryButtonClass} type="button" onClick={() => copy(webhookExample)}>Copy webhook example</button>
          </div>
        </Panel>

        <Panel title="Recent integration usage" description="Last 100 public integration calls">
          <div className="p-5">
            {usageLoading ? <LoadingRows /> : !usage?.length ? <EmptyState title="No integration usage yet" detail="Widget and webhook calls will appear here." /> : (
              <div className="overflow-hidden rounded-md border border-line/70">
                <table className="w-full text-sm">
                  <thead className={tableHeaderClass}><tr><th className={tableCellClass}>Endpoint</th><th className={tableCellClass}>Event</th><th className={tableCellClass}>Status</th><th className={tableCellClass}>Time</th></tr></thead>
                  <tbody>
                    {usage.map((event) => (
                      <tr key={event.id} className="border-t border-line/70">
                        <td className={tableCellClass}>{event.endpoint}</td>
                        <td className={tableCellClass}>{event.event_type}</td>
                        <td className={tableCellClass}>{event.status_code}</td>
                        <td className={tableCellClass}>{new Date(event.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <button className={`${secondaryButtonClass} mt-4`} type="button" onClick={reloadUsage}>Refresh usage</button>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
