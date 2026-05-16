import json
import re
from typing import Any

from openai import OpenAI

from app.config import get_settings


class BaseAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def complete_json(self, system: str, user: str) -> dict[str, Any] | None:
        if not self.client:
            return None
        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    @staticmethod
    def keyword_score(message: str) -> int:
        text = message.lower()
        score = 35
        signals = {
            r"\bpricing|price|quote|budget|contract\b": 18,
            r"\bdemo|schedule|call|meeting|next week\b": 20,
            r"\bteam|employees|company|department\b": 12,
            r"\burgent|asap|this week|deadline\b": 15,
        }
        for pattern, weight in signals.items():
            if re.search(pattern, text):
                score += weight
        return max(1, min(score, 100))
