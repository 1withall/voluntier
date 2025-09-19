"""
Comprehensive Audit Logging Service
Tracks all privileged operations and security events for compliance and monitoring.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, and_, desc, func
import structlog

from voluntier.database import get_db_session
from voluntier.models import User, SecurityEvent
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Types of audit events to track."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SECURITY_OPERATION = "security_operation"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_ACCESS = "api_access"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str]
    username: Optional[str]
    user_role: Optional[str]
    client_ip: str
    user_agent: Optional[str]
    resource: str
    action: str
    success: bool
    details: Dict[str, Any]
    risk_score: Optional[float] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AuditService:
    """Service for comprehensive audit logging."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self._audit_queue = asyncio.Queue()
        self._processing_task = None

    async def initialize(self):
        """Initialize the audit service."""
        self._processing_task = asyncio.create_task(self._process_audit_queue())
        self.logger.info("Audit service initialized")

    async def shutdown(self):
        """Shutdown the audit service."""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Audit service shutdown")

    async def log_event(self, event: AuditEvent):
        """Log an audit event asynchronously."""
        await self._audit_queue.put(event)

    async def log_security_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        client_ip: str,
        resource: str,
        action: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        user_agent: Optional[str] = None,
        risk_score: Optional[float] = None,
        session_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM
    ):
        """Convenience method to log security events."""
        # Get user details if user_id is provided
        username = None
        user_role = None

        if user_id:
            async for session in get_db_session():
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if user:
                    username = user.email
                    user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            username=username,
            user_role=user_role,
            client_ip=client_ip,
            user_agent=user_agent,
            resource=resource,
            action=action,
            success=success,
            details=details or {},
            risk_score=risk_score,
            session_id=session_id
        )

        await self.log_event(event)

    async def _process_audit_queue(self):
        """Process audit events from the queue."""
        while True:
            try:
                event = await self._audit_queue.get()

                # Log to structured logger
                self.logger.info(
                    "Audit event",
                    event_type=event.event_type.value,
                    severity=event.severity.value,
                    user_id=event.user_id,
                    username=event.username,
                    user_role=event.user_role,
                    client_ip=event.client_ip,
                    resource=event.resource,
                    action=event.action,
                    success=event.success,
                    risk_score=event.risk_score,
                    details=json.dumps(event.details)
                )

                # Store in database for compliance
                await self._store_audit_event(event)

                self._audit_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing audit event: {e}")

    async def _store_audit_event(self, event: AuditEvent):
        """Store audit event in database."""
        try:
            async for session in get_db_session():
                # Create security event record
                security_event = SecurityEvent(
                    event_type=f"audit:{event.event_type.value}",
                    severity=event.severity.value.upper(),
                    description=f"Audit: {event.action} on {event.resource}",
                    source_ip=event.client_ip,
                    user_id=event.user_id,
                    metadata={
                        "username": event.username,
                        "user_role": event.user_role,
                        "user_agent": event.user_agent,
                        "resource": event.resource,
                        "action": event.action,
                        "success": event.success,
                        "details": event.details,
                        "risk_score": event.risk_score,
                        "session_id": event.session_id
                    }
                )

                session.add(security_event)
                await session.commit()

        except Exception as e:
            self.logger.error(f"Error storing audit event in database: {e}")

    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering."""
        try:
            async for session in get_db_session():
                query = select(SecurityEvent).where(
                    SecurityEvent.event_type.like("audit:%")
                )

                # Apply filters
                if user_id:
                    query = query.where(SecurityEvent.user_id == user_id)
                if event_type:
                    query = query.where(SecurityEvent.event_type == f"audit:{event_type.value}")
                if severity:
                    query = query.where(SecurityEvent.severity == severity.value.upper())
                if start_date:
                    query = query.where(SecurityEvent.timestamp >= start_date)
                if end_date:
                    query = query.where(SecurityEvent.timestamp <= end_date)

                query = query.order_by(desc(SecurityEvent.timestamp)).limit(limit).offset(offset)

                result = await session.execute(query)
                events = result.scalars().all()

                return [
                    {
                        "id": str(event.id),
                        "event_type": event.event_type.replace("audit:", ""),
                        "severity": event.severity,
                        "user_id": str(event.user_id) if event.user_id else None,
                        "client_ip": event.source_ip,
                        "timestamp": event.timestamp.isoformat(),
                        "description": event.description,
                        "metadata": event.metadata
                    }
                    for event in events
                ]

        except Exception as e:
            self.logger.error(f"Error retrieving audit logs: {e}")
            return []


# Global audit service instance
audit_service = AuditService()


# Convenience functions for common audit operations
async def audit_auth_success(user_id: str, client_ip: str, user_agent: str = None):
    """Audit successful authentication."""
    await audit_service.log_security_event(
        event_type=AuditEventType.AUTHENTICATION,
        user_id=user_id,
        client_ip=client_ip,
        resource="authentication",
        action="login_success",
        success=True,
        user_agent=user_agent,
        severity=AuditSeverity.LOW
    )


async def audit_auth_failure(client_ip: str, username: str = None, user_agent: str = None):
    """Audit failed authentication."""
    await audit_service.log_security_event(
        event_type=AuditEventType.AUTHENTICATION,
        user_id=None,
        client_ip=client_ip,
        resource="authentication",
        action="login_failure",
        success=False,
        details={"attempted_username": username},
        user_agent=user_agent,
        severity=AuditSeverity.MEDIUM
    )


async def audit_privileged_operation(
    user_id: str,
    client_ip: str,
    resource: str,
    action: str,
    details: Dict[str, Any] = None,
    risk_score: float = None
):
    """Audit privileged operations."""
    severity = AuditSeverity.HIGH if risk_score and risk_score > 0.7 else AuditSeverity.MEDIUM

    await audit_service.log_security_event(
        event_type=AuditEventType.SECURITY_OPERATION,
        user_id=user_id,
        client_ip=client_ip,
        resource=resource,
        action=action,
        success=True,
        details=details,
        risk_score=risk_score,
        severity=severity
    )


async def audit_suspicious_activity(
    user_id: str,
    client_ip: str,
    activity: str,
    details: Dict[str, Any] = None,
    risk_score: float = 0.8
):
    """Audit suspicious activities."""
    await audit_service.log_security_event(
        event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
        user_id=user_id,
        client_ip=client_ip,
        resource="security",
        action=activity,
        success=False,
        details=details,
        risk_score=risk_score,
        severity=AuditSeverity.HIGH
    )