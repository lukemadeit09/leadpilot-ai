export type LeadStatus = "new" | "analyzed" | "qualified" | "contacted" | "follow_up" | "closed_won" | "closed_lost";
export type TaskStatus = "pending" | "in_progress" | "completed" | "cancelled";
export type TaskPriority = "low" | "medium" | "high" | "urgent";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

export type Lead = {
  id: string;
  name?: string | null;
  email?: string | null;
  company?: string | null;
  message: string;
  status: LeadStatus;
  score: number;
  sentiment?: string | null;
  urgency?: string | null;
  created_at: string;
  updated_at: string;
};

export type Analysis = {
  id: string;
  lead_id: string;
  summary: string;
  sentiment: string;
  urgency: string;
  category: string;
  lead_score: number;
  pain_points: string[];
  buying_intent: string;
  recommended_action: string;
  suggested_reply: string;
  follow_up_task: string;
  created_at: string;
};

export type Task = {
  id: string;
  lead_id?: string | null;
  title: string;
  description?: string | null;
  due_date?: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  created_at: string;
};

export type Activity = {
  id: string;
  lead_id?: string | null;
  action: string;
  detail: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type DashboardMetrics = {
  total_leads: number;
  qualified_leads: number;
  average_score: number;
  pending_tasks: number;
  pipeline: Record<LeadStatus, number>;
  recent_activity: Activity[];
};

export type BillingUsage = {
  organization_id: string;
  plan: "starter" | "pro" | "agency";
  plan_label: string;
  monthly_limit: number;
  organization_used: number;
  user_used: number;
  remaining: number;
  usage_percent: number;
  requests: number;
  tokens: number;
  month_start: string;
};

export type AnalyzeLeadResponse = {
  lead: Lead;
  analysis: Analysis;
  task: Task;
  activity: Activity;
};

export type AIJob = {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  endpoint_used: string;
  attempts: number;
  max_attempts: number;
  error_message?: string | null;
  result_payload?: AnalyzeLeadResponse | null;
  created_at: string;
  updated_at: string;
};

export type KnowledgeDocument = {
  id: string;
  filename: string;
  content_type?: string | null;
  created_at: string;
};
