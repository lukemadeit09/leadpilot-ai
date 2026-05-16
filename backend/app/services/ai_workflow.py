from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import AnalyzerAgent, CRMAgent, ReplyAgent, ScoringAgent, TaskAgent
from app.models import Lead, LeadAnalysis, LeadStatus, Task, TaskPriority, User
from app.schemas import AnalysisPayload, AnalyzeLeadRequest
from app.services.activity import log_activity


class AILeadWorkflow:
    def __init__(self) -> None:
        self.analyzer = AnalyzerAgent()
        self.scorer = ScoringAgent()
        self.reply = ReplyAgent()
        self.crm = CRMAgent()
        self.task_agent = TaskAgent()

    def run(self, db: Session, user: User, payload: AnalyzeLeadRequest) -> tuple[Lead, LeadAnalysis, Task, object]:
        raw_analysis = self.analyzer.analyze(payload.message)
        lead_score = self.scorer.score(payload.message, raw_analysis)
        suggested_reply = self.reply.draft(payload.message, raw_analysis)

        analysis_payload = AnalysisPayload(
            summary=raw_analysis.get("summary", "Customer message analyzed."),
            sentiment=raw_analysis.get("sentiment", "neutral"),
            urgency=raw_analysis.get("urgency", "medium"),
            category=raw_analysis.get("category", "general inquiry"),
            lead_score=lead_score,
            pain_points=raw_analysis.get("pain_points", []),
            buying_intent=raw_analysis.get("buying_intent", "medium"),
            recommended_action="",
            suggested_reply=suggested_reply,
            follow_up_task="",
        )
        status_value, action = self.crm.decide(analysis_payload)
        analysis_payload.recommended_action = action
        analysis_payload.follow_up_task = self._follow_up_title(status_value, payload.company)

        lead = self._upsert_lead(db, user, payload, analysis_payload, status_value)
        analysis = LeadAnalysis(lead_id=lead.id, **analysis_payload.model_dump())
        db.add(analysis)

        task_spec = self.task_agent.create_task(payload.message, analysis_payload)
        task = Task(
            owner_id=user.id,
            lead_id=lead.id,
            title=task_spec["title"],
            description=task_spec["description"],
            priority=TaskPriority(task_spec["priority"]),
            due_date=datetime.now(timezone.utc) + timedelta(days=2 if task_spec["priority"] == "high" else 5),
        )
        db.add(task)

        activity = log_activity(
            db,
            owner_id=user.id,
            lead_id=lead.id,
            action="email_analyzed",
            detail=f"AI analyzed lead and set pipeline status to {status_value}.",
            metadata={"lead_score": lead_score, "sentiment": analysis_payload.sentiment},
        )
        db.commit()
        db.refresh(lead)
        db.refresh(analysis)
        db.refresh(task)
        db.refresh(activity)
        return lead, analysis, task, activity

    def _upsert_lead(self, db: Session, user: User, payload: AnalyzeLeadRequest, analysis: AnalysisPayload, status_value: str) -> Lead:
        lead = None
        if payload.email:
            lead = db.scalar(select(Lead).where(Lead.owner_id == user.id, Lead.email == str(payload.email)))
        if not lead:
            lead = Lead(owner_id=user.id, message=payload.message)
            db.add(lead)
        lead.name = payload.name
        lead.email = str(payload.email) if payload.email else None
        lead.company = payload.company
        lead.message = payload.message
        lead.score = analysis.lead_score
        lead.sentiment = analysis.sentiment
        lead.urgency = analysis.urgency
        lead.status = LeadStatus(status_value)
        return lead

    @staticmethod
    def _follow_up_title(status_value: str, company: str | None) -> str:
        account = company or "lead"
        if status_value == "qualified":
            return f"Schedule demo with {account}"
        if status_value == "follow_up":
            return f"Send qualification follow-up to {account}"
        return f"Review next steps for {account}"
