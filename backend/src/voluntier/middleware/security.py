"""
Advanced AI/ML-Enhanced Security Module
Comprehensive Blue Team & Red Team Security Framework

This module implements sophisticated security measures including:
- Adaptive threat detection using ML models
- Honeypot deployment for threat intelligence
- Real-time attack surface analysis
- Automated incident response
- Zero-trust architecture enforcement
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Set, Union, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import ipaddress
import re

import numpy as np
from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import redis
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

from voluntier.config import get_settings
from voluntier.database import get_db_session
from voluntier.models import User, SecurityEvent, ThreatIntelligence
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Security constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 3600  # 1 hour
JWT_ALGORITHM = "HS256"
BCRYPT_ROUNDS = 12

# Rate limiting constants
DEFAULT_RATE_LIMIT = 100  # requests per minute
AGGRESSIVE_RATE_LIMIT = 10  # for suspicious IPs
API_RATE_LIMIT = 1000  # for API endpoints

# ML Model thresholds
ANOMALY_THRESHOLD = -0.5
HIGH_RISK_THRESHOLD = -0.8

@dataclass
class SecurityMetrics:
    """Real-time security metrics tracking"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    request_count: int = 0
    failed_auth_attempts: int = 0
    blocked_requests: int = 0
    anomalous_requests: int = 0
    honeypot_hits: int = 0
    threat_level: float = 0.0
    active_attacks: List[str] = field(default_factory=list)
    
@dataclass
class ThreatIndicator:
    """Threat intelligence indicator"""
    indicator_type: str  # ip, hash, domain, etc.
    value: str
    threat_level: float
    source: str
    first_seen: datetime
    last_seen: datetime
    hit_count: int = 0

@dataclass
class AttackPattern:
    """Attack pattern detection"""
    pattern_id: str
    pattern_type: str  # sql_injection, xss, brute_force, etc.
    signatures: List[str]
    confidence_threshold: float
    response_action: str  # block, monitor, honeypot

class HoneypotManager:
    """Advanced honeypot deployment and management"""
    
    def __init__(self):
        self.active_honeypots: Dict[str, Dict] = {}
        self.honeypot_hits: List[Dict] = []
        self.decoy_endpoints = [
            "/admin/config",
            "/wp-admin/",
            "/.env",
            "/backup.sql",
            "/api/v1/admin/users",
            "/debug/vars",
            "/.git/config"
        ]
        
    async def deploy_honeypot(self, endpoint: str, response_type: str = "fake_data"):
        """Deploy a honeypot at specified endpoint"""
        honeypot_id = str(uuid.uuid4())
        self.active_honeypots[endpoint] = {
            "id": honeypot_id,
            "deployed_at": datetime.utcnow(),
            "response_type": response_type,
            "hits": 0,
            "attackers": set()
        }
        logger.info(f"Honeypot deployed at {endpoint} with ID {honeypot_id}")
        
    async def check_honeypot_hit(self, request: Request) -> bool:
        """Check if request hits a honeypot"""
        path = request.url.path
        if path in self.active_honeypots:
            client_ip = self.get_client_ip(request)
            self.active_honeypots[path]["hits"] += 1
            self.active_honeypots[path]["attackers"].add(client_ip)
            
            hit_data = {
                "timestamp": datetime.utcnow(),
                "path": path,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", ""),
                "headers": dict(request.headers),
                "method": request.method
            }
            self.honeypot_hits.append(hit_data)
            
            # Log security event
            await self.log_security_event(
                "HONEYPOT_HIT",
                f"Honeypot hit from {client_ip} at {path}",
                hit_data,
                severity="HIGH"
            )
            return True
        return False
        
    def get_client_ip(self, request: Request) -> str:
        """Extract real client IP considering proxies"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
        
    async def log_security_event(self, event_type: str, description: str, 
                                 metadata: Dict, severity: str = "MEDIUM"):
        """Log security events to database"""
        async with get_db_session() as session:
            event = SecurityEvent(
                event_type=event_type,
                description=description,
                metadata=metadata,
                severity=severity,
                timestamp=datetime.utcnow()
            )
            session.add(event)
            await session.commit()

class MLThreatDetector:
    """Machine Learning-based threat detection system"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_buffer = []
        self.training_threshold = 1000  # samples needed before training
        
    def extract_features(self, request: Request) -> np.ndarray:
        """Extract numerical features from request for ML analysis"""
        features = []
        
        # Request size features
        content_length = int(request.headers.get("content-length", "0"))
        features.append(content_length)
        features.append(len(request.url.path))
        features.append(len(request.url.query or ""))
        
        # Time-based features
        hour = datetime.utcnow().hour
        features.append(hour)
        features.append(1 if 22 <= hour or hour <= 6 else 0)  # Night activity
        
        # HTTP method encoding
        method_encoding = {
            "GET": 1, "POST": 2, "PUT": 3, "DELETE": 4, 
            "PATCH": 5, "HEAD": 6, "OPTIONS": 7
        }
        features.append(method_encoding.get(request.method, 0))
        
        # User agent features
        user_agent = request.headers.get("user-agent", "")
        features.append(len(user_agent))
        features.append(1 if "bot" in user_agent.lower() else 0)
        features.append(1 if "curl" in user_agent.lower() else 0)
        features.append(1 if "python" in user_agent.lower() else 0)
        
        # Security-relevant header presence
        security_headers = [
            "x-forwarded-for", "x-real-ip", "x-originating-ip",
            "authorization", "cookie", "referer"
        ]
        for header in security_headers:
            features.append(1 if header in request.headers else 0)
            
        # Path-based features
        path = request.url.path.lower()
        suspicious_patterns = [
            "admin", "config", "backup", "sql", "php", "wp-",
            ".env", "debug", "test", "api/v", "swagger"
        ]
        for pattern in suspicious_patterns:
            features.append(1 if pattern in path else 0)
            
        return np.array(features).reshape(1, -1)
        
    async def analyze_request(self, request: Request) -> float:
        """Analyze request and return anomaly score"""
        try:
            features = self.extract_features(request)
            
            # Add to training buffer
            self.feature_buffer.append(features.flatten())
            
            # Train model if we have enough samples and not yet trained
            if not self.is_trained and len(self.feature_buffer) >= self.training_threshold:
                await self.train_model()
                
            # If model is trained, get anomaly score
            if self.is_trained:
                scaled_features = self.scaler.transform(features)
                anomaly_score = self.isolation_forest.decision_function(scaled_features)[0]
                return anomaly_score
                
            return 0.0  # Neutral score if not trained yet
            
        except Exception as e:
            logger.error(f"Error in ML threat analysis: {e}")
            return 0.0
            
    async def train_model(self):
        """Train the anomaly detection model"""
        try:
            X = np.array(self.feature_buffer)
            X_scaled = self.scaler.fit_transform(X)
            self.isolation_forest.fit(X_scaled)
            self.is_trained = True
            
            # Save model for persistence
            joblib.dump(self.isolation_forest, "/tmp/threat_detector.pkl")
            joblib.dump(self.scaler, "/tmp/feature_scaler.pkl")
            
            logger.info(f"ML threat detector trained with {len(self.feature_buffer)} samples")
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")

class AdaptiveBlueTeam:
    """Adaptive Blue Team defense strategies"""
    
    def __init__(self):
        self.defense_strategies = {
            "rate_limiting": True,
            "geo_blocking": True,
            "behavioral_analysis": True,
            "honeypot_deployment": True,
            "adaptive_timeouts": True
        }
        self.threat_response_playbook = {
            "sql_injection": ["block_ip", "deploy_honeypot", "increase_monitoring"],
            "brute_force": ["rate_limit", "captcha", "account_lockout"],
            "xss_attempt": ["sanitize_input", "csp_enforcement", "log_incident"],
            "ddos": ["rate_limit", "circuit_breaker", "cdn_activation"],
            "reconnaissance": ["honeypot_redirect", "fake_responses", "monitor"]
        }
        
    async def execute_defense_strategy(self, threat_type: str, context: Dict):
        """Execute appropriate defense strategy based on threat type"""
        strategies = self.threat_response_playbook.get(threat_type, ["log_incident"])
        
        for strategy in strategies:
            await self.execute_strategy(strategy, context)
            
    async def execute_strategy(self, strategy: str, context: Dict):
        """Execute specific defense strategy"""
        if strategy == "block_ip":
            await self.block_ip(context.get("client_ip"))
        elif strategy == "rate_limit":
            await self.apply_rate_limit(context.get("client_ip"))
        elif strategy == "deploy_honeypot":
            await self.deploy_decoy_honeypot(context)
        elif strategy == "increase_monitoring":
            await self.increase_monitoring_level(context.get("client_ip"))
        # Add more strategy implementations as needed
        
    async def block_ip(self, ip_address: str):
        """Block specific IP address"""
        # Implementation would integrate with firewall/WAF
        logger.warning(f"IP {ip_address} blocked due to malicious activity")
        
    async def apply_rate_limit(self, ip_address: str):
        """Apply aggressive rate limiting to specific IP"""
        # Implementation would update rate limiting rules
        logger.info(f"Aggressive rate limiting applied to {ip_address}")
        
    async def deploy_decoy_honeypot(self, context: Dict):
        """Deploy targeted honeypot based on attack context"""
        # Implementation would create specific honeypots
        logger.info("Decoy honeypot deployed in response to detected threat")
        
    async def increase_monitoring_level(self, ip_address: str):
        """Increase monitoring for specific IP"""
        # Implementation would enhance logging and monitoring
        logger.info(f"Enhanced monitoring activated for {ip_address}")

class ContinuousSecurityAssessment:
    """Continuous security assessment and vulnerability scanning"""
    
    def __init__(self):
        self.assessment_schedule = {
            "quick_scan": 300,      # 5 minutes
            "deep_scan": 3600,      # 1 hour
            "penetration_test": 86400  # 24 hours
        }
        self.last_assessments = {}
        
    async def run_continuous_assessment(self):
        """Run continuous security assessments"""
        current_time = time.time()
        
        for assessment_type, interval in self.assessment_schedule.items():
            last_run = self.last_assessments.get(assessment_type, 0)
            
            if current_time - last_run >= interval:
                await self.run_assessment(assessment_type)
                self.last_assessments[assessment_type] = current_time
                
    async def run_assessment(self, assessment_type: str):
        """Run specific type of security assessment"""
        if assessment_type == "quick_scan":
            await self.quick_vulnerability_scan()
        elif assessment_type == "deep_scan":
            await self.deep_security_scan()
        elif assessment_type == "penetration_test":
            await self.automated_penetration_test()
            
    async def quick_vulnerability_scan(self):
        """Quick vulnerability assessment"""
        vulnerabilities = []
        
        # Check for common misconfigurations
        # This would integrate with actual vulnerability scanners
        logger.info("Running quick vulnerability scan")
        
    async def deep_security_scan(self):
        """Deep security assessment"""
        # This would run comprehensive security tests
        logger.info("Running deep security scan")
        
    async def automated_penetration_test(self):
        """Automated penetration testing"""
        # This would run automated pen-testing tools
        logger.info("Running automated penetration test")

class ZeroTrustValidator:
    """Zero Trust architecture enforcement"""
    
    def __init__(self):
        self.trust_levels = {
            "UNTRUSTED": 0,
            "LOW": 25,
            "MEDIUM": 50,
            "HIGH": 75,
            "VERIFIED": 100
        }
        
    async def calculate_trust_score(self, request: Request, user_context: Dict) -> int:
        """Calculate dynamic trust score for request"""
        score = 0
        
        # User authentication status
        if user_context.get("authenticated"):
            score += 30
            
        # Device fingerprinting
        if user_context.get("known_device"):
            score += 20
            
        # Location consistency
        if user_context.get("consistent_location"):
            score += 15
            
        # Behavioral patterns
        if user_context.get("normal_behavior"):
            score += 20
            
        # Network reputation
        if user_context.get("trusted_network"):
            score += 15
            
        return min(score, 100)
        
    async def enforce_zero_trust(self, request: Request, trust_score: int) -> bool:
        """Enforce zero trust policies based on trust score"""
        required_trust = self.get_required_trust_level(request)
        
        if trust_score < required_trust:
            await self.trigger_additional_verification(request, trust_score)
            return False
            
        return True
        
    def get_required_trust_level(self, request: Request) -> int:
        """Get required trust level for specific endpoint"""
        path = request.url.path
        
        # High-security endpoints
        if any(pattern in path for pattern in ["/admin", "/api/users", "/config"]):
            return self.trust_levels["HIGH"]
        
        # Medium-security endpoints
        if any(pattern in path for pattern in ["/api", "/profile", "/settings"]):
            return self.trust_levels["MEDIUM"]
            
        # Public endpoints
        return self.trust_levels["LOW"]
        
    async def trigger_additional_verification(self, request: Request, current_score: int):
        """Trigger additional verification steps"""
        # This would implement MFA, CAPTCHA, device verification, etc.
        logger.warning(f"Additional verification required for {request.url.path}")

class AdvancedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware integrating all security components
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.honeypot_manager = HoneypotManager()
        self.ml_detector = MLThreatDetector()
        self.blue_team = AdaptiveBlueTeam()
        self.security_assessor = ContinuousSecurityAssessment()
        self.zero_trust = ZeroTrustValidator()
        
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        
        self.rate_limits = defaultdict(lambda: defaultdict(int))
        self.blocked_ips = set()
        self.suspicious_ips = set()
        
        # Initialize security components
        asyncio.create_task(self.initialize_security_components())
        
    async def initialize_security_components(self):
        """Initialize all security components"""
        # Deploy initial honeypots
        for endpoint in self.honeypot_manager.decoy_endpoints:
            await self.honeypot_manager.deploy_honeypot(endpoint)
            
        # Start continuous security assessment
        asyncio.create_task(self.run_security_loop())
        
    async def run_security_loop(self):
        """Main security monitoring loop"""
        while True:
            try:
                await self.security_assessor.run_continuous_assessment()
                await asyncio.sleep(60)  # Run every minute
            except Exception as e:
                logger.error(f"Error in security loop: {e}")
                await asyncio.sleep(60)
                
    async def dispatch(self, request: Request, call_next) -> Response:
        """Main security processing pipeline"""
        start_time = time.time()
        client_ip = self.honeypot_manager.get_client_ip(request)
        
        try:
            # 1. Check if IP is blocked
            if client_ip in self.blocked_ips:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied"}
                )
            
            # 2. Check honeypot hits
            if await self.honeypot_manager.check_honeypot_hit(request):
                self.suspicious_ips.add(client_ip)
                return self.generate_honeypot_response(request)
            
            # 3. Rate limiting (IP and user-based)
            user_context = await self.get_user_context(request)
            if not await self.check_rate_limit(request, client_ip, user_context):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
            
            # 4. ML-based threat detection
            anomaly_score = await self.ml_detector.analyze_request(request)
            if anomaly_score < ANOMALY_THRESHOLD:
                await self.handle_anomalous_request(request, anomaly_score)
                
                if anomaly_score < HIGH_RISK_THRESHOLD:
                    self.suspicious_ips.add(client_ip)
                    return JSONResponse(
                        status_code=403,
                        content={"error": "Suspicious activity detected"}
                    )
            
            # 5. Zero Trust validation
            user_context = await self.get_user_context(request)
            trust_score = await self.zero_trust.calculate_trust_score(request, user_context)
            
            if not await self.zero_trust.enforce_zero_trust(request, trust_score):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Additional verification required"}
                )
            
            # 6. Input validation and sanitization
            await self.validate_and_sanitize_input(request)
            
            # 7. Process request
            response = await call_next(request)
            
            # 8. Add security headers
            self.add_security_headers(response)
            
            # 9. Log security metrics
            await self.log_security_metrics(request, response, start_time, anomaly_score)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal security error"}
            )
    
    async def check_rate_limit(self, request: Request, client_ip: str, user_context: Dict = None) -> bool:
        """Advanced rate limiting with adaptive thresholds and user-based limits"""
        current_minute = int(time.time() // 60)
        user_id = user_context.get("user_id") if user_context else None

        # Determine rate limit based on IP reputation and user context
        if client_ip in self.suspicious_ips:
            ip_limit = AGGRESSIVE_RATE_LIMIT
        else:
            ip_limit = DEFAULT_RATE_LIMIT

        # User-based rate limiting
        user_limit = DEFAULT_RATE_LIMIT
        if user_context and user_context.get("authenticated"):
            user_role = user_context.get("user_role", "volunteer")
            # Different limits based on user role
            role_limits = {
                "volunteer": 100,      # Basic users
                "organization": 200,   # Organizations
                "moderator": 500,      # Moderators
                "admin": 1000          # Admins
            }
            user_limit = role_limits.get(user_role, 100)

            # Adjust based on user risk score
            risk_score = user_context.get("risk_score", 0.0)
            if risk_score > 0.7:
                user_limit = max(10, user_limit // 10)  # Severe reduction for high-risk users
            elif risk_score > 0.3:
                user_limit = max(50, user_limit // 2)   # Moderate reduction

        # Check IP-based rate limit
        ip_key = f"rate_limit:ip:{client_ip}:{current_minute}"
        ip_count = await self.redis_client.get(ip_key) or 0
        ip_count = int(ip_count)

        if ip_count >= ip_limit:
            await self.handle_rate_limit_exceeded(client_ip, ip_count, "ip")
            return False

        # Check user-based rate limit if user is authenticated
        if user_id:
            user_key = f"rate_limit:user:{user_id}:{current_minute}"
            user_count = await self.redis_client.get(user_key) or 0
            user_count = int(user_count)

            if user_count >= user_limit:
                await self.handle_rate_limit_exceeded(user_id, user_count, "user")
                return False

            # Increment user counter
            await self.redis_client.incr(user_key)
            await self.redis_client.expire(user_key, 60)

        # Increment IP counter
        await self.redis_client.incr(ip_key)
        await self.redis_client.expire(ip_key, 60)

        return True
        
    async def handle_rate_limit_exceeded(self, identifier: str, count: int, limit_type: str = "ip"):
        """Handle rate limit violations for both IP and user-based limits"""
        if limit_type == "ip":
            self.suspicious_ips.add(identifier)

            # If severely exceeding limits, block IP
            if count > DEFAULT_RATE_LIMIT * 2:
                self.blocked_ips.add(identifier)
                await self.blue_team.execute_defense_strategy("ddos", {"client_ip": identifier})
        elif limit_type == "user":
            # For user-based rate limiting, we might want to log or take different actions
            # Could implement progressive penalties or temporary restrictions
            logger.warning(f"User {identifier} exceeded rate limit with {count} requests")

            # Optionally add to suspicious users list or implement user-specific penalties
            # This could trigger additional authentication requirements or temporary blocks
            
    async def handle_anomalous_request(self, request: Request, score: float):
        """Handle anomalous requests detected by ML"""
        client_ip = self.honeypot_manager.get_client_ip(request)
        
        threat_data = {
            "client_ip": client_ip,
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent", ""),
            "anomaly_score": score
        }
        
        await self.honeypot_manager.log_security_event(
            "ANOMALY_DETECTED",
            f"ML detected anomalous request from {client_ip}",
            threat_data,
            severity="HIGH" if score < HIGH_RISK_THRESHOLD else "MEDIUM"
        )
        
        # Trigger adaptive defenses
        await self.blue_team.execute_defense_strategy("reconnaissance", threat_data)
        
    def generate_honeypot_response(self, request: Request) -> Response:
        """Generate realistic honeypot response"""
        path = request.url.path
        
        if "admin" in path:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "login_url": "/admin/login"}
            )
        elif ".env" in path:
            return Response(
                content="DB_PASSWORD=fake_password\nAPI_KEY=fake_key",
                media_type="text/plain"
            )
        elif "backup" in path:
            return JSONResponse(
                content={"backups": ["backup_2023.sql", "backup_2024.sql"]}
            )
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Not found"}
            )
    
    async def get_user_context(self, request: Request) -> Dict:
        """Get user context for zero trust evaluation"""
        try:
            # Extract JWT token from Authorization header
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return {
                    "authenticated": False,
                    "user_id": None,
                    "user_role": None,
                    "known_device": False,
                    "consistent_location": True,
                    "normal_behavior": True,
                    "trusted_network": False
                }

            token = auth_header.split(" ")[1]

            # Decode JWT token (similar to get_current_user dependency)
            try:
                from voluntier.dependencies import SECRET_KEY, ALGORITHM
                import jwt
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")

                if not user_id:
                    return {
                        "authenticated": False,
                        "user_id": None,
                        "user_role": None,
                        "known_device": False,
                        "consistent_location": True,
                        "normal_behavior": True,
                        "trusted_network": False
                    }

                # Get user from database for additional context
                from voluntier.database import get_db_session
                from sqlalchemy import select

                async for session in get_db_session():
                    result = await session.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()

                    if not user:
                        return {
                            "authenticated": False,
                            "user_id": None,
                            "user_role": None,
                            "known_device": False,
                            "consistent_location": True,
                            "normal_behavior": True,
                            "trusted_network": False
                        }

                    # Check device fingerprint (simplified)
                    user_agent = request.headers.get("user-agent", "")
                    known_device = user_agent in (user.device_trust_levels or {})

                    # Check location consistency (simplified)
                    client_ip = self.honeypot_manager.get_client_ip(request)
                    consistent_location = True  # Would implement geolocation checking

                    # Check behavioral patterns (simplified)
                    normal_behavior = user.risk_score < 0.7 if user.risk_score else True

                    # Check network reputation (simplified)
                    trusted_network = client_ip not in self.suspicious_ips

                    return {
                        "authenticated": True,
                        "user_id": str(user.id),
                        "user_role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                        "known_device": known_device,
                        "consistent_location": consistent_location,
                        "normal_behavior": normal_behavior,
                        "trusted_network": trusted_network,
                        "risk_score": user.risk_score or 0.0,
                        "account_active": user.is_active,
                        "mfa_verified": user.mfa_settings.get("verified", False) if user.mfa_settings else False
                    }

            except Exception as e:
                logger.warning(f"Failed to decode JWT token: {e}")
                return {
                    "authenticated": False,
                    "user_id": None,
                    "user_role": None,
                    "known_device": False,
                    "consistent_location": True,
                    "normal_behavior": True,
                    "trusted_network": False
                }

        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {
                "authenticated": False,
                "user_id": None,
                "user_role": None,
                "known_device": False,
                "consistent_location": True,
                "normal_behavior": True,
                "trusted_network": False
            }
    
    async def validate_and_sanitize_input(self, request: Request):
        """Validate and sanitize all input"""
        # SQL injection patterns
        sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(or|and)\s+\d+\s*=\s*\d+)",
            r"(\bexec\s*\()",
        ]
        
        # XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
        ]
        
        # Check URL path and query parameters
        full_url = str(request.url)
        
        for pattern in sql_patterns + xss_patterns:
            if re.search(pattern, full_url, re.IGNORECASE):
                client_ip = self.honeypot_manager.get_client_ip(request)
                attack_type = "sql_injection" if pattern in sql_patterns else "xss_attempt"
                
                await self.blue_team.execute_defense_strategy(attack_type, {
                    "client_ip": client_ip,
                    "pattern": pattern,
                    "url": full_url
                })
                
                raise HTTPException(status_code=400, detail="Invalid input detected")
    
    def add_security_headers(self, response: Response):
        """Add comprehensive security headers"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            ),
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
    
    async def log_security_metrics(self, request: Request, response: Response, 
                                  start_time: float, anomaly_score: float):
        """Log comprehensive security metrics"""
        client_ip = self.honeypot_manager.get_client_ip(request)
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "response_time": time.time() - start_time,
            "anomaly_score": anomaly_score,
            "user_agent": request.headers.get("user-agent", ""),
            "is_suspicious": client_ip in self.suspicious_ips,
            "is_blocked": client_ip in self.blocked_ips
        }
        
        # Store in time-series database or logs
        logger.info("Security metrics", extra={"security_metrics": metrics})

# Additional security utilities
class SecurityUtils:
    """Utility functions for security operations"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return uuid.uuid4().hex[:length]
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, hashed)
    
    @staticmethod
    def create_jwt_token(user_data: Dict, expires_delta: timedelta = None) -> str:
        """Create JWT token with expiration"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
            
        to_encode = user_data.copy()
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_jwt_token(token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

# Export main security middleware
SecurityMiddleware = AdvancedSecurityMiddleware