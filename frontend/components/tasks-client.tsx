"use client";

import { useCallback } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, EmptyState, LoadingRows, PageHeader, Panel } from "@/components/ui";
import { api } from "@/lib/api";
import { useAsyncData } from "@/hooks/use-api";
import type { Task } from "@/types";

export function TasksClient() {
  const loader = useCallback(() => api<Task[]>("/tasks"), []);
  const { data, loading, error } = useAsyncData(loader);
  return (
    <AppShell>
      <PageHeader
        eyebrow="Execution"
        title="Tasks"
        description="Track the operational follow-ups created manually or by the AI workflow."
      />
      <Panel title="Follow-up queue" description="Prioritized sales work generated from lead activity">
        <div className="p-5">
        {error && <p className="text-sm text-rose-200">{error}</p>}
        {loading || !data ? (
          <LoadingRows />
        ) : data.length === 0 ? (
          <EmptyState title="No tasks yet" detail="Analyze a lead and LeadPilot AI will create follow-up work automatically." />
        ) : (
          <div className="space-y-3">
            {data.map((task) => (
              <div key={task.id} className="flex flex-col justify-between gap-3 rounded-md border border-line/70 bg-ink/70 p-4 transition hover:bg-white/[0.025] md:flex-row md:items-center">
                <div>
                  <p className="font-medium text-white">{task.title}</p>
                  <p className="mt-1 text-sm text-slate-400">{task.description}</p>
                </div>
                <div className="flex gap-2">
                  <Badge tone={task.priority === "high" || task.priority === "urgent" ? "warn" : "neutral"}>{task.priority}</Badge>
                  <Badge tone={task.status === "completed" ? "good" : "info"}>{task.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        )}
        </div>
      </Panel>
    </AppShell>
  );
}
