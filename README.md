# ⚡ SwarmForge Ultimate

> **Autonomous AI Software Factory — Describe software in English, get production-ready code.**

```
   ╔══════════════════════════════════════════════╗
   ║  ⚡  S W A R M F O R G E   U L T I M A T E  ║
   ║     100% Open Source • Zero Local GPU        ║
   ╚══════════════════════════════════════════════╝
```

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com)
[![Open Source LLMs](https://img.shields.io/badge/LLMs-Open_Source-green.svg)](#models)

---

## What is SwarmForge?

SwarmForge Ultimate is an **autonomous multi-agent software factory**. You describe what software you want in natural language, and a swarm of 16 specialized AI agents collaborates to:

1. 🧠 **Analyze** your specification (CEO + CPO agents)
2. 🏗️ **Architect** the system (CTO agent)
3. 💻 **Write every line of code** (4 specialized Coder agents)
4. 🔍 **Review code quality** (Reviewer agent)
5. 🧪 **Generate & run tests** (Unit Tester + QA Lead)
6. 🛡️ **Audit security** (Security Auditor)
7. ⚡ **Benchmark performance** (Performance Analyzer)
8. 🐛 **Fix bugs automatically** (Bug Fix agent)
9. ⚖️ **Judge quality gates** (Judge agent — Go/No-Go decisions)
10. 📦 **Package for deployment** (Container + CI/CD + Docs agents)

All powered by **100% open-source models** via Groq + OpenRouter — no GPT-4, no local GPU required.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   META SWARM                            │
│  CEO ──→ CPO ──→ CTO ──→ Judge                         │
├─────────────────────────────────────────────────────────┤
│                   DEV SWARM                             │
│  Tech Lead ──→ [Backend│API│Frontend│DB] ──→ Reviewer   │
├─────────────────────────────────────────────────────────┤
│                    QA SWARM                             │
│  QA Lead ──→ [UnitTester│Security│Perf] ──→ Bug Fix    │
├─────────────────────────────────────────────────────────┤
│                   OPS SWARM                             │
│  Container Agent │ CI/CD Agent │ Docs Agent             │
├─────────────────────────────────────────────────────────┤
│              SHARED INFRASTRUCTURE                      │
│  PostgreSQL │ Redis Streams │ LiteLLM Proxy             │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer        | Technology           | Purpose                    |
|-------------|----------------------|----------------------------|
| Backend     | FastAPI + Python 3.11 | API server + orchestrator  |
| Frontend    | React 18 + Vite      | Real-time dashboard        |
| Database    | PostgreSQL 16        | Blackboard state store     |
| Event Bus   | Redis 7 Streams      | Pub/sub + task queues      |
| LLM Proxy   | LiteLLM              | Model routing + fallback   |
| Graph Viz   | React Flow           | Agent topology canvas      |
| Monitoring  | Prometheus + Grafana | Metrics + dashboards       |
| Reverse Proxy| Nginx               | Routing + WebSocket        |

## Models Used

| Agent          | Model                         | Provider   |
|---------------|-------------------------------|------------|
| CEO, CPO, CTO | Llama 3.3 70B                | Groq       |
| Judge          | DeepSeek R1 Distill 70B      | Groq       |
| Backend Coder  | DeepSeek R1                  | OpenRouter |
| Frontend Coder | Qwen 2.5 Coder 32B          | OpenRouter |
| API Coder      | Codestral 2501               | OpenRouter |
| Reviewer       | Qwen 2.5 Coder 32B          | OpenRouter |
| Security       | DeepSeek R1 Distill 70B      | Groq       |
| Ops agents     | Llama 3.1 8B Instant         | Groq       |

---

## Prerequisites

- **Docker** & **Docker Compose** v2+
- **Groq API Key** — [Get free key](https://console.groq.com)
- **OpenRouter API Key** — [Get free key](https://openrouter.ai/keys)

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/swarmforge-ultimate.git
cd swarmforge-ultimate

# 2. Set up environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY and OPENROUTER_API_KEY

# 3. Start everything
make setup
make up

# 4. Open the dashboard
open http://localhost
```

---

## API Endpoints

| Method | Path                              | Description               |
|--------|-----------------------------------|---------------------------|
| POST   | `/api/v1/sessions`                | Create new pipeline run   |
| GET    | `/api/v1/sessions`                | List all sessions         |
| GET    | `/api/v1/sessions/{id}`           | Get session details       |
| GET    | `/api/v1/sessions/{id}/blackboard`| Full state snapshot       |
| GET    | `/api/v1/sessions/{id}/files`     | List generated files      |
| GET    | `/api/v1/sessions/{id}/agents`    | Agent statuses (live)     |
| GET    | `/api/v1/sessions/{id}/logs`      | Audit logs                |
| GET    | `/api/v1/sessions/{id}/quality`   | Quality scores            |
| GET    | `/api/v1/sessions/{id}/download`  | Download ZIP              |
| POST   | `/api/v1/sessions/{id}/cancel`    | Cancel pipeline           |
| WS     | `/ws/swarm/{id}`                  | Real-time event stream    |
| GET    | `/api/v1/health`                  | Health check              |
| GET    | `/metrics`                        | Prometheus metrics        |

---

## Dashboard Features

- **Agent Canvas** — React Flow visualization showing all 16 agents with live status
- **Quality Gates** — Real-time progress bars for Build, Test, Security, Performance
- **Radial Score** — Overall quality score with animated ring chart
- **Blackboard** — Browse spec, architecture, generated files, and test results
- **Code Viewer** — Monaco Editor showing generated source with review annotations
- **Live Logs** — Streaming event log with agent-type filtering

---

## Environment Variables

| Variable                | Default                    | Description           |
|------------------------|----------------------------|-----------------------|
| `GROQ_API_KEY`         | (required)                 | Groq API key          |
| `OPENROUTER_API_KEY`   | (required)                 | OpenRouter API key    |
| `DATABASE_URL`         | postgresql+asyncpg://...   | Postgres connection   |
| `REDIS_URL`            | redis://redis:6379/0       | Redis connection      |
| `MAX_ITERATIONS`       | 5                          | Max pipeline loops    |
| `BUILD_GATE_MIN_SCORE` | 80                         | Min code quality      |
| `TEST_GATE_MIN_COVERAGE`| 90                        | Min test coverage %   |
| `SECURITY_GATE_MIN_SCORE`| 85                       | Min security score    |
| `FINAL_GATE_MIN_SCORE` | 85                         | Min overall score     |

---

## Team Members

| Name | Role | GitHub | LinkedIn |
|------|------|--------|----------|
| [Your Name] | Full Stack AI Developer | [@yourgithub](https://github.com/yourgithub) | [LinkedIn](https://linkedin.com/in/yourprofile) |
| [Member 2] | AI Engineer / Prompt Engineering | [@member2](https://github.com/member2) | [LinkedIn](https://linkedin.com/in/member2) |
| [Member 3] | UX/UI Designer & Frontend | [@member3](https://github.com/member3) | [LinkedIn](https://linkedin.com/in/member3) |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

Built with ❤️ by the SwarmForge team. Powered by open-source AI.
