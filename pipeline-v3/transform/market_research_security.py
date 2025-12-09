"""
MarketResearchAgent Security and Compliance Module

Production-grade security, authentication, authorization, and compliance features
for Jina Market Research Integration Phase 3.7
"""

import asyncio
import hashlib
import json
import logging
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any

from cryptography.fernet import Fernet

# Import monitoring and other components

# PII detection and anonymization (with fallback)
try:
    import spacy
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different operations"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class PIIType(Enum):
    """Types of Personally Identifiable Information"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    ADDRESS = "address"
    IP_ADDRESS = "ip_address"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    HEALTH_INFO = "health_info"
    FINANCIAL_INFO = "financial_info"


@dataclass
class SecurityContext:
    """Security context for operations"""
    user_id: str | None = None
    api_key_id: str | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    security_level: SecurityLevel = SecurityLevel.PUBLIC
    permissions: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    additional_claims: dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: str) -> bool:
        """Check if context has specific permission"""
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        """Check if context has specific role"""
        return f"role:{role}" in self.permissions


@dataclass
class PIIEntity:
    """PII entity detected in text"""
    text: str
    pii_type: PIIType
    start: int
    end: int
    confidence: float
    additional_info: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.pii_type, str):
            self.pii_type = PIIType(self.pii_type)


class APIKeyManager:
    """Secure API key management with rotation"""

    def __init__(
        self,
        encryption_key: bytes | None = None,
        key_rotation_days: int = 90
    ):
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.key_rotation_days = key_rotation_days
        self.api_keys: dict[str, dict[str, Any]] = {}
        self.usage_log: list[dict[str, Any]] = []

    def generate_api_key(
        self,
        name: str,
        permissions: list[str],
        expires_days: int | None = None,
        rate_limit: int | None = None
    ) -> tuple[str, str]:
        """
        Generate new API key

        Args:
            name: Human-readable name for the key
            permissions: List of permissions
            expires_days: Days until key expires (None = no expiry)
            rate_limit: Requests per minute limit

        Returns:
            Tuple of (api_key, key_id)
        """
        key_id = secrets.token_urlsafe(16)
        raw_key = secrets.token_urlsafe(32)
        api_key = f"rh_{key_id}_{raw_key}"

        # Encrypt and store key details
        key_data = {
            'name': name,
            'permissions': permissions,
            'created_at': datetime.now().isoformat(),
            'expires_at': (
                (datetime.now() + timedelta(days=expires_days)).isoformat()
                if expires_days else None
            ),
            'rate_limit': rate_limit,
            'last_used': None,
            'usage_count': 0,
            'enabled': True
        }

        encrypted_data = self.cipher_suite.encrypt(json.dumps(key_data).encode())
        self.api_keys[key_id] = {
            'encrypted_data': encrypted_data.decode(),
            'checksum': hashlib.sha256(api_key.encode()).hexdigest()
        }

        logger.info(f"Generated API key: {name} (ID: {key_id})")
        return api_key, key_id

    def validate_api_key(self, api_key: str) -> SecurityContext | None:
        """
        Validate API key and return security context

        Args:
            api_key: API key to validate

        Returns:
            SecurityContext if valid, None otherwise
        """
        try:
            # Parse key format: rh_keyId_rawKey
            if not api_key.startswith('rh_'):
                return None

            parts = api_key.split('_', 2)
            if len(parts) != 3:
                return None

            _, key_id, raw_key = parts

            # Check if key exists
            if key_id not in self.api_keys:
                logger.warning(f"Unknown API key ID: {key_id}")
                return None

            key_info = self.api_keys[key_id]

            # Verify checksum
            expected_checksum = hashlib.sha256(api_key.encode()).hexdigest()
            if key_info['checksum'] != expected_checksum:
                logger.warning(f"Invalid API key checksum for: {key_id}")
                return None

            # Decrypt and parse key data
            decrypted_data = json.loads(
                self.cipher_suite.decrypt(key_info['encrypted_data'].encode()).decode()
            )

            # Check if key is enabled
            if not decrypted_data.get('enabled', True):
                logger.warning(f"Disabled API key used: {key_id}")
                return None

            # Check expiration
            if decrypted_data.get('expires_at'):
                expires_at = datetime.fromisoformat(decrypted_data['expires_at'])
                if datetime.now() > expires_at:
                    logger.warning(f"Expired API key used: {key_id}")
                    return None

            # Update usage statistics
            decrypted_data['last_used'] = datetime.now().isoformat()
            decrypted_data['usage_count'] += 1
            key_info['encrypted_data'] = self.cipher_suite.encrypt(
                json.dumps(decrypted_data).encode()
            ).decode()

            # Log usage
            self.usage_log.append({
                'key_id': key_id,
                'timestamp': datetime.now().isoformat(),
                'success': True
            })

            # Create security context
            return SecurityContext(
                api_key_id=key_id,
                security_level=SecurityLevel.INTERNAL,
                permissions=decrypted_data.get('permissions', []),
                additional_claims={
                    'key_name': decrypted_data.get('name'),
                    'rate_limit': decrypted_data.get('rate_limit'),
                    'usage_count': decrypted_data.get('usage_count', 0)
                }
            )

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None

    def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke API key

        Args:
            key_id: Key ID to revoke

        Returns:
            True if revoked successfully
        """
        if key_id in self.api_keys:
            try:
                key_data = json.loads(
                    self.cipher_suite.decrypt(
                        self.api_keys[key_id]['encrypted_data'].encode()
                    ).decode()
                )
                key_data['enabled'] = False
                key_data['revoked_at'] = datetime.now().isoformat()

                self.api_keys[key_id]['encrypted_data'] = self.cipher_suite.encrypt(
                    json.dumps(key_data).encode()
                ).decode()

                logger.info(f"Revoked API key: {key_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to revoke API key {key_id}: {e}")
                return False

        return False

    def rotate_keys(self) -> list[str]:
        """
        Rotate keys that are due for rotation

        Returns:
            List of rotated key IDs
        """
        rotated_keys = []
        now = datetime.now()

        for key_id, key_info in self.api_keys.items():
            try:
                key_data = json.loads(
                    self.cipher_suite.decrypt(key_info['encrypted_data'].encode()).decode()
                )

                created_at = datetime.fromisoformat(key_data['created_at'])
                days_old = (now - created_at).days

                if days_old >= self.key_rotation_days and key_data.get('enabled', True):
                    # Generate new key for same permissions
                    new_api_key, new_key_id = self.generate_api_key(
                        name=f"{key_data['name']} (Rotated)",
                        permissions=key_data['permissions'],
                        expires_days=None if not key_data.get('expires_at') else
                            int((datetime.fromisoformat(key_data['expires_at']) - now).days),
                        rate_limit=key_data.get('rate_limit')
                    )

                    # Revoke old key
                    self.revoke_api_key(key_id)
                    rotated_keys.append(f"{key_id} -> {new_key_id}")

            except Exception as e:
                logger.error(f"Failed to rotate key {key_id}: {e}")

        return rotated_keys


class PIIAnonymizer:
    """PII detection and anonymization"""

    def __init__(
        self,
        model_name: str = "en_core_web_lg",
        enabled: bool = True,
        custom_patterns: dict[str, str] | None = None
    ):
        self.enabled = enabled
        self.nlp = None
        self.custom_patterns = custom_patterns or {}

        # Initialize spaCy model if available
        if SPACY_AVAILABLE and enabled:
            try:
                self.nlp = spacy.load(model_name)
                logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                logger.warning(f"spaCy model {model_name} not found, using basic patterns")
                self._initialize_basic_patterns()
        else:
            self._initialize_basic_patterns()

        # Define regex patterns for basic PII detection
        self.patterns = {
            PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            PIIType.PHONE: r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            PIIType.SSN: r'\b\d{3}-?\d{2}-?\d{4}\b',
            PIIType.CREDIT_CARD: r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
            PIIType.IP_ADDRESS: r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            PIIType.PASSPORT: r'\b[A-Z]{1,2}[0-9]{6,9}\b',
            PIIType.DRIVERS_LICENSE: r'\b[A-Z]{1,2}[0-9]{6,8}\b'
        }

        # Add custom patterns
        for pii_type, pattern in self.custom_patterns.items():
            try:
                self.patterns[PIIType(pii_type)] = pattern
            except ValueError:
                logger.warning(f"Invalid PII type: {pii_type}")

    def _initialize_basic_patterns(self):
        """Initialize basic text processing for when spaCy is not available"""
        try:
            self.nlp = English()
            self.nlp.add_pipe("sentencizer")
        except Exception as e:
            logger.error(f"Failed to initialize basic text processing: {e}")
            self.nlp = None

    def detect_pii(self, text: str) -> list[PIIEntity]:
        """
        Detect PII in text

        Args:
            text: Text to analyze

        Returns:
            List of detected PII entities
        """
        if not self.enabled:
            return []

        entities = []

        # Use regex patterns
        for pii_type, pattern in self.patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(PIIEntity(
                    text=match.group(),
                    pii_type=pii_type,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.8  # Medium confidence for regex
                ))

        # Use spaCy NER if available
        if self.nlp and hasattr(self.nlp, 'pipe_names'):
            doc = self.nlp(text)

            # Map spaCy entities to PII types
            entity_mapping = {
                'PERSON': PIIType.NAME,
                'GPE': PIIType.ADDRESS,  # Geopolitical Entity
                'LOC': PIIType.ADDRESS,  # Location
                'ORG': None,  # Organizations not considered PII
                'MONEY': PIIType.FINANCIAL_INFO,
                'CARDINAL': None,  # Numbers not inherently PII
            }

            for ent in doc.ents:
                pii_type = entity_mapping.get(ent.label_)
                if pii_type:
                    entities.append(PIIEntity(
                        text=ent.text,
                        pii_type=pii_type,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.9,  # Higher confidence for spaCy
                        additional_info={'spacy_label': ent.label_}
                    ))

        # Remove duplicates and sort by position
        unique_entities = []
        seen_positions = set()

        for entity in sorted(entities, key=lambda e: e.start):
            pos_key = (entity.start, entity.end)
            if pos_key not in seen_positions:
                unique_entities.append(entity)
                seen_positions.add(pos_key)

        return unique_entities

    def anonymize_text(
        self,
        text: str,
        method: str = "mask",
        preserve_length: bool = False
    ) -> tuple[str, list[PIIEntity]]:
        """
        Anonymize PII in text

        Args:
            text: Text to anonymize
            method: Anonymization method ("mask", "remove", "replace")
            preserve_length: Whether to preserve original text length

        Returns:
            Tuple of (anonymized_text, detected_pii)
        """
        if not self.enabled:
            return text, []

        pii_entities = self.detect_pii(text)
        anonymized_text = text

        # Process entities in reverse order to maintain positions
        for entity in sorted(pii_entities, key=lambda e: e.start, reverse=True):
            if method == "mask":
                replacement = "*" * len(entity.text) if preserve_length else "***"
            elif method == "remove":
                replacement = ""
            elif method == "replace":
                replacement = f"[{entity.pii_type.value.upper()}]"
            else:
                replacement = "***"

            anonymized_text = (
                anonymized_text[:entity.start] +
                replacement +
                anonymized_text[entity.end:]
            )

        return anonymized_text, pii_entities

    def anonymize_json(
        self,
        data: dict[str, Any],
        method: str = "mask"
    ) -> tuple[dict[str, Any], dict[str, list[PIIEntity]]]:
        """
        Anonymize PII in JSON data

        Args:
            data: JSON data to anonymize
            method: Anonymization method

        Returns:
            Tuple of (anonymized_data, pii_by_field)
        """
        if not self.enabled:
            return data, {}

        anonymized_data = {}
        pii_by_field = {}

        for key, value in data.items():
            if isinstance(value, str):
                anonymized_text, pii_entities = self.anonymize_text(value, method)
                anonymized_data[key] = anonymized_text
                if pii_entities:
                    pii_by_field[key] = pii_entities
            elif isinstance(value, dict):
                nested_anonymized, nested_pii = self.anonymize_json(value, method)
                anonymized_data[key] = nested_anonymized
                if nested_pii:
                    pii_by_field[key] = nested_pii
            elif isinstance(value, list):
                anonymized_list = []
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        anonymized_text, pii_entities = self.anonymize_text(item, method)
                        anonymized_list.append(anonymized_text)
                        if pii_entities:
                            pii_by_field[f"{key}[{i}]"] = pii_entities
                    elif isinstance(item, dict):
                        nested_anonymized, nested_pii = self.anonymize_json(item, method)
                        anonymized_list.append(nested_anonymized)
                        if nested_pii:
                            pii_by_field[f"{key}[{i}]"] = nested_pii
                    else:
                        anonymized_list.append(item)
                anonymized_data[key] = anonymized_list
            else:
                anonymized_data[key] = value

        return anonymized_data, pii_by_field


class AuditLogger:
    """Comprehensive audit logging for security and compliance"""

    def __init__(
        self,
        log_file: str | None = None,
        retention_days: int = 1095,
        enable_file_logging: bool = True,
        enable_remote_logging: bool = False
    ):
        self.retention_days = retention_days
        self.enable_file_logging = enable_file_logging
        self.enable_remote_logging = enable_remote_logging
        self.log_file = log_file or "/var/log/redditharbor/audit.log"

        # Initialize file logger
        if self.enable_file_logging:
            self._setup_file_logger()

        # In-memory buffer for recent logs
        self.recent_logs = deque(maxlen=1000)

    def _setup_file_logger(self):
        """Setup dedicated audit file logger"""
        self.audit_logger = logging.getLogger("market_research_audit")
        self.audit_logger.setLevel(logging.INFO)

        # Create file handler
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)

        # Create formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        self.audit_logger.addHandler(handler)

        # Prevent propagation to avoid duplicate logs
        self.audit_logger.propagate = False

    def log_event(
        self,
        event_type: str,
        user_id: str | None = None,
        api_key_id: str | None = None,
        resource: str | None = None,
        action: str | None = None,
        outcome: str = "success",
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None
    ):
        """
        Log security/compliance event

        Args:
            event_type: Type of event (api_access, data_access, security_event, etc.)
            user_id: User ID if applicable
            api_key_id: API key ID if applicable
            resource: Resource being accessed
            action: Action performed
            outcome: Outcome (success, failure, error)
            details: Additional event details
            ip_address: Client IP address
            user_agent: Client user agent
        """
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'api_key_id': api_key_id,
            'resource': resource,
            'action': action,
            'outcome': outcome,
            'details': details or {},
            'ip_address': ip_address,
            'user_agent': user_agent
        }

        # Add to in-memory buffer
        self.recent_logs.append(event_data)

        # Log to file if enabled
        if self.enable_file_logging:
            self.audit_logger.info(json.dumps(event_data))

        # Send to remote logging if enabled
        if self.enable_remote_logging:
            # Implementation depends on remote logging system
            # (e.g., Splunk, ELK Stack, CloudWatch Logs)
            asyncio.create_task(self._send_remote_log(event_data))

    async def _send_remote_log(self, event_data: dict[str, Any]):
        """Send log to remote logging system"""
        # Implementation depends on your logging infrastructure
        pass

    def log_api_access(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        security_context: SecurityContext | None = None,
        request_details: dict[str, Any] | None = None
    ):
        """Log API access event"""
        self.log_event(
            event_type="api_access",
            user_id=security_context.user_id if security_context else None,
            api_key_id=security_context.api_key_id if security_context else None,
            resource=endpoint,
            action=method,
            outcome="success" if 200 <= status_code < 400 else "failure",
            details={
                'status_code': status_code,
                'response_time_ms': response_time_ms,
                'request_details': request_details or {}
            },
            ip_address=security_context.additional_claims.get('ip_address') if security_context else None,
            user_agent=security_context.additional_claims.get('user_agent') if security_context else None
        )

    def log_data_access(
        self,
        operation: str,
        resource_type: str,
        resource_id: str | None = None,
        security_context: SecurityContext | None = None,
        pii_detected: bool = False
    ):
        """Log data access event"""
        self.log_event(
            event_type="data_access",
            user_id=security_context.user_id if security_context else None,
            api_key_id=security_context.api_key_id if security_context else None,
            resource=f"{resource_type}:{resource_id}" if resource_id else resource_type,
            action=operation,
            outcome="success",
            details={
                'pii_detected': pii_detected
            }
        )

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        security_context: SecurityContext | None = None,
        additional_details: dict[str, Any] | None = None
    ):
        """Log security-related event"""
        self.log_event(
            event_type="security_event",
            user_id=security_context.user_id if security_context else None,
            api_key_id=security_context.api_key_id if security_context else None,
            action=event_type,
            outcome="security_event",
            details={
                'severity': severity,
                'description': description,
                'additional_details': additional_details or {}
            }
        )

    def get_recent_logs(
        self,
        limit: int = 100,
        event_type: str | None = None,
        user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get recent logs from in-memory buffer

        Args:
            limit: Maximum number of logs to return
            event_type: Filter by event type
            user_id: Filter by user ID

        Returns:
            List of log entries
        """
        logs = list(self.recent_logs)

        # Apply filters
        if event_type:
            logs = [log for log in logs if log.get('event_type') == event_type]
        if user_id:
            logs = [log for log in logs if log.get('user_id') == user_id]

        # Return limited results
        return logs[-limit:]


class SecurityManager:
    """
    Central security management for MarketResearchAgent

    Coordinates:
    - API key management and rotation
    - PII detection and anonymization
    - Audit logging
    - Authentication and authorization
    - Rate limiting
    - Security monitoring
    """

    def __init__(
        self,
        encryption_key: bytes | None = None,
        enable_pii_anonymization: bool = True,
        enable_audit_logging: bool = True
    ):
        self.encryption_key = encryption_key
        self.enable_pii_anonymization = enable_pii_anonymization
        self.enable_audit_logging = enable_audit_logging

        # Initialize components
        self.api_key_manager = APIKeyManager(encryption_key=encryption_key)
        self.pii_anonymizer = PIIAnonymizer(enabled=enable_pii_anonymization)
        self.audit_logger = AuditLogger(enable_file_logging=enable_audit_logging)

        # Rate limiting
        self.rate_limits: dict[str, dict[str, Any]] = {}

        # Security monitoring
        self.security_events = deque(maxlen=1000)
        self.failed_attempts: dict[str, list[datetime]] = defaultdict(list)

    def authenticate_request(
        self,
        api_key: str,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> SecurityContext | None:
        """
        Authenticate API request

        Args:
            api_key: API key from request
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            SecurityContext if authenticated, None otherwise
        """
        try:
            security_context = self.api_key_manager.validate_api_key(api_key)

            if security_context:
                # Add request metadata
                if ip_address:
                    security_context.additional_claims['ip_address'] = ip_address
                if user_agent:
                    security_context.additional_claims['user_agent'] = user_agent

                # Check rate limiting
                if not self._check_rate_limit(security_context, ip_address):
                    self.audit_logger.log_security_event(
                        event_type="rate_limit_exceeded",
                        severity="warning",
                        description="API rate limit exceeded",
                        security_context=security_context
                    )
                    return None

                # Log successful authentication
                self.audit_logger.log_event(
                    event_type="authentication",
                    user_id=security_context.user_id,
                    api_key_id=security_context.api_key_id,
                    action="api_key_validation",
                    outcome="success",
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                return security_context

            else:
                # Log failed authentication
                self.audit_logger.log_security_event(
                    event_type="authentication_failure",
                    severity="warning",
                    description="Invalid API key",
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                # Track failed attempts
                if ip_address:
                    self._track_failed_attempt(ip_address)

                return None

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.audit_logger.log_security_event(
                event_type="authentication_error",
                severity="error",
                description=f"Authentication error: {str(e)}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None

    def authorize_operation(
        self,
        security_context: SecurityContext,
        required_permission: str,
        resource: str | None = None
    ) -> bool:
        """
        Authorize operation based on security context

        Args:
            security_context: Security context from authentication
            required_permission: Required permission for operation
            resource: Resource being accessed

        Returns:
            True if authorized, False otherwise
        """
        # Check if context has required permission
        if not security_context.has_permission(required_permission):
            self.audit_logger.log_security_event(
                event_type="authorization_failure",
                severity="warning",
                description=f"Missing required permission: {required_permission}",
                security_context=security_context,
                additional_details={'resource': resource}
            )
            return False

        # Log successful authorization
        self.audit_logger.log_event(
            event_type="authorization",
            user_id=security_context.user_id,
            api_key_id=security_context.api_key_id,
            resource=resource,
            action="permission_check",
            outcome="success",
            details={'required_permission': required_permission}
        )

        return True

    def process_sensitive_data(
        self,
        data: str | dict[str, Any],
        operation: str,
        security_context: SecurityContext | None = None
    ) -> tuple[str | dict[str, Any], bool]:
        """
        Process sensitive data with PII protection

        Args:
            data: Data to process
            operation: Operation being performed
            security_context: Security context

        Returns:
            Tuple of (processed_data, pii_detected)
        """
        if not self.enable_pii_anonymization:
            return data, False

        try:
            if isinstance(data, str):
                processed_data, pii_entities = self.pii_anonymizer.anonymize_text(data)
                pii_detected = len(pii_entities) > 0
            elif isinstance(data, dict):
                processed_data, pii_by_field = self.pii_anonymizer.anonymize_json(data)
                pii_detected = len(pii_by_field) > 0
            else:
                processed_data = data
                pii_detected = False

            # Log data access if PII detected
            if pii_detected and security_context:
                self.audit_logger.log_data_access(
                    operation=operation,
                    resource_type="market_research_data",
                    security_context=security_context,
                    pii_detected=True
                )

            return processed_data, pii_detected

        except Exception as e:
            logger.error(f"PII processing error: {e}")
            self.audit_logger.log_security_event(
                event_type="pii_processing_error",
                severity="error",
                description=f"PII processing error: {str(e)}",
                security_context=security_context
            )
            return data, False

    def _check_rate_limit(
        self,
        security_context: SecurityContext,
        ip_address: str | None = None
    ) -> bool:
        """Check if request exceeds rate limits"""
        # Get rate limit from security context
        rate_limit = security_context.additional_claims.get('rate_limit', 60)  # Default: 60/min

        if rate_limit is None or rate_limit <= 0:
            return True  # No rate limiting

        # Simple token bucket implementation
        key = security_context.api_key_id or ip_address or "anonymous"
        now = datetime.now()

        if key not in self.rate_limits:
            self.rate_limits[key] = {
                'tokens': rate_limit,
                'last_refill': now,
                'rate_limit': rate_limit
            }

        bucket = self.rate_limits[key]

        # Refill tokens based on time elapsed
        time_passed = (now - bucket['last_refill']).total_seconds()
        tokens_to_add = time_passed * (rate_limit / 60)  # Rate per second

        bucket['tokens'] = min(bucket['rate_limit'], bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now

        # Check if request can proceed
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        else:
            return False

    def _track_failed_attempt(self, ip_address: str):
        """Track failed authentication attempts"""
        now = datetime.now()
        self.failed_attempts[ip_address].append(now)

        # Remove old attempts (keep last hour)
        cutoff = now - timedelta(hours=1)
        self.failed_attempts[ip_address] = [
            attempt for attempt in self.failed_attempts[ip_address]
            if attempt > cutoff
        ]

        # Check for potential brute force attack
        if len(self.failed_attempts[ip_address]) > 10:  # 10 failed attempts in 1 hour
            self.audit_logger.log_security_event(
                event_type="potential_brute_force",
                severity="high",
                description="Multiple failed authentication attempts detected",
                ip_address=ip_address,
                additional_details={'failed_attempts': len(self.failed_attempts[ip_address])}
            )

    def require_permission(self, permission: str):
        """Decorator to require specific permission for function"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract security context from kwargs (should be passed by authentication middleware)
                security_context = kwargs.get('security_context')

                if not security_context or not self.authorize_operation(security_context, permission):
                    raise PermissionError(f"Required permission '{permission}' not found")

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def get_security_stats(self) -> dict[str, Any]:
        """Get security statistics"""
        active_api_keys = sum(
            1 for key_info in self.api_key_manager.api_keys.values()
            if json.loads(
                self.api_key_manager.cipher_suite.decrypt(
                    key_info['encrypted_data'].encode()
                ).decode()
            ).get('enabled', True)
        )

        return {
            'active_api_keys': active_api_keys,
            'total_api_keys': len(self.api_key_manager.api_keys),
            'failed_login_attempts': {
                ip: len(attempts) for ip, attempts in self.failed_attempts.items()
            },
            'rate_limit_buckets': len(self.rate_limits),
            'recent_security_events': len(self.security_events),
            'pii_anonymization_enabled': self.enable_pii_anonymization,
            'audit_logging_enabled': self.enable_audit_logging
        }

    async def cleanup_expired_data(self):
        """Clean up expired security data"""
        # Clean up expired API keys
        expired_keys = []
        for key_id, key_info in self.api_key_manager.api_keys.items():
            try:
                key_data = json.loads(
                    self.api_key_manager.cipher_suite.decrypt(
                        key_info['encrypted_data'].encode()
                    ).decode()
                )

                if key_data.get('expires_at'):
                    expires_at = datetime.fromisoformat(key_data['expires_at'])
                    if datetime.now() > expires_at:
                        expired_keys.append(key_id)

            except Exception:
                continue

        for key_id in expired_keys:
            self.api_key_manager.revoke_api_key(key_id)

        # Clean up old failed attempts
        cutoff = datetime.now() - timedelta(days=7)
        for ip in list(self.failed_attempts.keys()):
            self.failed_attempts[ip] = [
                attempt for attempt in self.failed_attempts[ip]
                if attempt > cutoff
            ]
            if not self.failed_attempts[ip]:
                del self.failed_attempts[ip]

        logger.info(f"Cleaned up {len(expired_keys)} expired API keys")


# Global security manager instance
_security_manager: SecurityManager | None = None


def get_security_manager() -> SecurityManager:
    """Get or create global security manager"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def require_authentication(func):
    """Decorator to require authentication for function"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        security_context = kwargs.get('security_context')
        if not security_context:
            raise PermissionError("Authentication required")

        return await func(*args, **kwargs)
    return wrapper


def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            security_context = kwargs.get('security_context')
            if not security_context or not security_context.has_role(role):
                raise PermissionError(f"Required role '{role}' not found")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
