.PHONY: setup up dev down logs db-migrate demo clean ps restart

# ═══════════════════════════════════════════════════
# SwarmForge Ultimate — Makefile
# ═══════════════════════════════════════════════════

setup: ## Initial setup — copy env, pull images, init DB
	@cp -n .env.example .env 2>/dev/null || true
	@echo "📦 Pulling Docker images..."
	docker compose pull
	@echo "🗄️  Starting database services..."
	docker compose up -d postgres redis
	@sleep 4
	@echo "✅ Setup complete! Run 'make up' to start everything."

up: ## Start all services in background
	docker compose up -d
	@echo ""
	@echo "  ⚡ SwarmForge Ultimate is running!"
	@echo "  ┌──────────────────────────────────────┐"
	@echo "  │  Dashboard:  http://localhost         │"
	@echo "  │  API:        http://localhost:8000     │"
	@echo "  │  LiteLLM:    http://localhost:4000     │"
	@echo "  │  Grafana:    http://localhost:3001     │"
	@echo "  │  Prometheus: http://localhost:9090     │"
	@echo "  └──────────────────────────────────────┘"

dev: ## Start with live logs
	docker compose up

down: ## Stop all services
	docker compose down
	@echo "🛑 All services stopped."

logs: ## Follow API logs
	docker compose logs -f api

db-migrate: ## Run database migrations
	docker compose run --rm api alembic upgrade head

demo: ## Launch a demo session
	@echo "🚀 Creating demo session..."
	curl -s -X POST http://localhost:8000/api/v1/sessions \
		-H "Content-Type: application/json" \
		-d '{"name":"demo-todo-app","spec":"Build a full-stack TODO application with user authentication using JWT, a REST API with FastAPI, PostgreSQL database, and a React frontend. Features: create, read, update, delete tasks; mark tasks as complete; filter by status; user registration and login."}' | python -m json.tool

clean: ## Stop and remove ALL data (volumes)
	docker compose down -v --remove-orphans
	rm -rf output/*
	@echo "🧹 Clean complete — all data removed."

ps: ## Show running services
	docker compose ps

restart: ## Restart a specific service (usage: make restart service=api)
	docker compose restart $(service)

health: ## Check API health
	@curl -s http://localhost:8000/api/v1/health | python -m json.tool

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
