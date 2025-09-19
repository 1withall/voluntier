"""
Comprehensive Input Validation Service
Provides enterprise-grade input validation and sanitization for all API endpoints.
"""

import re
import ipaddress
import email_validator
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, EmailStr
from pydantic.error_wrappers import ValidationError
import bleach

from voluntier.utils.logging import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom validation error with details."""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")


class InputValidator:
    """Comprehensive input validation service."""

    # Security patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(or|and)\s+\d+\s*=\s*\d+)",
        r"(\bexec\s*\()",
        r"(\bxp_cmdshell\b)",
        r"(\bsp_executesql\b)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"data:text/html",
    ]

    SHELL_INJECTION_PATTERNS = [
        r"[;&|`$()<>]",
        r"\$\{.*\}",
        r"`.*`",
        r"\$\(.*\)",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
    ]

    def __init__(self):
        self.logger = get_logger(__name__)

    def validate_email(self, email: str) -> bool:
        """Validate email address format and domain."""
        try:
            email_validator.validate_email(email, check_deliverability=False)
            return True
        except email_validator.EmailNotValidError:
            return False

    def validate_ip_address(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def validate_url(self, url: str) -> bool:
        """Validate URL format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return url_pattern.match(url) is not None

    def sanitize_html(self, content: str) -> str:
        """Sanitize HTML content to prevent XSS."""
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attributes = {}

        return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)

    def validate_string_length(self, value: str, min_length: int = 0, max_length: int = 1000) -> bool:
        """Validate string length constraints."""
        return min_length <= len(value) <= max_length

    def validate_alphanumeric(self, value: str, allow_spaces: bool = False) -> bool:
        """Validate that string contains only alphanumeric characters."""
        pattern = r'^[a-zA-Z0-9\s]+$' if allow_spaces else r'^[a-zA-Z0-9]+$'
        return bool(re.match(pattern, value))

    def detect_security_threats(self, input_string: str) -> List[str]:
        """Detect potential security threats in input."""
        threats = []

        # Check for SQL injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                threats.append("sql_injection")

        # Check for XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                threats.append("xss_attempt")

        # Check for shell injection
        for pattern in self.SHELL_INJECTION_PATTERNS:
            if re.search(pattern, input_string):
                threats.append("shell_injection")

        # Check for path traversal
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, input_string):
                threats.append("path_traversal")

        return list(set(threats))  # Remove duplicates

    def validate_and_sanitize(self, value: Any, field_type: str = "string") -> Any:
        """Validate and sanitize input based on type."""
        if isinstance(value, str):
            # Detect security threats
            threats = self.detect_security_threats(value)
            if threats:
                raise ValidationError(
                    "input",
                    f"Security threat detected: {', '.join(threats)}",
                    value
                )

            # Sanitize based on type
            if field_type == "html":
                return self.sanitize_html(value)
            elif field_type == "email":
                if not self.validate_email(value):
                    raise ValidationError("email", "Invalid email format", value)
                return value.lower().strip()
            elif field_type == "url":
                if not self.validate_url(value):
                    raise ValidationError("url", "Invalid URL format", value)
                return value
            else:
                # Basic string sanitization
                return value.strip()

        return value

    def validate_request_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate request data against a schema."""
        validated_data = {}

        for field_name, field_config in schema.items():
            if field_name not in data:
                if field_config.get("required", False):
                    raise ValidationError(field_name, "Required field is missing")
                continue

            value = data[field_name]
            field_type = field_config.get("type", "string")

            # Type validation
            if field_type == "string" and not isinstance(value, str):
                raise ValidationError(field_name, "Must be a string", value)
            elif field_type == "integer" and not isinstance(value, int):
                raise ValidationError(field_name, "Must be an integer", value)
            elif field_type == "boolean" and not isinstance(value, bool):
                raise ValidationError(field_name, "Must be a boolean", value)
            elif field_type == "list" and not isinstance(value, list):
                raise ValidationError(field_name, "Must be a list", value)

            # Length validation for strings
            if field_type == "string" and isinstance(value, str):
                min_length = field_config.get("min_length", 0)
                max_length = field_config.get("max_length", 1000)
                if not self.validate_string_length(value, min_length, max_length):
                    raise ValidationError(
                        field_name,
                        f"Length must be between {min_length} and {max_length} characters",
                        value
                    )

            # Pattern validation
            if "pattern" in field_config:
                if not re.match(field_config["pattern"], str(value)):
                    raise ValidationError(
                        field_name,
                        f"Does not match required pattern: {field_config['pattern']}",
                        value
                    )

            # Custom validation
            if "validator" in field_config:
                validator_func = field_config["validator"]
                if not validator_func(value):
                    raise ValidationError(
                        field_name,
                        field_config.get("validation_message", "Validation failed"),
                        value
                    )

            # Sanitize and validate
            try:
                validated_data[field_name] = self.validate_and_sanitize(value, field_type)
            except ValidationError as e:
                raise ValidationError(field_name, str(e), value)

        return validated_data


# Pydantic models for common API requests
class UserProfileUpdate(BaseModel):
    """User profile update request validation."""
    name: str = Field(..., min_length=2, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, regex=r'^\+?[\d\s\-\(\)]+$', max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)

    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z\s\-]+$', v):
            raise ValueError('Name can only contain letters, spaces, and hyphens')
        return v

    @validator('skills', 'interests')
    def validate_lists(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 items allowed')
        for item in v:
            if len(item) > 50:
                raise ValueError('Each item must be 50 characters or less')
        return v


class SecurityEventFilter(BaseModel):
    """Security event filtering validation."""
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    severity: Optional[str] = Field(None, regex=r'^(LOW|MEDIUM|HIGH|CRITICAL)$')
    event_type: Optional[str] = Field(None, max_length=100)
    source_ip: Optional[str] = Field(None, max_length=45)  # IPv6 max length
    since: Optional[datetime] = None


class ThreatIntelligenceCreate(BaseModel):
    """Threat intelligence creation validation."""
    indicator_type: str = Field(..., regex=r'^(ip|domain|url|hash|email)$')
    indicator_value: str = Field(..., max_length=500)
    threat_type: str = Field(..., max_length=100)
    threat_score: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class IncidentCreateRequest(BaseModel):
    """Security incident creation validation."""
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    incident_type: str = Field(..., max_length=100)
    severity: str = Field(..., regex=r'^(LOW|MEDIUM|HIGH|CRITICAL)$')
    affected_systems: List[str] = Field(default_factory=list, max_items=50)

    @validator('affected_systems')
    def validate_systems(cls, v):
        for system in v:
            if len(system) > 100:
                raise ValueError('System name too long')
        return v


# Global validator instance
input_validator = InputValidator()


# Convenience validation schemas
USER_PROFILE_SCHEMA = {
    "name": {"type": "string", "required": True, "min_length": 2, "max_length": 100},
    "bio": {"type": "string", "max_length": 500},
    "phone": {"type": "string", "pattern": r'^\+?[\d\s\-\(\)]+$', "max_length": 20},
    "location": {"type": "string", "max_length": 100},
    "skills": {"type": "list", "max_length": 20},
    "interests": {"type": "list", "max_length": 20}
}

SECURITY_FILTER_SCHEMA = {
    "limit": {"type": "integer", "min": 1, "max": 1000},
    "offset": {"type": "integer", "min": 0},
    "severity": {"type": "string", "pattern": r'^(LOW|MEDIUM|HIGH|CRITICAL)$'},
    "event_type": {"type": "string", "max_length": 100},
    "source_ip": {"type": "string", "max_length": 45}
}

THREAT_INTELLIGENCE_SCHEMA = {
    "indicator_type": {"type": "string", "required": True, "pattern": r'^(ip|domain|url|hash|email)$'},
    "indicator_value": {"type": "string", "required": True, "max_length": 500},
    "threat_type": {"type": "string", "required": True, "max_length": 100},
    "threat_score": {"type": "integer", "required": True, "min": 0, "max": 100},
    "confidence": {"type": "integer", "required": True, "min": 0, "max": 100},
    "source": {"type": "string", "required": True, "max_length": 200},
    "description": {"type": "string", "max_length": 1000}
}