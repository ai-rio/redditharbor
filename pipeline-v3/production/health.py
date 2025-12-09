"""
Production health check module

Provides HealthCheckEndpoint class for application health monitoring.
"""

import logging
from datetime import datetime
from typing import Any

# FastAPI is optional for production health checks
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger(__name__)


class HealthCheckEndpoint:
    """
    Health check endpoint for production monitoring

    Provides health status information for the RedditHarbor pipeline,
    including component status, performance metrics, and system health.
    """

    def __init__(self):
        """Initialize health check endpoint"""
        self.start_time = datetime.now()
        self.component_checks = {}
        self._monitor = None

    def add_component_check(self, name: str, check_func):
        """
        Add a component health check function

        Args:
            name: Component name
            check_func: Async function that returns health status
        """
        self.component_checks[name] = check_func

    async def get_health_status(self) -> dict[str, Any]:
        """
        Get comprehensive health status

        Returns:
            Health status dictionary
        """
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "version": "1.0.0",
            "components": {}
        }

        # Check all registered components
        for name, check_func in self.component_checks.items():
            try:
                component_status = await check_func()
                status["components"][name] = component_status

                # Mark unhealthy if any component is unhealthy
                if not component_status.get("healthy", True):
                    status["status"] = "unhealthy"

            except Exception as e:
                logger.error(f"Health check failed for component {name}: {e}")
                status["components"][name] = {
                    "healthy": False,
                    "error": str(e)
                }
                status["status"] = "unhealthy"

        # Try to get monitor status if available
        try:
            from transform.market_research_monitoring import get_monitor
            monitor = get_monitor()
            monitor_status = await monitor.get_health_status()
            status["monitoring"] = monitor_status

            if not monitor_status.get("healthy", True):
                status["status"] = "unhealthy"

        except Exception as e:
            logger.warning(f"Failed to get monitor status: {e}")
            status["monitoring"] = {"healthy": False, "error": str(e)}

        return status

    async def readiness_check(self) -> dict[str, Any]:
        """
        Check if the application is ready to serve traffic

        Returns:
            Readiness status
        """
        health = await self.get_health_status()

        return {
            "ready": health["status"] == "healthy",
            "timestamp": health["timestamp"]
        }

    async def liveness_check(self) -> dict[str, Any]:
        """
        Check if the application is alive

        Returns:
            Liveness status
        """
        return {
            "alive": True,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }

    def create_fastapi_routes(self, app):
        """
        Add health check routes to FastAPI application

        Args:
            app: FastAPI application instance
        """
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available, health check routes not created")
            return

        @app.get("/health", response_class=JSONResponse)
        async def health_check():
            """Main health check endpoint"""
            try:
                status = await self.get_health_status()

                if status["status"] == "healthy":
                    return JSONResponse(
                        content=status,
                        status_code=200
                    )
                else:
                    return JSONResponse(
                        content=status,
                        status_code=503
                    )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JSONResponse(
                    content={
                        "status": "error",
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    },
                    status_code=500
                )

        @app.get("/ready", response_class=JSONResponse)
        async def readiness_check():
            """Readiness check endpoint"""
            try:
                readiness = await self.readiness_check()

                if readiness["ready"]:
                    return JSONResponse(
                        content=readiness,
                        status_code=200
                    )
                else:
                    return JSONResponse(
                        content=readiness,
                        status_code=503
                    )
            except Exception as e:
                logger.error(f"Readiness check failed: {e}")
                return JSONResponse(
                    content={
                        "ready": False,
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    },
                    status_code=500
                )

        @app.get("/live", response_class=JSONResponse)
        async def liveness_check():
            """Liveness check endpoint"""
            try:
                liveness = await self.liveness_check()
                return JSONResponse(
                    content=liveness,
                    status_code=200
                )
            except Exception as e:
                logger.error(f"Liveness check failed: {e}")
                return JSONResponse(
                    content={
                        "alive": False,
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    },
                    status_code=500
                )


__all__ = ['HealthCheckEndpoint']
