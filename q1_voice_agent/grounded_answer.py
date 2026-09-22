"""Grounded answer generation from KB retrieval results.

Given a user question, retrieve from the Q2 KB and produce a spoken-style
answer that is strictly grounded in the retrieved chunks. Two modes:

  - LLM mode (OPENAI_API_KEY set): the model rewrites the retrieved context into
    a short, natural answer, instructed to refuse if the context lacks the fact.
  - Fallback mode (no key): returns the top chunk's content trimmed to a
    sentence or two, or a safe "not confirmed" message.

Either way, if retrieval is not confident, we return a safe fallback so the
voice agent never hallucinates.
"""
from __future__ import annotations

from shared.config import settings
from shared.logging_utils import get_logger
from q2_knowledge_base.retriever import Retriever, RetrievedAnswer

log = get_logger("q1.grounded")

NOT_CONFIRMED = (
    "I don't have that detail confirmed, so I won't guess. "
    "I can have a specialist follow up with the exact information."
)


class GroundedAnswerer:
    def __init__(self, retriever: Retriever | None = None) -> None:
        self.retriever = retriever or Retriever()

    def answer(self, question: str, category: str | None = None) -> dict:
        ans = self.retriever.retrieve(question, top_k=3, category=category)
        if not ans.confident:
            return {
                "answer": NOT_CONFIRMED,
                "grounded": False,
                "citations": ans.citations(),
                "confidence": round(ans.top_score, 3),
            }
        text = self._compose(question, ans)
        return {
            "answer": text,
            "grounded": True,
            "citations": ans.citations(),
            "confidence": round(ans.top_score, 3),
        }

    def _compose(self, question: str, ans: RetrievedAnswer) -> str:
        if settings.has_openai:
            llm = self._llm_compose(question, ans)
            if llm:
                return llm
        # Fallback: return the most relevant chunk, lightly trimmed.
        top = ans.results[0].chunk.content
        # Keep it short for speech: first 2 sentences.
        parts = top.replace("\n", " ").split(". ")
        return ". ".join(parts[:2]).strip().rstrip(".") + "."

    def _llm_compose(self, question: str, ans: RetrievedAnswer) -> str | None:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            context = ans.context_block()
            prompt = (
                "You answer a caller's question using ONLY the context below. "
                "If the context does not contain the answer, reply exactly with "
                f"'{NOT_CONFIRMED}'. Keep it to 1-2 short spoken sentences, no citations.\n\n"
                f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
            )
            resp = client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=120,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:  # pragma: no cover
            log.warning("LLM compose failed (%s); using extractive fallback", e)
            return None
