.PHONY: help install dev lint typecheck check test test-cov run
.PHONY: db-up db-down
.PHONY: build up down logs shell test-docker clean-docker clean

help:
	@echo "Comandos disponiveis:"
	@echo "  make install       Instalar dependencias do projeto"
	@echo "  make dev           Instalar dependencias incluindo dev"
	@echo "  make lint          Rodar ruff (linter)"
	@echo "  make typecheck     Rodar mypy (type checker)"
	@echo "  make check         Rodar lint + typecheck"
	@echo "  make test          Rodar testes com pytest"
	@echo "  make test-cov      Rodar testes com cobertura"
	@echo "  make run           Subir servidor uvicorn"
	@echo ""
	@echo "Docker:"
	@echo "  make db-up         Subir apenas PostgreSQL via Docker"
	@echo "  make db-down       Parar apenas PostgreSQL"
	@echo "  make build         Build da imagem Docker da aplicacao"
	@echo "  make up            Subir todo o stack (postgres + floci + app)"
	@echo "  make down          Derrubar todos os servicos"
	@echo "  make logs          Tail dos logs do container app"
	@echo "  make shell         Bash interativo no container app"
	@echo "  make test-docker   Rodar pytest dentro do container app"
	@echo "  make clean-docker  Derrubar tudo e remover volumes"
	@echo ""
	@echo "Utilitarios:"
	@echo "  make clean         Remover cache e artefatos"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

lint:
	ruff check app/ tests/

typecheck:
	mypy app/ tests/

check: lint typecheck

test:
	pytest -v

test-cov:
	pytest -v --cov=app --cov-report=term-missing

run:
	uvicorn app.main:app --reload --port 8000

db-up:
	docker compose up -d postgres

db-down:
	docker compose down postgres

build:
	docker compose build app

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f app

shell:
	docker compose exec app bash

test-docker:
	docker compose run --rm app pytest -v

clean-docker:
	docker compose down -v

clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf *.egg-info
