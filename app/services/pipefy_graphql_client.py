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
        pipe_id: String identifier of the target Pipefy pipe.
        title: Card title, conventionally ``"{cliente_nome} - {tipo_solicitacao}"``.
        fields_attributes: List of ``{field_id, field_value}`` dicts matching
            the pipe's field configuration.
    """
    pipe_id: str
    title: str
    fields_attributes: list[dict[str, str]] = field(default_factory=list)

    def build(self) -> str:
        """Render this mutation as a raw GraphQL string.

        The returned string is a valid Pipefy ``createCard`` mutation
        that can be sent directly to ``https://api.pipefy.com/graphql``.
        """
        fields = "\n".join(
            f'      {{field_id: "{f["field_id"]}", field_value: "{f["field_value"]}"}}'
            for f in self.fields_attributes
        )
        return (
            "mutation {\n"
            f"  createCard(input: {{\n"
            f'    pipe_id: "{self.pipe_id}",\n'
            f'    title: "{self.title}",\n'
            f"    fields_attributes: [\n"
            f"{fields}\n"
            f"    ]\n"
            f"  }}) {{ card {{ id title }} }}\n"
            f"}}"
        )


@dataclass
class UpdateCardFieldsMutation:
    """Encapsulates a Pipefy mutation with multiple ``updateCardField`` aliases.

    Pipefy GraphQL supports operation aliases, allowing multiple field
    updates in a single mutation call. This dataclass builds one such
    multi-operation mutation.

    Attributes:
        card_id: The Pipefy card ID to update.
        field_updates: List of ``(alias, field_id, new_value)`` tuples.
            The alias is a unique operation name (e.g. ``"updateStatus"``).
    """
    card_id: str
    field_updates: list[tuple[str, str, str]]

    def build(self) -> str:
        """Render this mutation as a raw GraphQL string with aliases.

        Example output:
            mutation {
              updateStatus: updateCardField(input: {
                card_id: "1357045729", field_id: "status", new_value: "Processado"
              }) { card { id } }

              updatPrioridade: updateCardField(input: {
                card_id: "1357045729", field_id: "prioridade", new_value: "prioridade_alta"
              }) { card { id } }
            }
        """
        operations = "\n\n".join(
            f'  {alias}: updateCardField(input: {{ '
            f'card_id: "{self.card_id}", '
            f'field_id: "{field_id}", '
            f'new_value: "{new_value}" '
            f'}}) {{ card {{ id }} }}'
            for alias, field_id, new_value in self.field_updates
        )
        return f"mutation {{\n{operations}\n}}"


class PipefyGraphQLClient:
    """Client for Pipefy's GraphQL API, currently in simulation mode.

    In production this class would:
      1. POST the mutation string to ``api.pipefy.com/graphql``
      2. Attach the ``Authorization: Bearer <token>`` header

    During development and testing it logs the mutation and returns
    a mock response matching the real Pipefy response shape so that
    every layer of the application can be exercised end-to-end.
    """

    def __init__(self, pipe_id: str) -> None:
        self._pipe_id = pipe_id

    async def send_create_card(
        self, nome: str, email: str, patrimonio: float, tipo_solicitacao: str
    ) -> dict:
        """Simulate a Pipefy ``createCard`` mutation.

        Returns:
            A dict matching the real Pipefy response format:
            ``{"data": {"createCard": {"card": {"id": "1357045729", "title": "..."}}}}``
        """
        title = f"{nome} - {tipo_solicitacao}"
        mutation = CreateCardMutation(
            pipe_id=self._pipe_id,
            title=title,
            fields_attributes=[
                {"field_id": "cliente_nome", "field_value": nome},
                {"field_id": "cliente_email", "field_value": email},
                {"field_id": "tipo_solicitacao", "field_value": tipo_solicitacao},
                {"field_id": "valor_patrimonio", "field_value": str(int(patrimonio))},
            ],
        )
        graphql_payload = mutation.build()
        print("===== CREATE CARD =====\n" + graphql_payload + "\n" + "=" * 25)
        return {
            "data": {
                "createCard": {
                    "card": {
                        "id": "1357045729",
                        "title": title,
                    }
                }
            }
        }

    async def send_update_card_fields(
        self, card_id: str, fields: list[tuple[str, str, str]]
    ) -> dict:
        """Simulate a Pipefy multi-field ``updateCardField`` mutation with aliases.

        Args:
            card_id: The Pipefy card ID to update.
            fields: List of ``(alias, field_id, new_value)`` tuples.
                Example: ``("updateStatus", "status", "Processado")``

        Returns:
            A dict matching the real Pipefy response format with aliased keys:
            ``{"data": {"updateStatus": {"card": {"id": "..."}}, "updatPrioridade": {"card": {"id": "..."}}}}``
        """
        mutation = UpdateCardFieldsMutation(card_id=card_id, field_updates=fields)
        graphql_payload = mutation.build()
        print("===== UPDATE CARD =====\n" + graphql_payload + "\n" + "=" * 25)
        data = {}
        for alias, _, _ in fields:
            data[alias] = {"card": {"id": card_id}}
        return {"data": data}
