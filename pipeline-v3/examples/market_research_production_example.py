#!/usr/bin/env python3
"""
MarketResearchAgent Production Readiness Example

This example demonstrates a complete production-ready implementation of the
MarketResearchAgent with all Phase 3.7 production readiness features:

- Comprehensive monitoring and observability
- Circuit breakers and resilience patterns
- Health checks and metrics
- Security and PII anonymization
- Cost tracking and budget management
- Error handling and dead letter queues
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import production-ready components
from transform.market_research_agent import MarketResearchAgent
from transform.market_research_monitoring import get_monitor
from transform.market_research_resilience import get_resilience_manager, resilient
from transform.market_research_security import get_security_manager
from transform.market_research_health import HealthCheckService, run_health_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionMarketResearchService:
    """
    Production-ready Market Research Service

    Integrates all production readiness components into a cohesive service
    with proper error handling, monitoring, and security.
    """

    def __init__(self):
        # Initialize core components
        self.monitor = get_monitor()
        self.resilience_manager = get_resilience_manager()
        self.security_manager = get_security_manager()
        self.health_service = HealthCheckService()

        # Initialize the agent with production configuration
        self.agent = None
        self._initialized = False

        # Service metrics
        self.start_time = datetime.now()
        self.total_requests = 0
        self.successful_requests = 0

        logger.info("ProductionMarketResearchService initialized")

    async def initialize(self):
        """Initialize the service and all components"""
        try:
            # Get production settings
            settings = self._get_production_settings()

            # Initialize MarketResearchAgent with production features
            self.agent = MarketResearchAgent(
                model=settings.get('llm_model', 'anthropic/claude-haiku-4.5'),
                api_key=settings.get('llm_api_key'),
                jina_api_key=settings.get('jina_api_key'),
                validation_threshold=settings.get('validation_threshold', 70.0),
                max_competitors=settings.get('max_competitors', 5),
                max_launches=settings.get('max_launches', 3),
                enable_cost_tracking=settings.get('enable_cost_tracking', True),
                use_real_jina=settings.get('use_real_jina', False)  # Set to True for production
            )

            # Initialize monitoring
            await self._setup_monitoring()

            # Initialize security
            await self._setup_security()

            self._initialized = True
            logger.info("ProductionMarketResearchService successfully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize service: {e}")
            raise

    def _get_production_settings(self) -> Dict[str, Any]:
        """Get production configuration from environment"""
        return {
            # API Configuration
            'llm_model': os.getenv('LLM_MODEL', 'anthropic/claude-haiku-4.5'),
            'llm_api_key': os.getenv('JINA_LLM_API_KEY'),
            'jina_api_key': os.getenv('JINA_API_KEY'),

            # Market Research Settings
            'validation_threshold': float(os.getenv('MARKET_RESEARCH_VALIDATION_THRESHOLD', '70.0')),
            'max_competitors': int(os.getenv('MARKET_RESEARCH_MAX_COMPETITORS', '5')),
            'max_launches': int(os.getenv('MARKET_RESEARCH_MAX_LAUNCHES', '3')),

            # Cost and Performance
            'enable_cost_tracking': os.getenv('COST_TRACKING_ENABLED', 'true').lower() == 'true',
            'daily_budget_usd': float(os.getenv('MONTHLY_JINA_BUDGET_USD', '500.0')) / 30,  # Daily budget

            # Production Features
            'use_real_jina': os.getenv('APP_ENV') == 'production',
            'enable_pii_anonymization': os.getenv('ENABLE_PII_ANONYMIZATION', 'true').lower() == 'true'
        }

    async def _setup_monitoring(self):
        """Setup monitoring and metrics collection"""
        # Configure custom retry policies
        self.resilience_manager.set_retry_policy(
            'MarketResearchAgent',
            'run_validation',
            self.resilience_manager.retry_policies.get('default')
        )

        logger.info("Monitoring configured")

    async def _setup_security(self):
        """Setup security and API key management"""
        # Generate initial API key if none exists
        if not self.security_manager.api_key_manager.api_keys:
            api_key, key_id = self.security_manager.api_key_manager.generate_api_key(
                name="Production API Key",
                permissions=["market_research:read", "market_research:write"],
                expires_days=90,
                rate_limit=60
            )
            logger.info(f"Generated production API key: {key_id}")
            logger.info(f"API Key (save securely): {api_key}")

        logger.info("Security configured")

    @resilient('MarketResearchAgent', 'process_request', max_attempts=3)
    async def process_market_research_request(
        self,
        request_data: Dict[str, Any],
        api_key: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process market research request with full production safeguards

        Args:
            request_data: Market research request data
            api_key: API key for authentication
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Market research results with metadata
        """
        start_time = time.time()
        self.total_requests += 1

        try:
            # 1. Authenticate request
            security_context = self.security_manager.authenticate_request(
                api_key=api_key,
                ip_address=ip_address,
                user_agent=user_agent
            )

            if not security_context:
                raise PermissionError("Invalid API key")

            # 2. Authorize operation
            if not self.security_manager.authorize_operation(
                security_context,
                'market_research:execute'
            ):
                raise PermissionError("Insufficient permissions")

            # 3. Process sensitive data (PII anonymization)
            processed_request_data, pii_detected = self.security_manager.process_sensitive_data(
                data=request_data,
                operation="market_research_validation",
                security_context=security_context
            )

            # 4. Execute market research with monitoring
            async with self.monitor:
                # Record API access
                self.security_manager.audit_logger.log_api_access(
                    endpoint="/market-research/validate",
                    method="POST",
                    status_code=200,  # Will update based on result
                    response_time_ms=0,  # Will update after execution
                    security_context=security_context,
                    request_details={
                        'pii_detected': pii_detected,
                        'request_size': len(json.dumps(request_data))
                    }
                )

                # Execute market research
                result = await self.agent.run(processed_request_data)

                # Add production metadata
                result['metadata'] = {
                    'request_id': security_context.additional_claims.get('request_id'),
                    'timestamp': datetime.now().isoformat(),
                    'processing_time_ms': round((time.time() - start_time) * 1000, 2),
                    'pii_anonymized': pii_detected,
                    'cost_tracking_enabled': self.agent.enable_cost_tracking
                }

                # Update audit log with success
                self.security_manager.audit_logger.log_data_access(
                    operation="market_research_validation",
                    resource_type="market_opportunity",
                    security_context=security_context,
                    pii_detected=pii_detected
                )

                self.successful_requests += 1

                # Log success with monitoring
                logger.info(
                    f"Market research completed successfully - "
                    f"Score: {result.get('validation_score', 0):.1f}, "
                    f"Cost: ${result.get('jina_cost', 0):.4f}, "
                    f"Time: {result['metadata']['processing_time_ms']}ms"
                )

                return result

        except Exception as e:
            # Log error with monitoring
            logger.error(f"Market research request failed: {e}")

            # Add to dead letter queue if appropriate
            error_info = self.resilience_manager.error_handler.classify_error(
                e,
                "process_market_research_request",
                "MarketResearchAgent"
            )

            await self.resilience_manager.dead_letter_queue.add_failed_request(
                request_data=request_data,
                error_info=error_info
            )

            raise

    async def get_service_health(self) -> Dict[str, Any]:
        """Get comprehensive service health status"""
        if not self._initialized:
            return {
                'healthy': False,
                'error': 'Service not initialized'
            }

        # Get health from health service
        health_result, status_code = await self.health_service.check_health(detailed=True)

        # Add service-specific metrics
        health_result.update({
            'service_metrics': {
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'success_rate': (
                    (self.successful_requests / self.total_requests * 100)
                    if self.total_requests > 0 else 0
                )
            },
            'monitoring': await self.monitor.get_health_status(),
            'security': self.security_manager.get_security_stats(),
            'resilience': self.resilience_manager.get_resilience_stats()
        })

        return health_result

    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics"""
        if not self._initialized:
            return {'error': 'Service not initialized'}

        return {
            'performance': await self.monitor.get_daily_report(),
            'costs': {
                'total_cost_usd': self.agent.get_cost_summary()['total_cost'],
                'daily_budget_remaining_usd': max(
                    0,
                    self._get_production_settings()['daily_budget_usd'] -
                    self.agent.get_cost_summary()['total_cost']
                )
            },
            'agent_stats': self.agent.get_cost_summary(),
            'monitoring_stats': {
                'response_times': list(self.monitor.response_times),
                'error_counts': dict(self.monitor.error_counts),
                'operation_counts': dict(self.monitor.operation_counts)
            }
        }

    async def process_dead_letter_queue(self):
        """Process failed requests from dead letter queue"""
        logger.info("Processing dead letter queue...")

        retryable_requests = await self.resilience_manager.dead_letter_queue.get_retryable_requests()

        if not retryable_requests:
            logger.info("No retryable requests in DLQ")
            return

        logger.info(f"Processing {len(retryable_requests)} retryable requests")

        for entry in retryable_requests:
            try:
                request_data = entry['request_data']
                logger.info(f"Retrying request: {request_data}")

                # Process with minimal security context for retry
                result = await self.agent.run(request_data)
                logger.info("Successfully retried failed request")

            except Exception as e:
                logger.error(f"Failed to retry request: {e}")

    async def cleanup(self):
        """Cleanup resources and shutdown gracefully"""
        logger.info("Shutting down ProductionMarketResearchService...")

        if self.agent:
            await self.agent.close()

        if self.monitor:
            await self.monitor.close()

        logger.info("ProductionMarketResearchService shutdown complete")


async def main():
    """
    Main function demonstrating production deployment
    """
    logger.info("Starting MarketResearchAgent Production Example")

    # Create service instance
    service = ProductionMarketResearchService()

    try:
        # Initialize the service
        await service.initialize()

        # Generate API key for testing
        test_api_key, key_id = service.security_manager.api_key_manager.generate_api_key(
            name="Test API Key",
            permissions=["market_research:execute"],
            rate_limit=30
        )

        logger.info(f"Generated test API key: {key_id}")
        logger.info(f"Test API Key: {test_api_key}")

        # Example market research requests
        test_requests = [
            {
                "app_concept": "AI-powered meal planning app for busy professionals",
                "target_market": "Health-conscious professionals aged 25-45",
                "problem_description": "Busy professionals struggle to maintain healthy eating habits due to time constraints"
            },
            {
                "app_concept": "Sustainable fashion marketplace for eco-conscious consumers",
                "target_market": "Environmentally aware millennials",
                "problem_description": "Fast fashion environmental impact and lack of sustainable alternatives"
            },
            {
                "app_concept": "Mental wellness app using AI for personalized therapy",
                "target_market": "Young adults experiencing anxiety and stress",
                "problem_description": "High cost and stigma associated with traditional mental health services"
            }
        ]

        # Process test requests
        logger.info("Processing test market research requests...")

        for i, request_data in enumerate(test_requests):
            try:
                logger.info(f"\n--- Processing Request {i+1} ---")
                logger.info(f"Concept: {request_data['app_concept']}")

                # Process with full production safeguards
                result = await service.process_market_research_request(
                    request_data=request_data,
                    api_key=test_api_key,
                    ip_address="127.0.0.1",
                    user_agent="Production Example Bot"
                )

                # Display results
                logger.info(f"Validation Score: {result['validation_score']:.1f}")
                logger.info(f"Data Quality Score: {result['data_quality_score']:.1f}")
                logger.info(f"Competitors Found: {len(result['competitor_pricing'])}")
                logger.info(f"Processing Time: {result['metadata']['processing_time_ms']}ms")
                logger.info(f"Cost: ${result.get('jina_cost', 0):.4f}")

                # Display reasoning
                logger.info(f"Reasoning: {result['reasoning']}")

                # Add delay between requests
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Failed to process request {i+1}: {e}")

        # Display service health
        logger.info("\n--- Service Health ---")
        health = await service.get_service_health()
        logger.info(f"Overall Health: {'✅' if health['healthy'] else '❌'}")
        logger.info(f"Total Requests: {health['service_metrics']['total_requests']}")
        logger.info(f"Success Rate: {health['service_metrics']['success_rate']:.1f}%")
        logger.info(f"Uptime: {health['service_metrics']['uptime_seconds']:.0f} seconds")

        # Display service metrics
        logger.info("\n--- Service Metrics ---")
        metrics = await service.get_service_metrics()
        logger.info(f"Total Cost: ${metrics['costs']['total_cost_usd']:.4f}")
        logger.info(f"Budget Remaining: ${metrics['costs']['daily_budget_remaining_usd']:.2f}")

        # Process dead letter queue (if any)
        await service.process_dead_letter_queue()

        # Display final statistics
        logger.info("\n--- Final Statistics ---")
        agent_stats = service.agent.get_cost_summary()
        logger.info(f"Agent Validations: {agent_stats['validation_count']}")
        logger.info(f"Agent Total Cost: ${agent_stats['total_cost']:.4f}")
        logger.info(f"Average Cost per Validation: ${agent_stats['average_cost_per_validation']:.4f}")

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")

    except Exception as e:
        logger.error(f"Service error: {e}")

    finally:
        # Cleanup
        await service.cleanup()


async def health_server_example():
    """Example of running health check server"""
    logger.info("Starting Health Check Server Example")

    # Run health server on port 8080
    run_health_server(
        host="0.0.0.0",
        port=8080,
        use_fastapi=True,  # Use FastAPI if available
        log_level="info"
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "health-server":
        # Run health check server
        asyncio.run(health_server_example())
    else:
        # Run production example
        asyncio.run(main())