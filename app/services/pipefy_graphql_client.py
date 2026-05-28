"""Pipefy GraphQL mutation builder and simulated HTTP client.

This module mirrors the official Pipefy API specification for cards.
Reference: https://developers.pipefy.com/reference/cards#card-mutations

The ``createCard`` mutation structure follows:
    mutation {
      createCard(input: { pipe_id: ..., title: ..., fields_attributes: [...] }) {
        card { id title }
      }
    }

Why dataclasses for mutations:
Building GraphQL strings through dataclass instances makes the
payload explicit, type-checked, and testable — unlike concatenating
f-strings in the service layer.
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CreateCardMutation:
    """Encapsulates a Pipefy ``createCard`` mutation payload.

    Attributes:
        pipe_id: Numeric identifier of the target Pipefy pipe.
        title: Card title, conventionally ``"{cliente_nome} - {tipo_solicitacao}"``.
        fields_attributes: List of ``{field_id, field_value}`` dicts matching
            the pipe's field configuration.
    """
    pipe_id: int
    title: str
    fields_attributes: list[dict[str, str]] = field(default_factory=list)

    def build(self) -> str:
        """Render this mutation as a raw GraphQL string.

        The returned string is a valid Pipefy ``createCard`` mutation
        that can be sent directly to ``https://api.pipefy.com/graphql``.
        """
        fields = ", ".join(
            f'{{field_id: "{f["field_id"]}", field_value: "{f["field_value"]}"}}'
            for f in self.fields_attributes
        )
        return (
            f"mutation {{ createCard(input: {{ pipe_id: {self.pipe_id}, "
            f'title: "{self.title}", fields_attributes: [{fields}] '
            f"}}) {{ card {{ id title }} }} }}"
        )


class PipefyGraphQLClient:
    """Client for Pipefy's GraphQL API, currently in simulation mode.

    In production this class would:
      1. POST the mutation string to ``api.pipefy.com/graphql``
      2. Attach the ``Authorization: Bearer <token>`` header

    During development and testing it logs the mutation and returns
    a mock response matching the real Pipefy response shape so that
    every layer of the application can be exercised end-to-end.
    """

    def __init__(self, pipe_id: int = 123) -> None:
        self._pipe_id = pipe_id

    async def send_create_card(
        self, nome: str, email: str, patrimonio: float, tipo_solicitacao: str
    ) -> dict:
        """Simulate a Pipefy ``createCard`` mutation.

        Returns:
            A dict matching the real Pipefy response format:
            ``{"data": {"createCard": {"card": {"id": "...", "title": "..."}}}}``
        """
        title = f"{nome} - {tipo_solicitacao}"
        mutation = CreateCardMutation(
            pipe_id=self._pipe_id,
            title=title,
            fields_attributes=[
                {"field_id": "cliente_nome", "field_value": nome},
                {"field_id": "cliente_email", "field_value": email},
                {"field_id": "valor_patrimonio", "field_value": str(int(patrimonio))},
            ],
        )
        graphql_payload = mutation.build()
        logger.info("Simulating Pipefy createCard mutation:\n%s", graphql_payload)
        return {
            "data": {
                "createCard": {
                    "card": {
                        "id": "1356383093",
                        "title": title,
                    }
                }
            }
        }
