"""深度追问链 — 苏格拉底式追问（最多 3 轮终止）"""

from __future__ import annotations

from dataclasses import dataclass, field

MAX_FOLLOWUP_ROUNDS = 3


@dataclass
class FollowUpQuestion:
    """追问项。"""

    round_num: int
    category: str
    question: str
    context: str  # 触发追问的上下文


@dataclass
class QuestionerState:
    """追问链状态管理。"""

    requirement_id: str
    current_round: int = 0
    questions_asked: list[FollowUpQuestion] = field(default_factory=list)
    user_answers: list[str] = field(default_factory=list)
    is_complete: bool = False

    @property
    def can_continue(self) -> bool:
        return self.current_round < MAX_FOLLOWUP_ROUNDS and not self.is_complete

    def add_question(self, category: str, question: str, context: str) -> FollowUpQuestion:
        self.current_round += 1
        q = FollowUpQuestion(
            round_num=self.current_round,
            category=category,
            question=question,
            context=context,
        )
        self.questions_asked.append(q)
        return q

    def add_answer(self, answer: str) -> None:
        self.user_answers.append(answer)

    def mark_complete(self) -> None:
        self.is_complete = True

    def get_conversation_context(self) -> str:
        """构建追问对话上下文，用于注入 Prompt。"""
        lines: list[str] = []
        for i, q in enumerate(self.questions_asked):
            lines.append(f"追问 {q.round_num} [{q.category}]: {q.question}")
            if i < len(self.user_answers):
                lines.append(f"用户回答: {self.user_answers[i]}")
        return "\n".join(lines)
