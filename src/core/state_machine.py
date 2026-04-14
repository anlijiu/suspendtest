"""单轮执行状态机。"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.models import CyclePhase


@dataclass(slots=True)
class CycleStateMachine:
    """记录单轮流程阶段迁移。"""

    phase_history: list[CyclePhase] = field(default_factory=lambda: [CyclePhase.IDLE])

    def transit(self, phase: CyclePhase) -> None:
        """迁移到新阶段。

        Args:
            phase: 目标阶段。
        """
        self.phase_history.append(phase)

