.PHONY: help install dev lint typecheck check test test-cov run db-up db-down clean

help:
	@echo "Comandos disponiveis:"
	@echo "  make install     Instalar dependencias do projeto"
	@echo "  make dev         Instalar dependencias incluindo dev"
	@echo "  make lint        Rodar ruff (linter)"
	@echo "  make typecheck   Rodar mypy (type checker)"
	@echo "  make check       Rodar lint + typecheck"
	@echo "  make test        Rodar testes com pytest"
	@echo "  make test-cov    Rodar testes com cobertura"
	@echo "  make run         Subir servidor uvicorn"
	@echo "  make db-up       Subir PostgreSQL via Docker"
	@echo "  make db-down     Parar PostgreSQL"
	@echo "  make clean       Remover cache e artefatos"

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
	docker compose up -d

db-down:
	docker compose down

clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf *.egg-info
