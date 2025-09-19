"""
Security Configuration Module
Comprehensive Security Settings and Parameters

This module defines all security-related configuration including:
- Threat detection thresholds
- Honeypot configurations
- Rate limiting parameters
- Authentication settings
- Encryption configurations
- Monitoring and alerting settings
"""

from datetime import timedelta
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class ThreatLevel(str, Enum):
    """Threat severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ResponseAction(str, Enum):
    """Security response actions"""
    LOG = "log"
    MONITOR = "monitor"
    RATE_LIMIT = "rate_limit"
    BLOCK_IP = "block_ip"
    REQUIRE_MFA = "require_mfa"
    QUARANTINE_USER = "quarantine_user"
    ALERT_ADMIN = "alert_admin"
    CREATE_INCIDENT = "create_incident"

class SecurityConfig(BaseModel):
    """Main security configuration"""
    
    # General security settings
    security_enabled: bool = True
    debug_mode: bool = False
    paranoid_mode: bool = False  # Extra strict security
    
    # Authentication and session settings
    session_timeout: int = 3600  # 1 hour in seconds
    max_login_attempts: int = 5
    lockout_duration: int = 3600  # 1 hour in seconds
    password_min_length: int = 12
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    mfa_required_for_admin: bool = True
    jwt_expiry: int = 86400  # 24 hours
    refresh_token_expiry: int = 604800  # 7 days
    
    # Rate limiting configuration
    global_rate_limit: int = 1000  # requests per minute
    api_rate_limit: int = 500  # API requests per minute
    login_rate_limit: int = 10  # login attempts per minute
    suspicious_ip_rate_limit: int = 50  # for suspicious IPs
    burst_allowance: int = 50  # burst allowance
    
    # Threat detection thresholds
    anomaly_detection_threshold: float = -0.5
    high_risk_threshold: float = -0.7
    critical_threat_threshold: float = -0.9
    behavioral_anomaly_threshold: float = 0.6
    ml_confidence_threshold: float = 0.7
    
    # Honeypot configuration
    honeypot_enabled: bool = True
    auto_deploy_honeypots: bool = True
    honeypot_response_delay: float = 0.5  # seconds
    max_honeypots: int = 100
    honeypot_rotation_interval: int = 86400  # 24 hours
    
    # Network security
    block_tor_networks: bool = True
    block_vpn_networks: bool = False
    block_cloud_providers: bool = False
    geo_blocking_enabled: bool = False
    blocked_countries: List[str] = []
    allowed_countries: List[str] = []
    
    # Monitoring and alerting
    real_time_monitoring: bool = True
    alert_threshold_critical: int = 1  # immediate alert
    alert_threshold_high: int = 5  # alert after 5 events
    alert_threshold_medium: int = 20  # alert after 20 events
    monitoring_interval: int = 60  # seconds
    log_retention_days: int = 90
    
    # Incident response
    auto_incident_creation: bool = True
    auto_response_enabled: bool = True
    escalation_timeout: int = 1800  # 30 minutes
    require_human_approval: List[ResponseAction] = [
        ResponseAction.BLOCK_IP,
        ResponseAction.QUARANTINE_USER,
        ResponseAction.CREATE_INCIDENT
    ]
    
    # Encryption and hashing
    bcrypt_rounds: int = 12
    jwt_algorithm: str = "HS256"
    encryption_algorithm: str = "AES-256-GCM"
    hash_algorithm: str = "SHA-256"
    
    # Data protection
    data_masking_enabled: bool = True
    pii_detection_enabled: bool = True
    data_loss_prevention: bool = True
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True

class ThreatDetectionConfig(BaseModel):
    """Threat detection specific configuration"""
    
    # Machine learning settings
    ml_model_retraining_interval: int = 86400  # 24 hours
    feature_extraction_enabled: bool = True
    anomaly_detection_enabled: bool = True
    behavioral_analysis_enabled: bool = True
    signature_detection_enabled: bool = True
    
    # Detection rules
    sql_injection_detection: bool = True
    xss_detection: bool = True
    command_injection_detection: bool = True
    directory_traversal_detection: bool = True
    brute_force_detection: bool = True
    reconnaissance_detection: bool = True
    
    # Adaptive thresholds
    adaptive_thresholds_enabled: bool = True
    threshold_adjustment_factor: float = 0.1
    min_threshold: float = 0.1
    max_threshold: float = 0.9
    
    # Training data requirements
    min_training_samples: int = 1000
    max_training_samples: int = 100000
    training_data_retention: int = 30  # days
    
    # Performance tuning
    batch_processing_enabled: bool = True
    batch_size: int = 100
    processing_timeout: int = 30  # seconds
    max_concurrent_analyses: int = 50

class HoneypotConfig(BaseModel):
    """Honeypot system configuration"""
    
    # Deployment settings
    auto_deployment_enabled: bool = True
    targeted_deployment_enabled: bool = True
    deployment_frequency_hours: int = 24
    max_honeypots_per_type: int = 10
    
    # Response generation
    realistic_responses: bool = True
    response_randomization: bool = True
    fake_data_generation: bool = True
    interactive_honeypots: bool = True
    
    # Intelligence collection
    attacker_profiling_enabled: bool = True
    tool_detection_enabled: bool = True
    attribution_analysis_enabled: bool = True
    behavioral_tracking_enabled: bool = True
    
    # Honeypot types and configurations
    admin_honeypots: Dict[str, Any] = {
        "enabled": True,
        "paths": ["/admin", "/administrator", "/wp-admin", "/phpmyadmin"],
        "response_type": "admin_login",
        "intelligence_value": "HIGH"
    }
    
    config_honeypots: Dict[str, Any] = {
        "enabled": True,
        "paths": ["/.env", "/config.php", "/.aws/credentials"],
        "response_type": "config_file",
        "intelligence_value": "CRITICAL"
    }
    
    backup_honeypots: Dict[str, Any] = {
        "enabled": True,
        "paths": ["/backup.sql", "/dump.sql", "/database.tar.gz"],
        "response_type": "database_backup",
        "intelligence_value": "HIGH"
    }
    
    api_honeypots: Dict[str, Any] = {
        "enabled": True,
        "paths": ["/api/admin", "/api/debug", "/api/internal"],
        "response_type": "api_error",
        "intelligence_value": "MEDIUM"
    }

class IncidentResponseConfig(BaseModel):
    """Incident response configuration"""
    
    # Response automation
    automated_response_enabled: bool = True
    human_approval_required: bool = True
    response_escalation_enabled: bool = True
    
    # Response playbooks
    playbooks: Dict[str, Dict[str, Any]] = {
        "brute_force": {
            "detection_threshold": 5,
            "time_window": 300,
            "actions": [ResponseAction.RATE_LIMIT, ResponseAction.BLOCK_IP],
            "escalation_time": 1800,
            "auto_resolve": True
        },
        "sql_injection": {
            "detection_threshold": 1,
            "time_window": 60,
            "actions": [ResponseAction.BLOCK_IP, ResponseAction.CREATE_INCIDENT],
            "escalation_time": 300,
            "auto_resolve": False
        },
        "malware": {
            "detection_threshold": 1,
            "time_window": 0,
            "actions": [ResponseAction.QUARANTINE_USER, ResponseAction.ALERT_ADMIN],
            "escalation_time": 60,
            "auto_resolve": False
        }
    }
    
    # Escalation rules
    escalation_rules: Dict[str, Dict[str, Any]] = {
        ThreatLevel.LOW: {
            "escalation_time": 3600,
            "escalate_to": "admin",
            "require_approval": False
        },
        ThreatLevel.MEDIUM: {
            "escalation_time": 1800,
            "escalate_to": "security_team",
            "require_approval": True
        },
        ThreatLevel.HIGH: {
            "escalation_time": 300,
            "escalate_to": "security_manager",
            "require_approval": True
        },
        ThreatLevel.CRITICAL: {
            "escalation_time": 60,
            "escalate_to": "ciso",
            "require_approval": True
        }
    }
    
    # Communication settings
    notification_channels: List[str] = ["email", "slack", "sms"]
    emergency_contacts: List[str] = []
    external_notification_required: bool = True

class ComplianceConfig(BaseModel):
    """Compliance and regulatory configuration"""
    
    # Compliance frameworks
    gdpr_compliance: bool = True
    hipaa_compliance: bool = False
    sox_compliance: bool = False
    pci_compliance: bool = False
    
    # Audit and logging
    audit_logging_enabled: bool = True
    detailed_audit_logs: bool = True
    log_data_access: bool = True
    log_administrative_actions: bool = True
    log_security_events: bool = True
    
    # Data retention
    audit_log_retention_days: int = 2555  # 7 years
    security_log_retention_days: int = 365  # 1 year
    user_data_retention_days: int = 1095  # 3 years
    
    # Privacy settings
    data_anonymization: bool = True
    right_to_be_forgotten: bool = True
    data_portability: bool = True
    consent_management: bool = True

# Default security configuration
DEFAULT_SECURITY_CONFIG = SecurityConfig()
DEFAULT_THREAT_DETECTION_CONFIG = ThreatDetectionConfig()
DEFAULT_HONEYPOT_CONFIG = HoneypotConfig()
DEFAULT_INCIDENT_RESPONSE_CONFIG = IncidentResponseConfig()
DEFAULT_COMPLIANCE_CONFIG = ComplianceConfig()

# Security rule templates
SECURITY_RULE_TEMPLATES = {
    "sql_injection": {
        "name": "SQL Injection Detection",
        "patterns": [
            r"union\s+.*\s+select",
            r"(and|or)\s+\d+\s*=\s*\d+",
            r"drop\s+table",
            r"insert\s+into.*values",
            r"update\s+.*\s+set"
        ],
        "severity": ThreatLevel.HIGH,
        "response_actions": [ResponseAction.BLOCK_IP, ResponseAction.LOG]
    },
    "xss": {
        "name": "Cross-Site Scripting Detection",
        "patterns": [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"document\.cookie",
            r"alert\s*\("
        ],
        "severity": ThreatLevel.HIGH,
        "response_actions": [ResponseAction.BLOCK_IP, ResponseAction.LOG]
    },
    "brute_force": {
        "name": "Brute Force Attack Detection",
        "threshold": 5,
        "time_window": 300,
        "severity": ThreatLevel.MEDIUM,
        "response_actions": [ResponseAction.RATE_LIMIT, ResponseAction.BLOCK_IP]
    },
    "reconnaissance": {
        "name": "Reconnaissance Detection",
        "patterns": [
            r"robots\.txt",
            r"sitemap\.xml",
            r"\.htaccess",
            r"server-status",
            r"phpinfo"
        ],
        "severity": ThreatLevel.LOW,
        "response_actions": [ResponseAction.MONITOR, ResponseAction.LOG]
    }
}

# Threat intelligence feed configurations
THREAT_INTEL_FEEDS = {
    "internal": {
        "enabled": True,
        "update_interval": 3600,
        "priority": 1
    },
    "commercial": {
        "enabled": False,
        "update_interval": 1800,
        "priority": 2,
        "feeds": []
    },
    "osint": {
        "enabled": True,
        "update_interval": 3600,
        "priority": 3,
        "feeds": []
    }
}

def get_security_config() -> SecurityConfig:
    """Get the current security configuration"""
    return DEFAULT_SECURITY_CONFIG

def get_threat_detection_config() -> ThreatDetectionConfig:
    """Get the threat detection configuration"""
    return DEFAULT_THREAT_DETECTION_CONFIG

def get_honeypot_config() -> HoneypotConfig:
    """Get the honeypot configuration"""
    return DEFAULT_HONEYPOT_CONFIG

def get_incident_response_config() -> IncidentResponseConfig:
    """Get the incident response configuration"""
    return DEFAULT_INCIDENT_RESPONSE_CONFIG

def get_compliance_config() -> ComplianceConfig:
    """Get the compliance configuration"""
    return DEFAULT_COMPLIANCE_CONFIG