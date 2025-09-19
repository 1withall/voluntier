"""
Security API Routes
Comprehensive Security Management and Monitoring API

This module provides API endpoints for:
- Security monitoring and alerting
- Threat intelligence management
- Incident response and management
- Security metrics and reporting
- Honeypot management
- Attack attribution and analysis
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from voluntier.database import get_db_session
from voluntier.models import (
    SecurityEvent, ThreatIntelligence, SecurityRule, SecurityIncident,
    User, AuthenticationLog, UserSession
)
from voluntier.services.security_service import security_service
from voluntier.services.threat_detection import threat_detection_system
from voluntier.services.honeypot_system import honeypot_manager
from voluntier.middleware.security import SecurityUtils
from voluntier.utils.logging import get_logger
from voluntier.dependencies import get_current_user, require_admin
from voluntier.services.audit_service import audit_privileged_operation
from voluntier.services.validation_service import (
    input_validator, IncidentCreateRequest, SecurityEventFilter, ThreatIntelligenceCreate
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/security", tags=["security"])

# Pydantic models for API requests/responses
class SecurityEventResponse(BaseModel):
    id: str
    event_type: str
    severity: str
    description: str
    source_ip: str
    timestamp: datetime
    threat_score: float
    metadata: Dict[str, Any]

class ThreatIntelligenceResponse(BaseModel):
    id: str
    indicator_type: str
    indicator_value: str
    threat_score: float
    threat_type: str
    source: str
    first_seen: datetime
    last_seen: datetime
    hit_count: int

class SecurityIncidentResponse(BaseModel):
    id: str
    incident_id: str
    title: str
    severity: str
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime]
    assigned_to: Optional[str]
    affected_systems: List[str]

class SecurityMetricsResponse(BaseModel):
    timeframe: str
    total_events: int
    critical_events: int
    high_events: int
    medium_events: int
    low_events: int
    unique_attackers: int
    blocked_attempts: int
    honeypot_hits: int
    threat_intelligence_hits: int

class ThreatAnalysisRequest(BaseModel):
    ip_address: str
    user_agent: str
    request_path: str
    request_method: str
    headers: Dict[str, str] = {}
    payload: Optional[str] = None
    user_id: Optional[str] = None

class IncidentCreateRequest(BaseModel):
    title: str
    description: str
    incident_type: str
    severity: str
    affected_systems: List[str] = []
    evidence: List[Dict[str, Any]] = []

class ThreatIntelligenceCreateRequest(BaseModel):
    indicator_type: str
    indicator_value: str
    threat_type: str
    threat_score: float
    confidence: float
    source: str
    description: Optional[str] = None

# Security dashboard endpoints
@router.get("/dashboard", response_model=Dict[str, Any])
async def get_security_dashboard(
    timeframe: str = Query("24h", description="Timeframe: 1h, 24h, 7d, 30d"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Get comprehensive security dashboard data"""
    
    # Parse timeframe
    if timeframe == "1h":
        cutoff = datetime.utcnow() - timedelta(hours=1)
    elif timeframe == "24h":
        cutoff = datetime.utcnow() - timedelta(days=1)
    elif timeframe == "7d":
        cutoff = datetime.utcnow() - timedelta(days=7)
    elif timeframe == "30d":
        cutoff = datetime.utcnow() - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="Invalid timeframe")
    
    # Get security events summary
    events_query = await session.execute(
        select(
            SecurityEvent.severity,
            func.count().label("count")
        )
        .where(SecurityEvent.timestamp > cutoff)
        .group_by(SecurityEvent.severity)
    )
    events_by_severity = {row.severity: row.count for row in events_query}
    
    # Get unique attackers
    attackers_query = await session.execute(
        select(func.count(func.distinct(SecurityEvent.source_ip)))
        .where(SecurityEvent.timestamp > cutoff)
    )
    unique_attackers = attackers_query.scalar() or 0
    
    # Get top attack types
    attack_types_query = await session.execute(
        select(
            SecurityEvent.event_type,
            func.count().label("count")
        )
        .where(SecurityEvent.timestamp > cutoff)
        .group_by(SecurityEvent.event_type)
        .order_by(desc("count"))
        .limit(10)
    )
    top_attack_types = [
        {"type": row.event_type, "count": row.count}
        for row in attack_types_query
    ]
    
    # Get threat intelligence statistics
    threat_intel_stats = await honeypot_manager.get_honeypot_statistics()
    detection_stats = await threat_detection_system.get_detection_statistics()
    
    return {
        "timeframe": timeframe,
        "summary": {
            "total_events": sum(events_by_severity.values()),
            "critical_events": events_by_severity.get("CRITICAL", 0),
            "high_events": events_by_severity.get("HIGH", 0),
            "medium_events": events_by_severity.get("MEDIUM", 0),
            "low_events": events_by_severity.get("LOW", 0),
            "unique_attackers": unique_attackers
        },
        "attack_types": top_attack_types,
        "threat_intelligence": {
            "honeypot_hits": threat_intel_stats["total_hits"],
            "unique_honeypot_attackers": threat_intel_stats["unique_attackers"],
            "detection_rate": detection_stats["detection_rate"]
        },
        "system_status": {
            "threat_detection_active": detection_stats["ml_models_trained"],
            "honeypots_deployed": threat_intel_stats["total_honeypots"],
            "security_rules_active": True
        }
    }

    # Audit the privileged operation
    from fastapi import Request
    # Note: In a real implementation, you'd get the request object from the endpoint parameters
    # For now, we'll log without the IP (it would be passed from the middleware)
    await audit_privileged_operation(
        user_id=str(current_user.id),
        client_ip="unknown",  # Would be passed from middleware
        resource="security_dashboard",
        action="view_dashboard",
        details={"timeframe": timeframe}
    )

    return result

@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    filters: SecurityEventFilter = Depends(),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Get security events with filtering options"""
    
    query = select(SecurityEvent).order_by(desc(SecurityEvent.timestamp))
    
    # Apply filters
    query_filters = []
    if filters.severity:
        query_filters.append(SecurityEvent.severity == filters.severity)
    if filters.event_type:
        query_filters.append(SecurityEvent.event_type == filters.event_type)
    if filters.source_ip:
        query_filters.append(SecurityEvent.source_ip == filters.source_ip)
    if filters.since:
        query_filters.append(SecurityEvent.timestamp > filters.since)

    if query_filters:
        query = query.where(and_(*query_filters))

    query = query.limit(filters.limit).offset(filters.offset)
    
    result = await session.execute(query)
    events = result.scalars().all()
    
    return [
        SecurityEventResponse(
            id=str(event.id),
            event_type=event.event_type,
            severity=event.severity,
            description=event.description,
            source_ip=event.source_ip or "",
            timestamp=event.timestamp,
            threat_score=event.threat_score or 0.0,
            metadata=event.metadata or {}
        )
        for event in events
    ]

@router.post("/analyze-threat", response_model=Dict[str, Any])
async def analyze_threat(
    request: ThreatAnalysisRequest,
    current_user: User = Depends(require_admin)
):
    """Analyze a potential threat using all detection engines"""
    
    # Prepare threat context
    from voluntier.services.security_service import ThreatContext
    
    context = ThreatContext(
        ip_address=request.ip_address,
        user_agent=request.user_agent,
        request_path=request.request_path,
        request_method=request.request_method,
        timestamp=datetime.utcnow(),
        user_id=request.user_id,
        session_id=None,
        headers=request.headers,
        payload=request.payload,
        geolocation=None
    )
    
    # Analyze using security service
    alert = await security_service.analyze_threat_context(context)
    
    # Also run through threat detection system
    request_data = {
        "ip_address": request.ip_address,
        "user_agent": request.user_agent,
        "request_path": request.request_path,
        "request_method": request.request_method,
        "headers": request.headers,
        "payload": request.payload,
        "user_id": request.user_id
    }
    
    detection_result = await threat_detection_system.analyze_threat(request_data)
    
    return {
        "threat_detected": detection_result["threat_detected"],
        "threat_score": detection_result["threat_score"],
        "confidence": detection_result["confidence"],
        "threat_types": detection_result["threat_types"],
        "ml_analysis": detection_result["ml_analysis"],
        "behavioral_analysis": detection_result["behavioral_analysis"],
        "signature_matches": detection_result["signature_matches"],
        "recommendations": detection_result["recommendations"],
        "alert_generated": alert is not None,
        "analysis_time": detection_result["analysis_time"]
    }

@router.get("/incidents", response_model=List[SecurityIncidentResponse])
async def get_security_incidents(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Get security incidents with filtering"""
    
    query = select(SecurityIncident).order_by(desc(SecurityIncident.detected_at))
    
    # Apply filters
    filters = []
    if status:
        filters.append(SecurityIncident.status == status)
    if severity:
        filters.append(SecurityIncident.severity == severity)
        
    if filters:
        query = query.where(and_(*filters))
        
    query = query.limit(limit).offset(offset)
    
    result = await session.execute(query)
    incidents = result.scalars().all()
    
    return [
        SecurityIncidentResponse(
            id=str(incident.id),
            incident_id=incident.incident_id,
            title=incident.title,
            severity=incident.severity,
            status=incident.status,
            detected_at=incident.detected_at,
            resolved_at=incident.resolved_at,
            assigned_to=incident.assigned_to,
            affected_systems=incident.affected_systems or []
        )
        for incident in incidents
    ]

@router.post("/incidents", response_model=Dict[str, str])
async def create_security_incident(
    request: IncidentCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Create a new security incident"""
    
    incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    incident = SecurityIncident(
        incident_id=incident_id,
        title=request.title,
        description=request.description,
        incident_type=request.incident_type,
        severity=request.severity,
        status="new",
        detected_at=datetime.utcnow(),
        affected_systems=request.affected_systems,
        evidence=request.evidence
    )
    
    session.add(incident)
    await session.commit()
    
    logger.warning(f"Security incident created: {incident_id}")
    
    return {"incident_id": incident_id, "status": "created"}

@router.get("/threat-intelligence", response_model=List[ThreatIntelligenceResponse])
async def get_threat_intelligence(
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    indicator_type: Optional[str] = Query(None),
    threat_type: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Get threat intelligence indicators"""
    
    query = select(ThreatIntelligence).order_by(desc(ThreatIntelligence.last_seen))
    
    # Apply filters
    filters = [ThreatIntelligence.status == "active"]
    
    if indicator_type:
        filters.append(ThreatIntelligence.indicator_type == indicator_type)
    if threat_type:
        filters.append(ThreatIntelligence.threat_type == threat_type)
    if min_score is not None:
        filters.append(ThreatIntelligence.threat_score >= min_score)
        
    query = query.where(and_(*filters)).limit(limit).offset(offset)
    
    result = await session.execute(query)
    indicators = result.scalars().all()
    
    return [
        ThreatIntelligenceResponse(
            id=str(indicator.id),
            indicator_type=indicator.indicator_type,
            indicator_value=indicator.indicator_value,
            threat_score=indicator.threat_score,
            threat_type=indicator.threat_type or "",
            source=indicator.source,
            first_seen=indicator.first_seen,
            last_seen=indicator.last_seen,
            hit_count=indicator.hit_count
        )
        for indicator in indicators
    ]

@router.post("/threat-intelligence", response_model=Dict[str, str])
async def add_threat_intelligence(
    request: ThreatIntelligenceCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Add new threat intelligence indicator"""
    
    # Check if indicator already exists
    existing = await session.execute(
        select(ThreatIntelligence)
        .where(ThreatIntelligence.indicator_value == request.indicator_value)
    )
    
    if existing.scalar():
        raise HTTPException(status_code=409, detail="Indicator already exists")
    
    indicator = ThreatIntelligence(
        indicator_type=request.indicator_type,
        indicator_value=request.indicator_value,
        indicator_hash=SecurityUtils.generate_secure_token(),
        threat_score=request.threat_score,
        confidence=request.confidence,
        threat_type=request.threat_type,
        source=request.source,
        description=request.description,
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
        status="active"
    )
    
    session.add(indicator)
    await session.commit()
    
    return {"id": str(indicator.id), "status": "created"}

@router.get("/honeypots/stats", response_model=Dict[str, Any])
async def get_honeypot_statistics(current_user: User = Depends(require_admin)):
    """Get honeypot deployment and hit statistics"""
    return await honeypot_manager.get_honeypot_statistics()

@router.post("/honeypots/deploy", response_model=Dict[str, str])
async def deploy_honeypot(
    path: str = Body(..., description="Honeypot path"),
    response_type: str = Body(..., description="Response type"),
    threat_level: str = Body("MEDIUM", description="Threat level"),
    intelligence_value: str = Body("MEDIUM", description="Intelligence value"),
    current_user: User = Depends(require_admin)
):
    """Deploy a new honeypot endpoint"""
    
    honeypot_id = await honeypot_manager.deploy_honeypot(
        path=path,
        response_type=response_type,
        threat_level=threat_level,
        intelligence_value=intelligence_value
    )
    
    return {"honeypot_id": honeypot_id, "status": "deployed"}

@router.get("/authentication/logs", response_model=List[Dict[str, Any]])
async def get_authentication_logs(
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    result: Optional[str] = Query(None, description="Filter by auth result"),
    ip_address: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Get authentication logs with filtering"""
    
    query = select(AuthenticationLog).order_by(desc(AuthenticationLog.timestamp))
    
    # Apply filters
    filters = []
    if result:
        filters.append(AuthenticationLog.auth_result == result)
    if ip_address:
        filters.append(AuthenticationLog.ip_address == ip_address)
    if since:
        filters.append(AuthenticationLog.timestamp > since)
        
    if filters:
        query = query.where(and_(*filters))
        
    query = query.limit(limit).offset(offset)
    
    result = await session.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "username": log.username,
            "auth_result": log.auth_result,
            "failure_reason": log.failure_reason,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "timestamp": log.timestamp,
            "risk_score": log.risk_score,
            "blocked": log.blocked
        }
        for log in logs
    ]

@router.get("/sessions/active", response_model=List[Dict[str, Any]])
async def get_active_sessions(
    limit: int = Query(100, le=500),
    high_risk_only: bool = Query(False),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Get active user sessions"""
    
    query = select(UserSession).where(UserSession.is_active == True)
    
    if high_risk_only:
        query = query.where(UserSession.risk_score > 0.6)
        
    query = query.order_by(desc(UserSession.last_activity)).limit(limit)
    
    result = await session.execute(query)
    sessions = result.scalars().all()
    
    return [
        {
            "id": str(session.id),
            "user_id": str(session.user_id),
            "ip_address": session.ip_address,
            "device_type": session.device_type,
            "last_activity": session.last_activity,
            "risk_score": session.risk_score,
            "suspicious_activity": session.suspicious_activity,
            "auth_method": session.auth_method,
            "mfa_verified": session.mfa_verified
        }
        for session in sessions
    ]

@router.post("/sessions/{session_id}/terminate")
async def terminate_session(
    session_id: str,
    reason: str = Body(..., description="Termination reason"),
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Terminate a user session"""
    
    session_uuid = uuid.UUID(session_id)
    
    result = await db_session.execute(
        select(UserSession).where(UserSession.id == session_uuid)
    )
    user_session = result.scalar()
    
    if not user_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    user_session.is_active = False
    user_session.terminated_at = datetime.utcnow()
    
    await db_session.commit()
    
    logger.warning(f"Session terminated: {session_id}, reason: {reason}")
    
    return {"status": "terminated", "reason": reason}

@router.get("/metrics/summary", response_model=SecurityMetricsResponse)
async def get_security_metrics(
    timeframe: str = Query("24h", description="Timeframe: 1h, 24h, 7d, 30d"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    """Get security metrics summary"""
    
    # Parse timeframe
    if timeframe == "1h":
        cutoff = datetime.utcnow() - timedelta(hours=1)
    elif timeframe == "24h":
        cutoff = datetime.utcnow() - timedelta(days=1)
    elif timeframe == "7d":
        cutoff = datetime.utcnow() - timedelta(days=7)
    elif timeframe == "30d":
        cutoff = datetime.utcnow() - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="Invalid timeframe")
    
    # Get events by severity
    events_query = await session.execute(
        select(
            SecurityEvent.severity,
            func.count().label("count")
        )
        .where(SecurityEvent.timestamp > cutoff)
        .group_by(SecurityEvent.severity)
    )
    events_by_severity = {row.severity: row.count for row in events_query}
    
    # Get unique attackers
    attackers_query = await session.execute(
        select(func.count(func.distinct(SecurityEvent.source_ip)))
        .where(SecurityEvent.timestamp > cutoff)
    )
    unique_attackers = attackers_query.scalar() or 0
    
    # Get blocked attempts
    blocked_query = await session.execute(
        select(func.count())
        .select_from(AuthenticationLog)
        .where(
            and_(
                AuthenticationLog.timestamp > cutoff,
                AuthenticationLog.blocked == True
            )
        )
    )
    blocked_attempts = blocked_query.scalar() or 0
    
    # Get honeypot hits
    honeypot_query = await session.execute(
        select(func.count())
        .select_from(SecurityEvent)
        .where(
            and_(
                SecurityEvent.timestamp > cutoff,
                SecurityEvent.event_type == "HONEYPOT_HIT"
            )
        )
    )
    honeypot_hits = honeypot_query.scalar() or 0
    
    # Get threat intelligence hits
    ti_query = await session.execute(
        select(func.sum(ThreatIntelligence.hit_count))
        .where(ThreatIntelligence.last_hit > cutoff)
    )
    ti_hits = ti_query.scalar() or 0
    
    return SecurityMetricsResponse(
        timeframe=timeframe,
        total_events=sum(events_by_severity.values()),
        critical_events=events_by_severity.get("CRITICAL", 0),
        high_events=events_by_severity.get("HIGH", 0),
        medium_events=events_by_severity.get("MEDIUM", 0),
        low_events=events_by_severity.get("LOW", 0),
        unique_attackers=unique_attackers,
        blocked_attempts=blocked_attempts,
        honeypot_hits=honeypot_hits,
        threat_intelligence_hits=ti_hits
    )

@router.post("/rules/test", response_model=Dict[str, Any])
async def test_security_rule(
    rule_logic: Dict[str, Any] = Body(...),
    test_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_admin)
):
    """Test a security rule against sample data"""
    
    # Simple rule evaluation - in production this would be more sophisticated
    try:
        # This is a simplified implementation
        # Real implementation would use a proper rule engine
        
        result = {
            "rule_triggered": False,
            "matched_conditions": [],
            "score": 0.0,
            "recommendations": []
        }
        
        # Test basic conditions
        conditions = rule_logic.get("conditions", [])
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            test_value = test_data.get(field)
            
            if operator == "equals" and test_value == value:
                result["matched_conditions"].append(condition)
                result["score"] += 0.3
            elif operator == "contains" and value in str(test_value):
                result["matched_conditions"].append(condition)
                result["score"] += 0.3
            elif operator == "greater_than" and float(test_value or 0) > float(value):
                result["matched_conditions"].append(condition)
                result["score"] += 0.3
                
        if result["matched_conditions"]:
            result["rule_triggered"] = True
            result["recommendations"] = ["monitor", "investigate"]
            
        return result
        
    except Exception as e:
        logger.error(f"Error testing security rule: {e}")
        raise HTTPException(status_code=400, detail="Invalid rule or test data")

# Include the router in the main application
def get_security_router():
    return router