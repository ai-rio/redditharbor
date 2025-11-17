# External Integrations Documentation

This directory contains documentation for third-party service integrations used in RedditHarbor's AI-powered analysis pipeline.

## Integration Overview

| Integration | Purpose | Status |
|------------|---------|--------|
| [Agno](./agno/) | Multi-agent LLM framework for monetization analysis | Production |
| [AgentOps](./agentops/) | AI agent observability and cost tracking | Production |
| [Jina](./jina/) | Reader API for real market data validation | Production |

## Architecture

```
Reddit Data → Agno Multi-Agent Analysis → AgentOps Tracking → Jina Market Validation
     ↓                    ↓                       ↓                      ↓
  Raw posts        Evidence generation      Cost monitoring      Real-world validation
```

## Quick Links

### Agno (Multi-Agent Framework)
- [Migration Guide](./agno/migration-guide.md) - DSPy to Agno migration

### AgentOps (Observability)
- [Evidence Integration Summary](./agentops/evidence-integration-summary.md) - SDK instrumentation and cost tracking

### Jina (Market Validation)
- [Market Validation Implementation](./jina/market-validation-implementation.md) - Reader API integration
- [Data-Driven Validation Plan](./jina/data-driven-monetization-validation-plan.md) - Architecture and design
- [Persistency Analysis](./jina/market-validation-persistency-analysis.md) - Database schema and storage

## Integration Dependencies

```bash
# Core dependencies (pyproject.toml)
agno>=2.2.13          # Multi-agent framework
agentops>=0.4.0       # Agent observability
httpx>=0.27.0         # Jina API client (async HTTP)
```

## Configuration

All integrations are configured via environment variables in `.env`:

```bash
# Agno (uses OpenRouter)
OPENROUTER_API_KEY=sk-or-...

# AgentOps
AGENTOPS_API_KEY=...

# Jina Reader API
JINA_API_KEY=jina_...
```

See `config/settings.py` for detailed configuration options.
