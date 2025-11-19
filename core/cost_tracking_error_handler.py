#!/usr/bin/env python3
"""
Cost Tracking Error Handler
Comprehensive error handling and recovery for LLM cost tracking operations
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CostTrackingError(Exception):
    """Base exception for cost tracking errors"""
    pass


class CostValidationError(CostTrackingError):
    """Exception raised when cost data validation fails"""
    pass


class CostDataCorruptionError(CostTrackingError):
    """Exception raised when cost data is corrupted or inconsistent"""
    pass


class CostThresholdExceededError(CostTrackingError):
    """Exception raised when cost limits are exceeded"""
    pass


class CostTrackingErrorHandler:
    """
    Comprehensive error handling for cost tracking operations.
    Provides validation, recovery, and monitoring capabilities.
    """

    def __init__(self, cost_threshold_usd: float = 10.0):
        """
        Initialize the error handler.

        Args:
            cost_threshold_usd: Maximum allowed cost per batch
        """
        self.cost_threshold_usd = cost_threshold_usd
        self.error_log: list[dict[str, Any]] = []
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3

    def validate_cost_data(self, cost_data: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate cost tracking data for consistency and completeness.

        Args:
            cost_data: Cost tracking dictionary from LLM profiler

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        required_fields = [
            'model_used', 'provider', 'prompt_tokens', 'completion_tokens',
            'total_tokens', 'input_cost_usd', 'output_cost_usd',
            'total_cost_usd', 'latency_seconds', 'timestamp'
        ]

        for field in required_fields:
            if field not in cost_data:
                errors.append(f"Missing required field: {field}")

        # Validate data types and ranges
        if 'total_tokens' in cost_data:
            try:
                total_tokens = int(cost_data['total_tokens'])
                if total_tokens < 0:
                    errors.append("Total tokens cannot be negative")
                if total_tokens > 100000:  # Sanity check
                    errors.append(f"Total tokens unexpectedly high: {total_tokens}")
            except (ValueError, TypeError):
                errors.append(f"Invalid total_tokens value: {cost_data['total_tokens']}")

        if 'total_cost_usd' in cost_data:
            try:
                total_cost = float(cost_data['total_cost_usd'])
                if total_cost < 0:
                    errors.append("Total cost cannot be negative")
                if total_cost > 100.0:  # Sanity check
                    errors.append(f"Total cost unexpectedly high: ${total_cost}")
            except (ValueError, TypeError):
                errors.append(f"Invalid total_cost_usd value: {cost_data['total_cost_usd']}")

        # Validate token consistency
        if all(field in cost_data for field in ['prompt_tokens', 'completion_tokens', 'total_tokens']):
            try:
                prompt_tokens = int(cost_data['prompt_tokens'])
                completion_tokens = int(cost_data['completion_tokens'])
                total_tokens = int(cost_data['total_tokens'])

                calculated_total = prompt_tokens + completion_tokens
                if calculated_total != total_tokens:
                    errors.append(
                        f"Token count mismatch: prompt({prompt_tokens}) + completion({completion_tokens}) "
                        f"!= total({total_tokens})"
                    )
            except (ValueError, TypeError):
                errors.append("Invalid token values in cost data")

        # Validate cost consistency
        if all(field in cost_data for field in ['input_cost_usd', 'output_cost_usd', 'total_cost_usd']):
            try:
                input_cost = float(cost_data['input_cost_usd'])
                output_cost = float(cost_data['output_cost_usd'])
                total_cost = float(cost_data['total_cost_usd'])

                calculated_total = input_cost + output_cost
                # Allow small floating point differences
                if abs(calculated_total - total_cost) > 0.000001:
                    errors.append(
                        f"Cost calculation mismatch: input(${input_cost}) + output(${output_cost}) "
                        f"!= total(${total_cost})"
                    )
            except (ValueError, TypeError):
                errors.append("Invalid cost values in cost data")

        # Validate timestamp
        if 'timestamp' in cost_data:
            timestamp = cost_data['timestamp']
            try:
                parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                # Check if timestamp is reasonable (not too old or future)
                now = datetime.utcnow()
                if parsed_time > now:
                    errors.append("Timestamp is in the future")
                elif (now - parsed_time).days > 7:
                    errors.append("Timestamp is more than 7 days old")
            except (ValueError, TypeError):
                errors.append(f"Invalid timestamp format: {timestamp}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_batch_costs(self, opportunities: list[dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
        """
        Validate costs for a batch of opportunities.

        Args:
            opportunities: List of opportunity dictionaries with cost data

        Returns:
            Tuple of (is_valid, validation_summary)
        """
        total_cost = 0.0
        total_tokens = 0
        valid_opportunities = 0
        validation_errors = []

        for i, opp in enumerate(opportunities):
            cost_data = opp.get('cost_tracking', {})

            if not cost_data:
                validation_errors.append(f"Opportunity {i}: No cost data found")
                continue

            is_valid, errors = self.validate_cost_data(cost_data)

            if is_valid:
                total_cost += cost_data.get('total_cost_usd', 0.0)
                total_tokens += cost_data.get('total_tokens', 0)
                valid_opportunities += 1
            else:
                validation_errors.extend([f"Opportunity {i}: {error}" for error in errors])

        # Check cost threshold
        exceeds_threshold = total_cost > self.cost_threshold_usd
        if exceeds_threshold:
            validation_errors.append(
                f"Batch cost ${total_cost:.6f} exceeds threshold ${self.cost_threshold_usd:.6f}"
            )

        summary = {
            'total_opportunities': len(opportunities),
            'valid_opportunities': valid_opportunities,
            'total_cost_usd': total_cost,
            'total_tokens': total_tokens,
            'exceeds_threshold': exceeds_threshold,
            'validation_errors': validation_errors
        }

        is_valid = valid_opportunities == len(opportunities) and not exceeds_threshold
        return is_valid, summary

    def sanitize_cost_data(self, cost_data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize and repair cost data if possible.

        Args:
            cost_data: Raw cost data that may have issues

        Returns:
            Sanitized cost data
        """
        sanitized = cost_data.copy()

        # Ensure numeric fields are properly typed
        numeric_fields = [
            'prompt_tokens', 'completion_tokens', 'total_tokens',
            'input_cost_usd', 'output_cost_usd', 'total_cost_usd',
            'latency_seconds'
        ]

        for field in numeric_fields:
            if field in sanitized:
                try:
                    sanitized[field] = float(sanitized[field]) if 'cost' in field or 'latency' in field else int(sanitized[field])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {field}, setting to 0")
                    sanitized[field] = 0

        # Recalculate totals if inconsistent
        if all(field in sanitized for field in ['prompt_tokens', 'completion_tokens']):
            calculated_total = sanitized['prompt_tokens'] + sanitized['completion_tokens']
            if 'total_tokens' not in sanitized or sanitized['total_tokens'] != calculated_total:
                logger.warning("Recalculating total_tokens from prompt and completion tokens")
                sanitized['total_tokens'] = calculated_total

        if all(field in sanitized for field in ['input_cost_usd', 'output_cost_usd']):
            calculated_total = sanitized['input_cost_usd'] + sanitized['output_cost_usd']
            if 'total_cost_usd' not in sanitized or abs(sanitized['total_cost_usd'] - calculated_total) > 0.000001:
                logger.warning("Recalculating total_cost_usd from input and output costs")
                sanitized['total_cost_usd'] = round(calculated_total, 6)

        # Ensure timestamp is valid
        if 'timestamp' not in sanitized:
            sanitized['timestamp'] = datetime.utcnow().isoformat()

        return sanitized

    def handle_cost_error(
        self,
        error: Exception,
        opportunities: list[dict[str, Any]],
        context: dict[str, Any] = None
    ) -> tuple[bool, list[dict[str, Any]]]:
        """
        Handle cost tracking errors with recovery attempts.

        Args:
            error: The exception that occurred
            opportunities: List of opportunities being processed
            context: Additional context about the error

        Returns:
            Tuple of (should_retry, recovered_opportunities)
        """
        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'opportunity_count': len(opportunities),
            'recovery_attempt': self.recovery_attempts,
            'context': context or {}
        }

        self.error_log.append(error_info)
        logger.error(f"Cost tracking error: {error_info}")

        if self.recovery_attempts >= self.max_recovery_attempts:
            logger.error("Max recovery attempts reached, giving up")
            return False, []

        self.recovery_attempts += 1

        # Recovery strategies based on error type
        if isinstance(error, CostValidationError):
            return self._handle_validation_error(opportunities)
        elif isinstance(error, CostDataCorruptionError):
            return self._handle_corruption_error(opportunities)
        elif isinstance(error, CostThresholdExceededError):
            return self._handle_threshold_error(opportunities)
        else:
            return self._handle_generic_error(opportunities)

    def _handle_validation_error(self, opportunities: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
        """Handle validation errors by attempting to sanitize data"""
        logger.info("Attempting to recover from validation error by sanitizing data")

        recovered_opportunities = []
        for opp in opportunities:
            if 'cost_tracking' in opp:
                try:
                    sanitized_cost = self.sanitize_cost_data(opp['cost_tracking'])
                    is_valid, errors = self.validate_cost_data(sanitized_cost)

                    if is_valid:
                        opp['cost_tracking'] = sanitized_cost
                        recovered_opportunities.append(opp)
                    else:
                        logger.warning(f"Could not recover cost data for opportunity {opp.get('opportunity_id', 'unknown')}: {errors}")
                        # Remove cost data but keep the opportunity
                        opp_without_cost = opp.copy()
                        opp_without_cost.pop('cost_tracking', None)
                        recovered_opportunities.append(opp_without_cost)
                except Exception as e:
                    logger.error(f"Failed to sanitize cost data: {e}")
                    continue
            else:
                recovered_opportunities.append(opp)

        return len(recovered_opportunities) > 0, recovered_opportunities

    def _handle_corruption_error(self, opportunities: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
        """Handle corruption errors by removing corrupted cost data"""
        logger.warning("Handling corruption error by removing corrupted cost data")

        recovered_opportunities = []
        for opp in opportunities:
            if 'cost_tracking' in opp:
                # Remove corrupted cost data
                opp_without_cost = opp.copy()
                opp_without_cost.pop('cost_tracking', None)
                recovered_opportunities.append(opp_without_cost)
            else:
                recovered_opportunities.append(opp)

        return True, recovered_opportunities

    def _handle_threshold_error(self, opportunities: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
        """Handle threshold exceeded errors by filtering high-cost opportunities"""
        logger.warning("Handling threshold error by filtering expensive opportunities")

        # Sort by cost and keep only opportunities under threshold
        opportunities_with_costs = [
            (opp, opp.get('cost_tracking', {}).get('total_cost_usd', 0.0))
            for opp in opportunities
        ]
        opportunities_with_costs.sort(key=lambda x: x[1])

        recovered_opportunities = []
        current_cost = 0.0

        for opp, cost in opportunities_with_costs:
            if current_cost + cost <= self.cost_threshold_usd:
                recovered_opportunities.append(opp)
                current_cost += cost
            else:
                # Remove cost data but keep opportunity
                opp_without_cost = opp.copy()
                opp_without_cost.pop('cost_tracking', None)
                recovered_opportunities.append(opp_without_cost)

        logger.info(f"Recovered {len(recovered_opportunities)} opportunities with total cost ${current_cost:.6f}")
        return True, recovered_opportunities

    def _handle_generic_error(self, opportunities: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
        """Handle generic errors by removing cost data"""
        logger.warning("Handling generic error by removing cost data")

        recovered_opportunities = []
        for opp in opportunities:
            opp_without_cost = opp.copy()
            opp_without_cost.pop('cost_tracking', None)
            recovered_opportunities.append(opp_without_cost)

        return True, recovered_opportunities

    def reset_recovery_state(self):
        """Reset recovery attempt counter"""
        self.recovery_attempts = 0

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of all errors encountered"""
        if not self.error_log:
            return {'total_errors': 0}

        error_types = {}
        for error in self.error_log:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            'total_errors': len(self.error_log),
            'error_types': error_types,
            'last_error': self.error_log[-1] if self.error_log else None,
            'recovery_attempts': self.recovery_attempts
        }


# Global error handler instance
cost_error_handler = CostTrackingErrorHandler()


def validate_and_handle_costs(
    opportunities: list[dict[str, Any]],
    max_cost_usd: float = 10.0
) -> tuple[bool, list[dict[str, Any]], dict[str, Any]]:
    """
    Validate and handle cost tracking for a batch of opportunities.

    Args:
        opportunities: List of opportunity dictionaries
        max_cost_usd: Maximum allowed cost per batch

    Returns:
        Tuple of (success, processed_opportunities, validation_summary)
    """
    handler = CostTrackingErrorHandler(max_cost_usd)

    try:
        # Validate batch costs
        is_valid, summary = handler.validate_batch_costs(opportunities)

        if not is_valid:
            # Handle validation errors
            should_retry, recovered_opps = handler.handle_cost_error(
                CostValidationError(f"Validation failed: {summary['validation_errors'][:3]}"),
                opportunities,
                {'validation_summary': summary}
            )

            if should_retry:
                return validate_and_handle_costs(recovered_opps, max_cost_usd)
            else:
                return False, recovered_opps, summary

        return True, opportunities, summary

    except Exception as e:
        # Handle unexpected errors
        should_retry, recovered_opps = handler.handle_cost_error(e, opportunities)
        return should_retry, recovered_opps, {'error': str(e)}
