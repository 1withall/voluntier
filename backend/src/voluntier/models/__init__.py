"""Database models for Voluntier platform."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Float,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum


Base = declarative_base()


class VerificationStatus(enum.Enum):
    """Verification status enumeration."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class EventStatus(enum.Enum):
    """Event status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UserRole(enum.Enum):
    """User role enumeration."""
    VOLUNTEER = "volunteer"
    ORGANIZATION = "organization"
    ADMIN = "admin"
    MODERATOR = "moderator"


class User(Base):
    """User model for volunteers and organizations."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.VOLUNTEER, nullable=False)
    
    # Profile information
    bio = Column(Text)
    avatar_url = Column(String(500))
    phone = Column(String(20))
    location = Column(String(255))
    timezone = Column(String(50), default="UTC")
    
    # Skills and interests (JSON arrays)
    skills = Column(JSON, default=list)
    interests = Column(JSON, default=list)
    
    # Verification and trust
    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING)
    verification_date = Column(DateTime(timezone=True))
    trust_score = Column(Float, default=0.0)
    
    # Zero-trust authentication fields
    hardware_token_credentials = Column(JSON, default=dict)  # WebAuthn/FIDO2 credentials
    biometric_data = Column(JSON, default=dict)  # Biometric templates and metadata
    risk_score = Column(Float, default=0.0)  # Dynamic risk assessment score
    mfa_settings = Column(JSON, default=dict)  # MFA configuration and preferences
    device_trust_levels = Column(JSON, default=dict)  # Trusted device registry
    last_biometric_verification = Column(DateTime(timezone=True))
    password_last_changed = Column(DateTime(timezone=True))
    account_lockout_until = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    security_questions = Column(JSON, default=list)  # Encrypted security questions
    recovery_codes = Column(JSON, default=list)  # Backup recovery codes
    
    # Statistics
    hours_logged = Column(Float, default=0.0)
    events_attended = Column(Integer, default=0)
    events_organized = Column(Integer, default=0)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active = Column(DateTime(timezone=True))
    
    # Relationships
    organized_events = relationship("Event", back_populates="organizer", foreign_keys="Event.organizer_id")
    registrations = relationship("EventRegistration", back_populates="user")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    received_messages = relationship("Message", back_populates="recipient", foreign_keys="Message.recipient_id")


class Organization(Base):
    """Organization model for non-profits and community groups."""
    
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Organization details
    legal_name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    website = Column(String(500))
    logo_url = Column(String(500))
    
    # Contact information
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    address = Column(Text)
    
    # Registration and verification
    tax_id = Column(String(50))
    registration_number = Column(String(100))
    verification_documents = Column(JSON, default=list)
    
    # Categories and focus areas
    categories = Column(JSON, default=list)
    focus_areas = Column(JSON, default=list)
    
    # Statistics
    total_volunteers = Column(Integer, default=0)
    total_hours_facilitated = Column(Float, default=0.0)
    total_events = Column(Integer, default=0)
    
    # Verification
    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING)
    verification_date = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="organization")
    events = relationship("Event", back_populates="organization")


class Event(Base):
    """Event model for volunteer opportunities."""
    
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    short_description = Column(String(500))
    
    # Scheduling
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True))
    timezone = Column(String(50), default="UTC")
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON)  # For recurring events
    
    # Location
    location_name = Column(String(255))
    location_address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    is_remote = Column(Boolean, default=False)
    
    # Volunteer requirements
    volunteers_needed = Column(Integer, nullable=False)
    volunteers_registered = Column(Integer, default=0)
    volunteers_attended = Column(Integer, default=0)
    min_age = Column(Integer)
    max_age = Column(Integer)
    
    # Skills and categories
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    categories = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    
    # Event management
    status = Column(SQLEnum(EventStatus), default=EventStatus.DRAFT)
    registration_deadline = Column(DateTime(timezone=True))
    is_featured = Column(Boolean, default=False)
    
    # Impact and tracking
    estimated_impact = Column(Text)
    actual_impact = Column(Text)
    impact_metrics = Column(JSON, default=dict)
    
    # Verification and moderation
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text)
    moderation_status = Column(String(50), default="pending")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    organizer = relationship("User", back_populates="organized_events", foreign_keys=[organizer_id])
    organization = relationship("Organization", back_populates="events")
    registrations = relationship("EventRegistration", back_populates="event")
    messages = relationship("Message", back_populates="event")


class EventRegistration(Base):
    """Registration model for volunteer event signups."""
    
    __tablename__ = "event_registrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    
    # Registration details
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="registered")  # registered, confirmed, attended, no_show, cancelled
    
    # Volunteer preferences
    availability_notes = Column(Text)
    special_requirements = Column(Text)
    emergency_contact = Column(JSON)
    
    # Attendance tracking
    checked_in = Column(Boolean, default=False)
    check_in_time = Column(DateTime(timezone=True))
    check_out_time = Column(DateTime(timezone=True))
    hours_contributed = Column(Float, default=0.0)
    
    # Feedback and ratings
    volunteer_rating = Column(Integer)  # 1-5 scale
    volunteer_feedback = Column(Text)
    organizer_rating = Column(Integer)  # 1-5 scale
    organizer_feedback = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")


class Message(Base):
    """Message model for communication between users."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    
    # Message content
    subject = Column(String(255))
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="direct")  # direct, event, broadcast, system
    
    # Message status
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    recipient = relationship("User", back_populates="received_messages", foreign_keys=[recipient_id])
    event = relationship("Event", back_populates="messages")


class AuditLog(Base):
    """Audit log model for tracking system events and user actions."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Event details
    event_type = Column(String(100), nullable=False)  # user_created, event_published, etc.
    resource_type = Column(String(50))  # user, event, organization
    resource_id = Column(UUID(as_uuid=True))
    
    # Change tracking
    old_values = Column(JSON)
    new_values = Column(JSON)
    changes = Column(JSON)
    
    # Request context
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_id = Column(String(100))
    
    # Additional metadata
    metadata = Column(JSON, default=dict)
    severity = Column(String(20), default="info")  # debug, info, warning, error, critical
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="audit_logs")


class SystemMetrics(Base):
    """System metrics model for tracking platform performance and usage."""
    
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric details
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    value = Column(Float, nullable=False)
    
    # Dimensions and labels
    dimensions = Column(JSON, default=dict)
    labels = Column(JSON, default=dict)
    
    # Timestamp and retention
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    retention_days = Column(Integer, default=90)
    
    # Metadata
    source = Column(String(100))
    description = Column(Text)
    unit = Column(String(20))


class SecurityEvent(Base):
    """Security event model for tracking security incidents and threats."""
    
    __tablename__ = "security_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event classification
    event_type = Column(String(100), nullable=False)  # HONEYPOT_HIT, ANOMALY_DETECTED, BRUTE_FORCE, etc.
    category = Column(String(50), nullable=False)  # authentication, input_validation, network, etc.
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Event details
    description = Column(Text, nullable=False)
    source_ip = Column(String(45))
    user_agent = Column(String(500))
    request_path = Column(String(1000))
    request_method = Column(String(10))
    
    # Attack details
    attack_vector = Column(String(100))  # sql_injection, xss, brute_force, etc.
    attack_signature = Column(Text)
    payload = Column(Text)
    
    # Response and mitigation
    response_action = Column(String(100))  # blocked, monitored, honeypot, rate_limited
    mitigation_status = Column(String(50), default="pending")  # pending, applied, failed
    mitigation_details = Column(JSON)
    
    # Threat intelligence
    threat_score = Column(Float, default=0.0)
    confidence_level = Column(Float, default=0.0)
    false_positive = Column(Boolean, default=False)
    
    # Geolocation and network
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    organization = Column(String(255))
    asn = Column(String(20))
    
    # Machine Learning features
    anomaly_score = Column(Float)
    feature_vector = Column(JSON)
    model_version = Column(String(50))
    
    # Metadata and context
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    related_events = Column(JSON, default=list)
    
    # Investigation and resolution
    investigated = Column(Boolean, default=False)
    investigation_notes = Column(Text)
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user = relationship("User", backref="security_events")


class ThreatIntelligence(Base):
    """Threat intelligence model for storing IOCs and threat data."""
    
    __tablename__ = "threat_intelligence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Indicator details
    indicator_type = Column(String(50), nullable=False)  # ip, domain, hash, url, email
    indicator_value = Column(String(1000), nullable=False)
    indicator_hash = Column(String(64))  # SHA256 hash for deduplication
    
    # Threat classification
    threat_type = Column(String(100))  # malware, phishing, botnet, scanner, etc.
    threat_family = Column(String(100))
    threat_category = Column(String(50))  # targeted, opportunistic, reconnaissance
    
    # Threat scoring
    threat_score = Column(Float, default=0.0)  # 0-100 scale
    confidence = Column(Float, default=0.0)  # 0-100 scale
    severity = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Source and attribution
    source = Column(String(100), nullable=False)  # internal, commercial_feed, osint, etc.
    source_reliability = Column(String(20))  # A, B, C, D, E, F
    attribution = Column(String(255))  # Threat actor or group
    
    # Temporal data
    first_seen = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    
    # Status and validation
    status = Column(String(20), default="active")  # active, expired, false_positive, deprecated
    validated = Column(Boolean, default=False)
    validation_date = Column(DateTime(timezone=True))
    
    # Geolocation (for IP indicators)
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    organization = Column(String(255))
    asn = Column(String(20))
    
    # Context and relationships
    tags = Column(JSON, default=list)
    related_indicators = Column(JSON, default=list)
    campaign_id = Column(String(100))
    
    # Detection and response
    detection_rules = Column(JSON, default=list)
    response_actions = Column(JSON, default=list)
    kill_chain_phase = Column(String(50))
    
    # Metadata
    metadata = Column(JSON, default=dict)
    description = Column(Text)
    references = Column(JSON, default=list)
    
    # Usage statistics
    hit_count = Column(Integer, default=0)
    last_hit = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SecurityRule(Base):
    """Security rule model for defining detection and response rules."""
    
    __tablename__ = "security_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule identification
    rule_name = Column(String(255), nullable=False, unique=True)
    rule_id = Column(String(100), nullable=False, unique=True)
    version = Column(String(20), default="1.0")
    
    # Rule classification
    rule_type = Column(String(50), nullable=False)  # detection, response, prevention
    category = Column(String(100))  # network, application, authentication, etc.
    subcategory = Column(String(100))
    
    # Rule logic
    rule_logic = Column(JSON, nullable=False)  # Detection logic/conditions
    pattern = Column(Text)  # Regex or signature pattern
    threshold = Column(Float)  # Threshold for triggering
    
    # MITRE ATT&CK mapping
    attack_techniques = Column(JSON, default=list)
    attack_tactics = Column(JSON, default=list)
    
    # Response configuration
    response_actions = Column(JSON, default=list)  # Actions to take when triggered
    severity = Column(String(20), default="MEDIUM")
    priority = Column(Integer, default=50)
    
    # Rule status and control
    enabled = Column(Boolean, default=True)
    testing_mode = Column(Boolean, default=False)  # Don't execute actions, just log
    
    # Performance and tuning
    false_positive_rate = Column(Float, default=0.0)
    effectiveness_score = Column(Float, default=0.0)
    last_tuned = Column(DateTime(timezone=True))
    
    # Metadata
    description = Column(Text)
    author = Column(String(255))
    references = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    
    # Usage statistics
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SecurityIncident(Base):
    """Security incident model for tracking and managing security incidents."""
    
    __tablename__ = "security_incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Incident identification
    incident_id = Column(String(50), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Classification
    incident_type = Column(String(100), nullable=False)  # data_breach, malware, ddos, etc.
    category = Column(String(50))  # security, availability, integrity, confidentiality
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, URGENT
    
    # Status and workflow
    status = Column(String(50), default="new")  # new, investigating, contained, resolved, closed
    resolution = Column(String(100))  # false_positive, resolved, mitigated, etc.
    
    # Impact assessment
    impact_scope = Column(String(100))  # single_user, multiple_users, system_wide, external
    affected_systems = Column(JSON, default=list)
    affected_users = Column(JSON, default=list)
    estimated_impact = Column(Text)
    
    # Timeline
    detected_at = Column(DateTime(timezone=True), nullable=False)
    occurred_at = Column(DateTime(timezone=True))
    reported_at = Column(DateTime(timezone=True))
    contained_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Assignment and ownership
    assigned_to = Column(String(255))
    team = Column(String(100))
    escalated = Column(Boolean, default=False)
    escalation_reason = Column(Text)
    
    # Evidence and artifacts
    evidence = Column(JSON, default=list)
    artifacts = Column(JSON, default=list)
    indicators = Column(JSON, default=list)
    
    # Response and mitigation
    response_actions = Column(JSON, default=list)
    mitigation_steps = Column(JSON, default=list)
    lessons_learned = Column(Text)
    
    # Investigation details
    investigation_notes = Column(Text)
    root_cause = Column(Text)
    attribution = Column(String(255))
    
    # Related data
    related_events = Column(JSON, default=list)
    related_incidents = Column(JSON, default=list)
    parent_incident_id = Column(UUID(as_uuid=True), ForeignKey("security_incidents.id"))
    
    # Compliance and reporting
    regulatory_notification_required = Column(Boolean, default=False)
    regulatory_notifications = Column(JSON, default=list)
    external_reporting = Column(JSON, default=list)
    
    # Cost and metrics
    estimated_cost = Column(Float)
    recovery_time = Column(Integer)  # Minutes
    downtime = Column(Integer)  # Minutes
    
    # Metadata
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assignee = relationship("User", backref="assigned_incidents")
    child_incidents = relationship("SecurityIncident", backref="parent_incident", remote_side=[id])


class UserSession(Base):
    """User session model for tracking active sessions and authentication."""
    
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session identification
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    refresh_token = Column(String(255), unique=True, index=True)
    device_fingerprint = Column(String(255))
    
    # Hardware token and biometric session data
    hardware_token_id = Column(String(255))  # Associated hardware token
    biometric_session_id = Column(String(255))  # Biometric session identifier
    encrypted_session_key = Column(String(500))  # Encrypted session key for zero-trust
    session_signature = Column(String(500))  # Cryptographic signature of session
    
    # Session details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    device_type = Column(String(50))  # mobile, desktop, tablet
    browser = Column(String(100))
    os = Column(String(100))
    
    # Geolocation
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    
    # Session status
    is_active = Column(Boolean, default=True)
    is_trusted = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    
    # Authentication details
    auth_method = Column(String(50))  # password, mfa, oauth, hardware_token, biometric, etc.
    mfa_verified = Column(Boolean, default=False)
    auth_factors = Column(JSON, default=list)
    
    # Zero-trust session security
    session_risk_score = Column(Float, default=0.0)  # Session-specific risk assessment
    behavioral_biometrics = Column(JSON, default=dict)  # Keystroke patterns, mouse movements
    continuous_auth_score = Column(Float, default=1.0)  # Continuous authentication confidence
    last_auth_verification = Column(DateTime(timezone=True))
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    terminated_at = Column(DateTime(timezone=True))
    
    # Security events
    suspicious_activity = Column(Boolean, default=False)
    security_alerts = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", backref="sessions")


class AuthenticationLog(Base):
    """Authentication log model for tracking login attempts and security events."""
    
    __tablename__ = "authentication_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Authentication attempt details
    username = Column(String(255))  # Email or username attempted
    auth_method = Column(String(50))  # password, oauth, mfa, etc.
    auth_result = Column(String(50), nullable=False)  # success, failed, blocked, etc.
    failure_reason = Column(String(100))  # invalid_password, account_locked, etc.
    
    # Request context
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    source = Column(String(100))  # web, mobile_app, api, etc.
    
    # Geolocation
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    
    # Risk assessment
    risk_score = Column(Float, default=0.0)
    risk_factors = Column(JSON, default=list)
    blocked = Column(Boolean, default=False)
    
    # MFA details
    mfa_required = Column(Boolean, default=False)
    mfa_method = Column(String(50))
    mfa_success = Column(Boolean)
    
    # Session details
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"))
    device_fingerprint = Column(String(255))
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="auth_logs")
    session = relationship("UserSession", backref="auth_logs")