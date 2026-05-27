"""Business rule for assigning client priority based on invested assets.

Why a dedicated class instead of a free function:
Encapsulating the threshold and logic in a class makes the rule
显式 (explicit), testable in isolation, and easy to find when
the business changes the threshold value.
"""
import logging

logger = logging.getLogger(__name__)


class PriorityCalculator:
    """Assigns a priority level based on ``valor_patrimonio``.

    The threshold is ``200_000.0``:
    - ``>= 200k`` → ``"prioridade_alta"``
    - ``< 200k``  → ``"prioridade_normal"``

    Why ``@staticmethod``:
    The calculator is pure — no state, no side effects. A static
    method communicates this clearly and avoids unnecessary
    instantiation in the service layer.
    """

    PRIORITY_THRESHOLD: float = 200_000.0

    @staticmethod
    def calculate(valor_patrimonio: float) -> str:
        """Return the priority string for the given asset value."""
        if valor_patrimonio >= PriorityCalculator.PRIORITY_THRESHOLD:
            return "prioridade_alta"
        return "prioridade_normal"
