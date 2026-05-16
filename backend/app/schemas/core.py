from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import AIJobStatus, LeadStatus, PlanType, TaskPriority, TaskStatus


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class LeadBase(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    company: str | None = None
    message: str = Field(min_length=5)


class LeadCreate(LeadBase):
    status: LeadStatus = LeadStatus.new


class LeadUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    company: str | None = None
    message: str | None = None
    status: LeadStatus | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    sentiment: str | None = None
    urgency: str | None = None


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: LeadStatus
    score: int
    sentiment: str | None
    urgency: str | None
    created_at: datetime
    updated_at: datetime


class AnalysisPayload(BaseModel):
    summary: str
    sentiment: str
    urgency: str
    category: str
    lead_score: int = Field(ge=1, le=100)
    pain_points: list[str] = Field(default_factory=list)
    buying_intent: str
    recommended_action: str
    suggested_reply: str
    follow_up_task: str


class AnalyzeLeadRequest(LeadBase):
    pass


class LeadAnalysisRead(AnalysisPayload):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    due_date: datetime | None = None
    lead_id: UUID | None = None
    priority: TaskPriority = TaskPriority.medium


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: datetime | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID | None
    title: str
    description: str | None
    due_date: datetime | None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID | None
    action: str
    detail: str
    metadata_json: dict
    created_at: datetime


class AnalyzeLeadResponse(BaseModel):
    lead: LeadRead
    analysis: LeadAnalysisRead
    task: TaskRead
    activity: ActivityRead


class AIJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: AIJobStatus
    endpoint_used: str
    attempts: int
    max_attempts: int
    error_message: str | None
    result_payload: dict | None
    created_at: datetime
    updated_at: datetime


class ReplyRequest(BaseModel):
    message: str = Field(min_length=5)
    tone: str = "professional"


class ReplyResponse(BaseModel):
    suggested_reply: str


class DashboardMetrics(BaseModel):
    total_leads: int
    qualified_leads: int
    average_score: float
    pending_tasks: int
    pipeline: dict[str, int]
    recent_activity: list[ActivityRead]


class KnowledgeDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str | None
    created_at: datetime


class KnowledgeAskRequest(BaseModel):
    question: str = Field(min_length=4)


class KnowledgeAskResponse(BaseModel):
    answer: str
    sources: list[str]


class PlanRead(BaseModel):
    plan: PlanType
    label: str
    monthly_limit: float
    included_seats: int


class PlanUpdate(BaseModel):
    plan: PlanType


class UsageSummary(BaseModel):
    organization_id: UUID
    plan: PlanType
    plan_label: str
    monthly_limit: float
    organization_used: float
    user_used: float
    remaining: float
    usage_percent: float
    requests: int
    tokens: int
    month_start: datetime
