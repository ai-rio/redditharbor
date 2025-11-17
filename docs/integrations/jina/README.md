# Jina Reader API Integration

Jina Reader API provides real-world market data validation for AI-generated monetization insights.

## Overview

Jina Reader API is used to:
- Fetch competitor pricing data from product websites
- Validate market size estimates with industry reports
- Extract product launch metrics from Product Hunt
- Transform opinion-based LLM analysis into data-driven validation

## Documentation

- [Market Validation Implementation](./market-validation-implementation.md) - Complete Reader API integration guide
- [Data-Driven Validation Plan](./data-driven-monetization-validation-plan.md) - Architecture and design decisions
- [Persistency Analysis](./market-validation-persistency-analysis.md) - Database schema and storage patterns

## Key Features

### Market Data Validation
- **Competitor Pricing**: Extract real pricing from competitor websites
- **Market Size**: Validate TAM/SAM/SOM estimates with industry data
- **Product Launch Success**: Fetch metrics from Product Hunt launches
- **Data Quality Scoring**: Confidence scores for each data source

## Architecture

```
Jina Reader API Client
├── JinaReaderClient (agent_tools/jina_reader_client.py)
│   ├── read_url() - Fetch and parse web content
│   ├── extract_pricing() - Parse pricing structures
│   └── validate_market_data() - Cross-reference market claims
│
└── MarketDataValidator (agent_tools/market_data_validator.py)
    ├── validate_competitor_pricing()
    ├── validate_market_size()
    └── calculate_data_quality_score()
```

## Implementation

### Client Setup
**File**: `agent_tools/jina_reader_client.py`

```python
import httpx

class JinaReaderClient:
    def __init__(self):
        self.api_key = os.environ.get("JINA_API_KEY")
        self.base_url = "https://r.jina.ai/"

    async def read_url(self, url: str) -> dict:
        """Fetch and parse web content via Jina Reader API"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}{url}", headers=headers)
            return response.json()
```

### Market Validator
**File**: `agent_tools/market_data_validator.py`

```python
class MarketDataValidator:
    def __init__(self, jina_client: JinaReaderClient):
        self.jina = jina_client

    async def validate_pricing(self, competitor_urls: list) -> dict:
        """Validate pricing claims with real competitor data"""
        pricing_data = []
        for url in competitor_urls:
            content = await self.jina.read_url(url)
            pricing = self.extract_pricing_from_content(content)
            pricing_data.append(pricing)
        return self.aggregate_pricing_data(pricing_data)
```

## Data Flow

1. **Agno Analysis** → Generates monetization evidence with price estimates
2. **Jina Validation** → Fetches real competitor pricing and market data
3. **Evidence Scoring** → Calculates alignment between LLM estimates and real data
4. **Database Storage** → Persists validated evidence with source citations

## Configuration

```bash
# .env
JINA_API_KEY=jina_your_key_here
```

```python
# config/settings.py
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")
JINA_RATE_LIMIT = 10  # requests per minute
JINA_TIMEOUT = 30     # seconds
```

## Database Schema

Market validation data is stored in Supabase:
- `market_validation_results` table
- Source citations with URLs
- Data quality scores
- Timestamp tracking for freshness

See [Persistency Analysis](./market-validation-persistency-analysis.md) for full schema details.

## Testing

```bash
# Unit tests
pytest tests/test_jina_reader_client.py
pytest tests/test_market_data_validator_edge_cases.py

# Integration tests
python test_jina_api_live.py
python test_market_validation_integration.py
```

## Related Documentation

- [Agno Integration](../agno/) - Source of monetization evidence
- [AgentOps Integration](../agentops/) - Cost tracking for API calls
