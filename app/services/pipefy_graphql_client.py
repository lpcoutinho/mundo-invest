import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CreateCardMutation:
    pipe_id: int
    title: str
    fields_attributes: list[dict[str, str]] = field(default_factory=list)

    def build(self) -> str:
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
    def __init__(self, pipe_id: int = 123) -> None:
        self._pipe_id = pipe_id

    async def send_create_card(
        self, nome: str, email: str, patrimonio: float, tipo_solicitacao: str
    ) -> dict:
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
