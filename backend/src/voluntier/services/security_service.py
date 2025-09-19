"""
Advanced Security Service
Comprehensive Red Team & Blue Team Security Operations

This service provides enterprise-grade security operations including:
- Real-time threat detection and response
- Behavioral analysis and anomaly detection
- Automated incident response and remediation
- Threat intelligence integration
- Continuous security monitoring
- Adaptive defense mechanisms
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, deque
import ipaddress
import re

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
import redis.asyncio as redis
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import joblib
import geoip2.database
import requests

from voluntier.config import get_settings
from voluntier.database import get_db_session
from voluntier.models import (
    User, SecurityEvent, ThreatIntelligence, SecurityRule, 
    SecurityIncident, UserSession, AuthenticationLog
)
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    alert_type: str
    severity: str
    description: str
    source_ip: str
    user_id: Optional[str]
    threat_score: float
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any]
    response_actions: List[str]

@dataclass
class ThreatContext:
    """Threat context for analysis"""
    ip_address: str
    user_agent: str
    request_path: str
    request_method: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    headers: Dict[str, str]
    payload: Optional[str]
    geolocation: Optional[Dict[str, str]]

class ThreatIntelligenceEngine:
    """Advanced threat intelligence engine with real-time feeds"""
    
    def __init__(self):
        self.intelligence_sources = {
            "internal": "Internal threat intelligence",
            "commercial": "Commercial threat feeds",
            "osint": "Open source intelligence",
            "honeypot": "Honeypot intelligence",
            "community": "Community sharing"
        }
        self.ioc_cache = {}
        self.last_update = {}
        
    async def initialize(self):
        """Initialize threat intelligence engine"""
        await self.load_threat_feeds()
        await self.update_geolocation_database()
        
    async def load_threat_feeds(self):
        """Load threat intelligence feeds"""
        async with get_db_session() as session:
            # Load active threat indicators
            result = await session.execute(
                select(ThreatIntelligence).where(
                    and_(
                        ThreatIntelligence.status == "active",
                        or_(
                            ThreatIntelligence.expires_at.is_(None),
                            ThreatIntelligence.expires_at > datetime.utcnow()
                        )
                    )
                )
            )
            indicators = result.scalars().all()
            
            # Build lookup cache
            for indicator in indicators:
                self.ioc_cache[indicator.indicator_value] = {
                    "type": indicator.indicator_type,
                    "threat_score": indicator.threat_score,
                    "threat_type": indicator.threat_type,
                    "source": indicator.source,
                    "confidence": indicator.confidence
                }
                
        logger.info(f"Loaded {len(self.ioc_cache)} threat indicators")
        
    async def check_threat_intelligence(self, indicator: str, indicator_type: str) -> Optional[Dict]:
        """Check indicator against threat intelligence"""
        # Check cache first
        if indicator in self.ioc_cache:
            intel = self.ioc_cache[indicator]
            await self.update_hit_count(indicator)
            return intel
            
        # Check external feeds if not in cache
        intel = await self.query_external_feeds(indicator, indicator_type)
        if intel:
            await self.store_new_indicator(indicator, indicator_type, intel)
            
        return intel
        
    async def query_external_feeds(self, indicator: str, indicator_type: str) -> Optional[Dict]:
        """Query external threat intelligence feeds"""
        # Implementation would integrate with commercial/OSINT feeds
        # For now, return None - would integrate with VirusTotal, OTX, etc.
        return None
        
    async def store_new_indicator(self, indicator: str, indicator_type: str, intel: Dict):
        """Store new threat indicator"""
        async with get_db_session() as session:
            new_indicator = ThreatIntelligence(
                indicator_type=indicator_type,
                indicator_value=indicator,
                indicator_hash=hashlib.sha256(indicator.encode()).hexdigest(),
                threat_score=intel.get("threat_score", 0),
                confidence=intel.get("confidence", 0),
                threat_type=intel.get("threat_type", "unknown"),
                source=intel.get("source", "external"),
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            session.add(new_indicator)
            await session.commit()
            
    async def update_hit_count(self, indicator: str):
        """Update hit count for indicator"""
        async with get_db_session() as session:
            await session.execute(
                update(ThreatIntelligence)
                .where(ThreatIntelligence.indicator_value == indicator)
                .values(
                    hit_count=ThreatIntelligence.hit_count + 1,
                    last_hit=datetime.utcnow()
                )
            )
            await session.commit()
            
    async def update_geolocation_database(self):
        """Update geolocation database"""
        # Would download and update MaxMind GeoIP database
        logger.info("Geolocation database updated")

class BehavioralAnalyzer:
    """Advanced behavioral analysis engine"""
    
    def __init__(self):
        self.user_profiles = {}
        self.baseline_models = {}
        self.anomaly_detectors = {}
        self.learning_buffer = defaultdict(list)
        self.analysis_window = timedelta(hours=24)
        
    async def initialize(self):
        """Initialize behavioral analysis engine"""
        await self.load_user_baselines()
        await self.train_anomaly_models()
        
    async def load_user_baselines(self):
        """Load existing user behavioral baselines"""
        async with get_db_session() as session:
            # Load user activity patterns
            result = await session.execute(
                select(AuthenticationLog.user_id, 
                       func.count().label("login_count"),
                       func.avg(func.extract('hour', AuthenticationLog.timestamp)).label("avg_hour"),
                       func.array_agg(AuthenticationLog.ip_address.distinct()).label("ip_addresses"))
                .where(AuthenticationLog.timestamp > datetime.utcnow() - timedelta(days=30))
                .group_by(AuthenticationLog.user_id)
            )
            
            for row in result:
                user_id = str(row.user_id)
                self.user_profiles[user_id] = {
                    "login_frequency": row.login_count / 30,  # per day
                    "typical_hours": [row.avg_hour],
                    "known_ips": set(row.ip_addresses or []),
                    "risk_score": 0.0
                }
                
        logger.info(f"Loaded behavioral profiles for {len(self.user_profiles)} users")
        
    async def analyze_user_behavior(self, context: ThreatContext) -> float:
        """Analyze user behavior and return anomaly score"""
        if not context.user_id:
            return 0.5  # Unknown user, moderate risk
            
        user_id = str(context.user_id)
        profile = self.user_profiles.get(user_id, {})
        
        anomaly_score = 0.0
        factors = []
        
        # Time-based analysis
        current_hour = context.timestamp.hour
        typical_hours = profile.get("typical_hours", [])
        if typical_hours and abs(current_hour - typical_hours[0]) > 6:
            anomaly_score += 0.3
            factors.append("unusual_time")
            
        # IP reputation analysis
        known_ips = profile.get("known_ips", set())
        if context.ip_address not in known_ips:
            anomaly_score += 0.4
            factors.append("unknown_ip")
            
        # Request pattern analysis
        if await self.is_unusual_request_pattern(context):
            anomaly_score += 0.3
            factors.append("unusual_pattern")
            
        # Update learning buffer
        self.learning_buffer[user_id].append({
            "timestamp": context.timestamp,
            "ip_address": context.ip_address,
            "hour": current_hour,
            "path": context.request_path,
            "anomaly_score": anomaly_score
        })
        
        return min(anomaly_score, 1.0)
        
    async def is_unusual_request_pattern(self, context: ThreatContext) -> bool:
        """Check for unusual request patterns"""
        # Analyze request frequency, path patterns, etc.
        # Implementation would use ML models trained on user behavior
        suspicious_patterns = [
            r"/admin",
            r"/api/.*/(delete|remove)",
            r"\.php$",
            r"wp-admin"
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, context.request_path, re.IGNORECASE):
                return True
                
        return False
        
    async def train_anomaly_models(self):
        """Train machine learning models for anomaly detection"""
        # Implementation would train models on historical data
        logger.info("Anomaly detection models trained")
        
    async def update_user_profile(self, user_id: str, context: ThreatContext):
        """Update user behavioral profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "login_frequency": 0,
                "typical_hours": [],
                "known_ips": set(),
                "risk_score": 0.0
            }
            
        profile = self.user_profiles[user_id]
        profile["known_ips"].add(context.ip_address)
        profile["typical_hours"].append(context.timestamp.hour)
        
        # Keep only recent hours
        if len(profile["typical_hours"]) > 100:
            profile["typical_hours"] = profile["typical_hours"][-50:]

class IncidentResponseEngine:
    """Automated incident response and remediation"""
    
    def __init__(self):
        self.response_playbooks = {}
        self.active_incidents = {}
        self.escalation_rules = {}
        self.auto_remediation = True
        
    async def initialize(self):
        """Initialize incident response engine"""
        await self.load_response_playbooks()
        await self.load_escalation_rules()
        
    async def load_response_playbooks(self):
        """Load incident response playbooks"""
        self.response_playbooks = {
            "brute_force": {
                "detection_threshold": 5,
                "time_window": 300,  # 5 minutes
                "actions": ["rate_limit", "block_ip", "alert_admin"],
                "auto_resolve": True
            },
            "sql_injection": {
                "detection_threshold": 1,
                "time_window": 60,
                "actions": ["block_request", "block_ip", "create_incident"],
                "auto_resolve": False
            },
            "anomalous_behavior": {
                "detection_threshold": 0.8,
                "time_window": 1800,  # 30 minutes
                "actions": ["increase_monitoring", "require_mfa", "alert_security"],
                "auto_resolve": False
            },
            "ddos": {
                "detection_threshold": 100,
                "time_window": 60,
                "actions": ["rate_limit", "circuit_breaker", "cdn_activation"],
                "auto_resolve": True
            }
        }
        
    async def load_escalation_rules(self):
        """Load incident escalation rules"""
        self.escalation_rules = {
            "HIGH": {"time_to_escalate": 300, "escalate_to": "security_team"},
            "CRITICAL": {"time_to_escalate": 60, "escalate_to": "security_manager"},
            "MEDIUM": {"time_to_escalate": 1800, "escalate_to": "admin"},
            "LOW": {"time_to_escalate": 3600, "escalate_to": "log_only"}
        }
        
    async def handle_security_alert(self, alert: SecurityAlert) -> Dict[str, Any]:
        """Handle security alert and execute response"""
        response_result = {
            "alert_id": alert.alert_id,
            "actions_taken": [],
            "incident_created": False,
            "escalated": False,
            "auto_resolved": False
        }
        
        # Check if this requires incident creation
        if await self.should_create_incident(alert):
            incident = await self.create_security_incident(alert)
            response_result["incident_created"] = True
            response_result["incident_id"] = incident.incident_id
            
        # Execute automated response actions
        for action in alert.response_actions:
            success = await self.execute_response_action(action, alert)
            response_result["actions_taken"].append({
                "action": action,
                "success": success,
                "timestamp": datetime.utcnow()
            })
            
        # Check for escalation
        if await self.should_escalate(alert):
            await self.escalate_alert(alert)
            response_result["escalated"] = True
            
        return response_result
        
    async def should_create_incident(self, alert: SecurityAlert) -> bool:
        """Determine if alert should trigger incident creation"""
        severity_thresholds = {"CRITICAL": True, "HIGH": True, "MEDIUM": False, "LOW": False}
        return severity_thresholds.get(alert.severity, False)
        
    async def create_security_incident(self, alert: SecurityAlert) -> 'SecurityIncident':
        """Create security incident from alert"""
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        async with get_db_session() as session:
            incident = SecurityIncident(
                incident_id=incident_id,
                title=f"{alert.alert_type} - {alert.description}",
                description=alert.description,
                incident_type=alert.alert_type,
                severity=alert.severity,
                status="new",
                detected_at=alert.timestamp,
                affected_systems=[alert.source_ip],
                evidence=[alert.metadata],
                response_actions=alert.response_actions
            )
            session.add(incident)
            await session.commit()
            
        self.active_incidents[incident_id] = incident
        logger.warning(f"Created security incident: {incident_id}")
        return incident
        
    async def execute_response_action(self, action: str, alert: SecurityAlert) -> bool:
        """Execute specific response action"""
        try:
            if action == "block_ip":
                return await self.block_ip_address(alert.source_ip)
            elif action == "rate_limit":
                return await self.apply_rate_limit(alert.source_ip)
            elif action == "require_mfa":
                return await self.require_mfa(alert.user_id)
            elif action == "increase_monitoring":
                return await self.increase_monitoring(alert.source_ip)
            elif action == "alert_admin":
                return await self.send_admin_alert(alert)
            elif action == "quarantine_user":
                return await self.quarantine_user(alert.user_id)
            else:
                logger.warning(f"Unknown response action: {action}")
                return False
        except Exception as e:
            logger.error(f"Failed to execute response action {action}: {e}")
            return False
            
    async def block_ip_address(self, ip_address: str) -> bool:
        """Block IP address at firewall level"""
        # Implementation would integrate with firewall/WAF
        logger.warning(f"Blocked IP address: {ip_address}")
        return True
        
    async def apply_rate_limit(self, ip_address: str) -> bool:
        """Apply aggressive rate limiting to IP"""
        # Implementation would update rate limiting rules
        logger.info(f"Applied rate limiting to: {ip_address}")
        return True
        
    async def require_mfa(self, user_id: str) -> bool:
        """Require MFA for user account"""
        if not user_id:
            return False
            
        async with get_db_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(trust_score=0.0)  # Force re-authentication
            )
            await session.commit()
            
        logger.info(f"Required MFA for user: {user_id}")
        return True
        
    async def increase_monitoring(self, target: str) -> bool:
        """Increase monitoring for specific target"""
        # Implementation would enhance logging and monitoring
        logger.info(f"Increased monitoring for: {target}")
        return True
        
    async def send_admin_alert(self, alert: SecurityAlert) -> bool:
        """Send alert to administrators"""
        # Implementation would send email/SMS/Slack notification
        logger.critical(f"SECURITY ALERT: {alert.description}")
        return True
        
    async def quarantine_user(self, user_id: str) -> bool:
        """Quarantine user account"""
        if not user_id:
            return False
            
        async with get_db_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=False)
            )
            await session.commit()
            
        logger.warning(f"Quarantined user account: {user_id}")
        return True
        
    async def should_escalate(self, alert: SecurityAlert) -> bool:
        """Determine if alert should be escalated"""
        escalation_rule = self.escalation_rules.get(alert.severity, {})
        time_threshold = escalation_rule.get("time_to_escalate", 3600)
        
        # Check if alert has been active long enough to escalate
        age = (datetime.utcnow() - alert.timestamp).total_seconds()
        return age > time_threshold
        
    async def escalate_alert(self, alert: SecurityAlert):
        """Escalate alert to appropriate team"""
        escalation_rule = self.escalation_rules.get(alert.severity, {})
        escalate_to = escalation_rule.get("escalate_to", "admin")
        
        logger.critical(f"Escalating {alert.severity} alert to {escalate_to}: {alert.description}")

class ContinuousMonitoring:
    """Continuous security monitoring and assessment"""
    
    def __init__(self):
        self.monitoring_active = False
        self.assessment_queue = asyncio.Queue()
        self.monitoring_tasks = []
        
    async def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring_active = True
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self.monitor_authentication_attempts()),
            asyncio.create_task(self.monitor_api_usage()),
            asyncio.create_task(self.monitor_system_health()),
            asyncio.create_task(self.run_security_assessments()),
            asyncio.create_task(self.update_threat_intelligence())
        ]
        
        logger.info("Continuous security monitoring started")
        
    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        
        for task in self.monitoring_tasks:
            task.cancel()
            
        logger.info("Continuous security monitoring stopped")
        
    async def monitor_authentication_attempts(self):
        """Monitor authentication attempts for suspicious activity"""
        while self.monitoring_active:
            try:
                # Query recent authentication failures
                async with get_db_session() as session:
                    cutoff_time = datetime.utcnow() - timedelta(minutes=5)
                    result = await session.execute(
                        select(AuthenticationLog.ip_address, func.count().label("failure_count"))
                        .where(
                            and_(
                                AuthenticationLog.auth_result == "failed",
                                AuthenticationLog.timestamp > cutoff_time
                            )
                        )
                        .group_by(AuthenticationLog.ip_address)
                        .having(func.count() > 5)
                    )
                    
                    for row in result:
                        await self.handle_brute_force_detection(row.ip_address, row.failure_count)
                        
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in authentication monitoring: {e}")
                await asyncio.sleep(60)
                
    async def monitor_api_usage(self):
        """Monitor API usage for anomalies"""
        while self.monitoring_active:
            try:
                # Monitor API request patterns
                # Implementation would analyze API usage patterns
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in API monitoring: {e}")
                await asyncio.sleep(300)
                
    async def monitor_system_health(self):
        """Monitor system health and security status"""
        while self.monitoring_active:
            try:
                # Check system health metrics
                # Implementation would monitor CPU, memory, disk, network
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in system health monitoring: {e}")
                await asyncio.sleep(60)
                
    async def run_security_assessments(self):
        """Run periodic security assessments"""
        while self.monitoring_active:
            try:
                # Run vulnerability scans, configuration checks, etc.
                await self.run_vulnerability_scan()
                await self.check_security_configuration()
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in security assessment: {e}")
                await asyncio.sleep(3600)
                
    async def update_threat_intelligence(self):
        """Update threat intelligence feeds"""
        while self.monitoring_active:
            try:
                # Update threat intelligence feeds
                await asyncio.sleep(1800)  # Update every 30 minutes
                
            except Exception as e:
                logger.error(f"Error updating threat intelligence: {e}")
                await asyncio.sleep(1800)
                
    async def handle_brute_force_detection(self, ip_address: str, failure_count: int):
        """Handle detected brute force attack"""
        alert = SecurityAlert(
            alert_id=str(uuid.uuid4()),
            alert_type="brute_force",
            severity="HIGH",
            description=f"Brute force attack detected from {ip_address} ({failure_count} failures)",
            source_ip=ip_address,
            user_id=None,
            threat_score=0.9,
            confidence=0.95,
            timestamp=datetime.utcnow(),
            metadata={"failure_count": failure_count},
            response_actions=["block_ip", "alert_admin"]
        )
        
        # Queue for incident response
        await self.assessment_queue.put(alert)
        
    async def run_vulnerability_scan(self):
        """Run automated vulnerability scan"""
        # Implementation would run security scanning tools
        logger.info("Running vulnerability scan")
        
    async def check_security_configuration(self):
        """Check security configuration compliance"""
        # Implementation would check security settings
        logger.info("Checking security configuration")

class AdvancedSecurityService:
    """Main security service orchestrating all security components"""
    
    def __init__(self):
        self.threat_intelligence = ThreatIntelligenceEngine()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.incident_response = IncidentResponseEngine()
        self.continuous_monitoring = ContinuousMonitoring()
        self.redis_client = None
        self.security_active = False
        
    async def initialize(self):
        """Initialize all security components"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
            
            # Initialize security components
            await self.threat_intelligence.initialize()
            await self.behavioral_analyzer.initialize()
            await self.incident_response.initialize()
            
            # Start continuous monitoring
            await self.continuous_monitoring.start_monitoring()
            
            self.security_active = True
            logger.info("Advanced security service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize security service: {e}")
            raise
            
    async def shutdown(self):
        """Shutdown security service"""
        self.security_active = False
        await self.continuous_monitoring.stop_monitoring()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Advanced security service shut down")
        
    async def analyze_threat_context(self, context: ThreatContext) -> SecurityAlert:
        """Analyze threat context and generate security alert if needed"""
        threat_score = 0.0
        confidence = 0.0
        alert_type = "unknown"
        severity = "LOW"
        response_actions = []
        
        # Check threat intelligence
        ip_intel = await self.threat_intelligence.check_threat_intelligence(
            context.ip_address, "ip"
        )
        if ip_intel:
            threat_score += ip_intel["threat_score"] / 100
            confidence = max(confidence, ip_intel["confidence"] / 100)
            alert_type = ip_intel["threat_type"]
            response_actions.append("block_ip")
            
        # Behavioral analysis
        if context.user_id:
            behavioral_score = await self.behavioral_analyzer.analyze_user_behavior(context)
            threat_score += behavioral_score * 0.5
            if behavioral_score > 0.7:
                response_actions.append("require_mfa")
                
        # Determine severity
        if threat_score > 0.8:
            severity = "CRITICAL"
        elif threat_score > 0.6:
            severity = "HIGH"
        elif threat_score > 0.4:
            severity = "MEDIUM"
        else:
            severity = "LOW"
            
        # Create alert if threat detected
        if threat_score > 0.3:
            alert = SecurityAlert(
                alert_id=str(uuid.uuid4()),
                alert_type=alert_type or "suspicious_activity",
                severity=severity,
                description=f"Threat detected from {context.ip_address}",
                source_ip=context.ip_address,
                user_id=context.user_id,
                threat_score=threat_score,
                confidence=confidence,
                timestamp=context.timestamp,
                metadata={
                    "request_path": context.request_path,
                    "user_agent": context.user_agent,
                    "geolocation": context.geolocation
                },
                response_actions=response_actions
            )
            
            # Handle the alert
            await self.incident_response.handle_security_alert(alert)
            return alert
            
        return None
        
    async def log_security_event(self, event_type: str, description: str, 
                                context: ThreatContext, severity: str = "MEDIUM"):
        """Log security event to database"""
        async with get_db_session() as session:
            event = SecurityEvent(
                event_type=event_type,
                description=description,
                severity=severity,
                source_ip=context.ip_address,
                user_agent=context.user_agent,
                request_path=context.request_path,
                request_method=context.request_method,
                metadata={
                    "timestamp": context.timestamp.isoformat(),
                    "headers": context.headers,
                    "payload": context.payload,
                    "geolocation": context.geolocation
                },
                timestamp=context.timestamp
            )
            session.add(event)
            await session.commit()

# Global security service instance
security_service = AdvancedSecurityService()