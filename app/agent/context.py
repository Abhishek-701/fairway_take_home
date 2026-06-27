"""Conversation context extraction for follow-up questions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app import config, router


@dataclass
class ConversationContext:
    tickers: list[str]
    last_user_question: str | None
    last_assistant_summary: str | None

    def as_dict(self) -> dict:
        return {
            "tickers": self.tickers,
            "last_user_question": self.last_user_question,
            "last_assistant_summary": self.last_assistant_summary,
        }


def from_history(history: list[dict]) -> ConversationContext:
    tickers: list[str] = []
    last_user_question = None
    last_assistant_summary = None
    for msg in history:
        content = msg.get("content", "")
        found = router.detect_companies(content)
        for ticker in found:
            if ticker not in tickers:
                tickers.append(ticker)
        if msg.get("role") == "user":
            last_user_question = content
        elif msg.get("role") == "assistant":
            last_assistant_summary = content[:500]
    return ConversationContext(tickers=tickers[-3:], last_user_question=last_user_question,
                               last_assistant_summary=last_assistant_summary)


def contextualize_question(question: str, context: ConversationContext | None) -> tuple[str, dict]:
    """Resolve simple follow-ups by carrying forward the last ticker only."""
    if not context:
        return question, {}
    if router.detect_companies(question) or not context.tickers:
        return question, context.as_dict()
    if re.search(r"\b(it|its|that|they|their|this|same company|what about)\b", question, re.I):
        names = ", ".join(config.COMPANIES[t] for t in context.tickers)
        return f"For {names}, {question}", context.as_dict()
    return question, context.as_dict()
