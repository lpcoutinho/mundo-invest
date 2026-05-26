from app.services.pipefy_graphql_client import CreateCardMutation, PipefyGraphQLClient


class TestCreateCardMutation:
    def test_build_contains_create_card(self):
        mutation = CreateCardMutation(
            pipe_id=123,
            title="João Silva - Atualização cadastral",
            fields_attributes=[
                {"field_id": "cliente_nome", "field_value": "João Silva"},
                {"field_id": "cliente_email", "field_value": "joao@example.com"},
                {"field_id": "valor_patrimonio", "field_value": "250000"},
            ],
        )
        result = mutation.build()
        assert "mutation {" in result
        assert "createCard" in result
        assert "pipe_id: 123" in result
        assert "João Silva - Atualização cadastral" in result
        assert "cliente_nome" in result
        assert "cliente_email" in result
        assert "valor_patrimonio" in result
        assert "id title" in result


class TestPipefyGraphQLClient:
    async def test_send_create_card_returns_mock_response(self):
        client = PipefyGraphQLClient()
        result = await client.send_create_card(
            nome="João Silva",
            email="joao@example.com",
            patrimonio=250000.0,
            tipo_solicitacao="Atualização cadastral",
        )
        assert "data" in result
        assert result["data"]["createCard"]["card"]["id"] is not None
        assert "João Silva" in result["data"]["createCard"]["card"]["title"]
        assert "Atualização cadastral" in result["data"]["createCard"]["card"]["title"]
