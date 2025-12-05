# Embedding Provider Configuration Guide

**Version:** 1.0
**Date:** 2025-12-05
**Target:** RedditHarbor Pipeline v3

## Overview

This guide provides configuration examples and best practices for integrating new embedding providers into RedditHarbor's embedding pipeline.

## Environment Variables

Add the following to your `.env` file:

```bash
# OpenAI (existing)
OPENAI_API_KEY=your_openai_api_key_here

# Cohere AI
COHERE_API_KEY=your_cohere_api_key_here

# Voyage AI
VOYAGE_API_KEY=your_voyage_api_key_here

# Jina AI
JINA_API_KEY=your_jina_api_key_here

# Google Vertex AI
GOOGLE_PROJECT_ID=your_google_cloud_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

## Provider Configuration Examples

### 1. Basic Provider Setup

```python
from pipeline_v3.transform.embedding_factory import EmbeddingFactory

# Cohere (Recommended for Production)
cohere_strategy = EmbeddingFactory.create_provider(
    provider_type="cohere",
    model="embed-english-v3.0",
    dimensions=1024
)

# Voyage AI (Cost-Effective Alternative)
voyage_strategy = EmbeddingFactory.create_provider(
    provider_type="voyage",
    model="voyage-large-2",
    dimensions=1536
)

# Jina AI (Async Support)
jina_strategy = EmbeddingFactory.create_provider(
    provider_type="jina",
    model="jina-embeddings-v3",
    dimensions=1024
)

# Google Vertex AI (Enterprise)
vertexai_strategy = EmbeddingFactory.create_provider(
    provider_type="vertexai",
    model="textembedding-gecko@003",
    dimensions=768,
    api_key="your-project-id"  # Pass project ID
)
```

### 2. Provider with Fallback

```python
# Primary: Cohere, Fallback: Voyage AI
cohere_with_fallback = EmbeddingFactory.create_provider(
    provider_type="cohere",
    model="embed-english-v3.0",
    dimensions=1024,
    fallback_provider="voyage"
)

# Primary: Voyage AI, Fallback: Local
voyage_with_fallback = EmbeddingFactory.create_provider(
    provider_type="voyage",
    model="voyage-large-2",
    dimensions=1536,
    fallback_provider="local"
)
```

### 3. Dynamic Provider Selection

```python
import os
from pipeline_v3.transform.embedding_factory import EmbeddingFactory

def get_embedding_strategy():
    """Select embedding strategy based on environment"""

    # Production: Use Cohere with Voyage fallback
    if os.getenv('ENVIRONMENT') == 'production':
        return EmbeddingFactory.create_provider(
            provider_type="cohere",
            fallback_provider="voyage"
        )

    # Development: Use local for free testing
    elif os.getenv('ENVIRONMENT') == 'development':
        return EmbeddingFactory.create_provider(
            provider_type="local",
            fallback_provider="fake"
        )

    # Default: Voyage AI for cost efficiency
    else:
        return EmbeddingFactory.create_provider(
            provider_type="voyage",
            fallback_provider="local"
        )

# Usage
strategy = get_embedding_strategy()
embedding, metadata = strategy.generate_embedding("Reddit post content")
```

## Model Selection Guide

### Cohere Models
- `embed-english-v3.0`: 1024 dimensions, balanced performance
- `embed-multilingual-v3.0`: 1024 dimensions, supports 100+ languages
- `embed-english-light-v3.0`: 384 dimensions, faster processing

### Voyage AI Models
- `voyage-large-2`: 1536 dimensions, best quality
- `voyage-code-2`: 1536 dimensions, optimized for code
- `voyage-law-2`: 1536 dimensions, legal documents

### Jina AI Models
- `jina-embeddings-v3`: 1024 dimensions, general purpose
- `jina-embeddings-v2-base-en`: 768 dimensions, English only
- `jina-embeddings-v2-base-zh`: 768 dimensions, Chinese

### Google Vertex AI Models
- `textembedding-gecko@003`: 768 dimensions, general purpose
- `textembedding-gecko-multilingual@001`: 768 dimensions, multilingual

## Performance Optimization

### 1. Batch Processing

```python
import concurrent.futures
from typing import List

def process_batch_texts(texts: List[str], strategy):
    """Process multiple texts efficiently"""

    def generate_embedding(text):
        return strategy.generate_embedding(text)

    # Use ThreadPoolExecutor for concurrent processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(generate_embedding, texts))

    return results

# Example usage
texts = ["Reddit post 1", "Reddit post 2", "Reddit post 3"]
results = process_batch_texts(texts, strategy)
```

### 2. Provider Pooling

```python
from pipeline_v3.transform.embedding_factory import EmbeddingFactory

class EmbeddingPool:
    """Pool of embedding providers for load balancing"""

    def __init__(self, provider_configs):
        self.providers = []
        self.current_index = 0

        for config in provider_configs:
            provider = EmbeddingFactory.create_provider(**config)
            self.providers.append(provider)

    def get_embedding(self, text):
        """Get embedding using round-robin provider selection"""
        provider = self.providers[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.providers)

        try:
            return provider.generate_embedding(text)
        except Exception as e:
            # Try next provider if current fails
            logger.warning(f"Provider failed: {e}, trying next")
            next_provider = self.providers[(self.current_index + 1) % len(self.providers)]
            return next_provider.generate_embedding(text)

# Configuration for pool
pool_configs = [
    {"provider_type": "cohere", "model": "embed-english-v3.0"},
    {"provider_type": "voyage", "model": "voyage-large-2"},
    {"provider_type": "jina", "model": "jina-embeddings-v3"}
]

pool = EmbeddingPool(pool_configs)
```

### 3. Adaptive Provider Selection

```python
import time
from collections import defaultdict

class AdaptiveEmbeddingManager:
    """Adaptive provider selection based on performance"""

    def __init__(self):
        self.providers = {}
        self.metrics = defaultdict(lambda: {'latency': [], 'errors': 0})

    def add_provider(self, name, strategy):
        self.providers[name] = strategy

    def get_best_provider(self):
        """Select provider with best performance"""
        best_provider = None
        best_score = float('inf')

        for name, metrics in self.metrics.items():
            if metrics['errors'] > 10:  # Skip unreliable providers
                continue

            avg_latency = sum(metrics['latency']) / len(metrics['latency'])
            score = avg_latency * (1 + metrics['errors'] * 0.1)  # Penalize errors

            if score < best_score:
                best_score = score
                best_provider = name

        return self.providers.get(best_provider)

    def generate_embedding(self, text):
        """Generate embedding with performance tracking"""
        provider = self.get_best_provider() or list(self.providers.values())[0]

        start_time = time.time()
        try:
            embedding, metadata = provider.generate_embedding(text)
            latency = time.time() - start_time

            # Update metrics
            provider_name = provider.primary_provider.get_provider_info()['provider']
            self.metrics[provider_name]['latency'].append(latency)

            # Keep only last 100 measurements
            if len(self.metrics[provider_name]['latency']) > 100:
                self.metrics[provider_name]['latency'].pop(0)

            return embedding, metadata

        except Exception as e:
            # Track error
            provider_name = provider.primary_provider.get_provider_info()['provider']
            self.metrics[provider_name]['errors'] += 1
            raise

# Usage
manager = AdaptiveEmbeddingManager()
manager.add_provider("cohere", cohere_strategy)
manager.add_provider("voyage", voyage_strategy)
```

## Monitoring and Observability

### 1. Basic Metrics Collection

```python
import json
from datetime import datetime

class EmbeddingMetrics:
    """Collect and track embedding metrics"""

    def __init__(self, log_file='embedding_metrics.json'):
        self.log_file = log_file
        self.metrics = []

    def log_request(self, provider, latency, success, dimensions, text_length):
        """Log embedding request metrics"""
        metric = {
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'latency_ms': round(latency * 1000, 2),
            'success': success,
            'dimensions': dimensions,
            'text_length': text_length
        }

        self.metrics.append(metric)

        # Keep only last 1000 entries
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

        # Append to file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(metric) + '\n')

    def get_summary(self, provider=None):
        """Get performance summary"""
        filtered = self.metrics
        if provider:
            filtered = [m for m in filtered if m['provider'] == provider]

        if not filtered:
            return {}

        latencies = [m['latency_ms'] for m in filtered]
        success_rate = sum(1 for m in filtered if m['success']) / len(filtered)

        return {
            'total_requests': len(filtered),
            'success_rate': round(success_rate * 100, 2),
            'avg_latency': round(sum(latencies) / len(latencies), 2),
            'p95_latency': round(sorted(latencies)[int(len(latencies) * 0.95)], 2),
            'p99_latency': round(sorted(latencies)[int(len(latencies) * 0.99)], 2)
        }

# Wrap provider for metrics
class MetricsWrapper:
    """Wrap embedding strategy with metrics collection"""

    def __init__(self, strategy, metrics_collector):
        self.strategy = strategy
        self.metrics = metrics_collector

    def generate_embedding(self, text, metadata=None):
        provider_info = self.strategy.primary_provider.get_provider_info()
        provider = provider_info['provider']

        start_time = time.time()
        try:
            embedding, result_metadata = self.strategy.generate_embedding(text, metadata)
            latency = time.time() - start_time

            self.metrics.log_request(
                provider=provider,
                latency=latency,
                success=True,
                dimensions=len(embedding),
                text_length=len(text)
            )

            return embedding, result_metadata

        except Exception as e:
            latency = time.time() - start_time

            self.metrics.log_request(
                provider=provider,
                latency=latency,
                success=False,
                dimensions=0,
                text_length=len(text)
            )

            raise

# Usage
metrics = EmbeddingMetrics()
wrapped_strategy = MetricsWrapper(strategy, metrics)
```

## Best Practices

### 1. API Key Management
- Store API keys in environment variables
- Rotate keys regularly
- Use different keys for different environments
- Monitor API key usage and costs

### 2. Error Handling
- Always implement fallback providers
- Use exponential backoff for retries
- Log all errors with sufficient context
- Implement circuit breakers for failing providers

### 3. Performance Optimization
- Use batch processing when possible
- Implement connection pooling
- Cache embeddings for repeated texts
- Monitor and optimize based on metrics

### 4. Cost Management
- Track token usage per provider
- Set up usage alerts
- Use cost-effective providers for bulk processing
- Consider hybrid strategies (premium + budget providers)

## Migration Path

### Phase 1: Setup
1. Install required packages:
   ```bash
   pip install cohere voyageai jina-client google-cloud-aiplatform
   ```

2. Configure API keys in environment
3. Test each provider individually

### Phase 2: Integration
1. Update EmbeddingFactory imports
2. Add new provider configurations
3. Implement fallback strategies
4. Add metrics and monitoring

### Phase 3: Production Rollout
1. Start with low traffic
2. Monitor performance and costs
3. Gradually increase usage
4. Optimize based on real data

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all required packages are installed
   - Check Python path includes project root

2. **Authentication Errors**
   - Verify API keys are correct
   - Check environment variable names
   - Ensure proper permissions for cloud providers

3. **Rate Limiting**
   - Implement proper rate limiting
   - Use multiple API keys if needed
   - Consider provider rotation

4. **Performance Issues**
   - Check batch processing implementation
   - Monitor network latency
   - Optimize text preprocessing

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for specific modules
logger = logging.getLogger('pipeline_v3.transform.embedding_providers_new')
logger.setLevel(logging.DEBUG)
```

## Resources

- [Cohere Python SDK Documentation](https://docs.cohere.com/docs/python-sdk)
- [Voyage AI Documentation](https://docs.voyageai.com/)
- [Jina AI Documentation](https://jina.ai/api/embeddings/)
- [Google Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)