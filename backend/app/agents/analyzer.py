from app.agents.base import BaseAgent
from app.schemas import AnalysisPayload


class AnalyzerAgent(BaseAgent):
    def analyze(self, message: str, model: str | None = None) -> dict:
        system = (
            "You are an enterprise sales operations analyst. Return strict JSON with "
            "summary, sentiment, urgency, category, pain_points, and buying_intent."
        )
        result = self.complete_json(system, message, model)
        if result:
            return result

        text = message.lower()
        urgency = "high" if any(word in text for word in ["urgent", "asap", "this week"]) else "medium"
        category = "sales opportunity" if any(word in text for word in ["pricing", "demo", "quote"]) else "general inquiry"
        return {
            "summary": "Customer is asking about the product and next steps.",
            "sentiment": "positive" if any(word in text for word in ["interested", "demo", "pricing"]) else "neutral",
            "urgency": urgency,
            "category": category,
            "pain_points": ["Needs clear next steps", "Needs pricing or fit confirmation"],
            "buying_intent": "high" if category == "sales opportunity" else "medium",
        }


class ScoringAgent(BaseAgent):
    def score(self, message: str, analysis: dict, model: str | None = None) -> int:
        system = "Score this lead from 1 to 100. Return JSON: {\"lead_score\": number}."
        result = self.complete_json(system, f"Message: {message}\nAnalysis: {analysis}", model)
        if result and isinstance(result.get("lead_score"), int):
            return max(1, min(result["lead_score"], 100))
        return self.keyword_score(message)


class ReplyAgent(BaseAgent):
    def draft(self, message: str, analysis: dict, tone: str = "professional", model: str | None = None) -> str:
        system = f"Draft a concise {tone} B2B sales reply. Return JSON: {{\"suggested_reply\": string}}."
        result = self.complete_json(system, f"Customer message: {message}\nAnalysis: {analysis}", model)
        if result and result.get("suggested_reply"):
            return str(result["suggested_reply"])
        return (
            "Hi,\n\nThanks for reaching out. Based on what you shared, it sounds like there may be a strong fit. "
            "I can send over pricing context and help schedule a demo for next week so we can walk through the workflow "
            "with your team.\n\nWhat day works best for a 30-minute conversation?\n\nBest,\nSales Team"
        )


class CRMAgent(BaseAgent):
    def decide(self, analysis: AnalysisPayload) -> tuple[str, str]:
        if analysis.lead_score >= 80:
            return "qualified", "Prioritize outreach and schedule a demo."
        if analysis.lead_score >= 60:
            return "follow_up", "Send discovery questions and confirm timeline."
        return "analyzed", "Nurture lead and collect more qualification details."


class TaskAgent(BaseAgent):
    def create_task(self, message: str, analysis: AnalysisPayload) -> dict:
        priority = "high" if analysis.lead_score >= 80 or analysis.urgency == "high" else "medium"
        return {
            "title": analysis.follow_up_task or "Follow up with lead",
            "description": analysis.recommended_action,
            "priority": priority,
        }
