-- Script de inicialização do banco de dados
-- Este script é usado pelo Floci e pelo R PostgreSQL

-- Criar extensão necessária para UUID (se não existir)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Criar tabela de clientes se não existir
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefone VARCHAR(50),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar tabela de eventos de webhook se não existir
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_tipo VARCHAR(100) NOT NULL,
    card_id INTEGER NOT NULL,
    payload JSONB NOT NULL,
    processado_em TIMESTAMP WITH TIME ZONE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);
CREATE INDEX IF NOT EXISTS idx_webhook_events_card_id ON webhook_events(card_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_evento_tipo ON webhook_events(evento_tipo);

-- Inserir dados de teste (opcional, comentado por padrão)
-- INSERT INTO clientes (nome, email, telefone) VALUES
-- ('João Silva', 'joao@example.com', '+55 11 98765-4321'),
-- ('Maria Santos', 'maria@example.com', '+55 11 98765-4322');

-- Comentar
COMMENT ON TABLE clientes IS 'Tabela de clientes do Mundo Invest';
COMMENT ON TABLE webhook_events IS 'Eventos recebidos do Pipefy via webhooks';
