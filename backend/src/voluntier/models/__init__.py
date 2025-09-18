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