"""
Advanced Honeypot and Deception System
Sophisticated Deception Technology for Threat Intelligence

This module implements advanced honeypots and deception techniques including:
- Dynamic honeypot deployment
- Intelligent response generation
- Attacker behavior profiling
- Threat intelligence collection
- Adaptive deception strategies
- Real-time attack attribution
"""

import asyncio
import json
import logging
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import re
import base64
import os

from fastapi import Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
import aiofiles
from jinja2 import Template

from voluntier.config import get_settings
from voluntier.database import get_db_session
from voluntier.models import SecurityEvent, ThreatIntelligence
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

@dataclass
class HoneypotEndpoint:
    """Honeypot endpoint configuration"""
    path: str
    methods: List[str]
    response_type: str
    response_data: Dict[str, Any]
    threat_level: str
    intelligence_value: str
    creation_time: datetime = field(default_factory=datetime.utcnow)
    hit_count: int = 0
    unique_attackers: Set[str] = field(default_factory=set)
    attack_patterns: List[Dict] = field(default_factory=list)

@dataclass
class AttackerProfile:
    """Attacker behavior profile"""
    attacker_id: str
    ip_address: str
    first_seen: datetime
    last_seen: datetime
    total_requests: int = 0
    honeypot_hits: int = 0
    attack_patterns: List[str] = field(default_factory=list)
    tools_detected: Set[str] = field(default_factory=set)
    geolocation: Optional[Dict[str, str]] = None
    user_agents: Set[str] = field(default_factory=set)
    threat_score: float = 0.0
    attack_sophistication: str = "low"  # low, medium, high, advanced
    attribution: Optional[str] = None

@dataclass
class DeceptionStrategy:
    """Deception strategy configuration"""
    strategy_id: str
    name: str
    description: str
    trigger_conditions: Dict[str, Any]
    response_template: str
    intelligence_goals: List[str]
    success_metrics: Dict[str, float]

class HoneypotResponseGenerator:
    """Generates realistic honeypot responses"""
    
    def __init__(self):
        self.response_templates = {
            "admin_login": {
                "html": """
                <!DOCTYPE html>
                <html>
                <head><title>Admin Login</title></head>
                <body>
                    <h2>Administrator Login</h2>
                    <form method="post" action="/admin/authenticate">
                        <input type="text" name="username" placeholder="Username" />
                        <input type="password" name="password" placeholder="Password" />
                        <button type="submit">Login</button>
                    </form>
                    <p><small>Version 2.1.4 - Build 20240315</small></p>
                </body>
                </html>
                """,
                "status_code": 200
            },
            "database_backup": {
                "content": """
-- MySQL dump 10.13  Distrib 8.0.32
-- Host: localhost    Database: volunteer_app
-- Server version	8.0.32-0ubuntu0.20.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;

CREATE TABLE `users` (
  `id` varchar(36) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `users` VALUES 
('1','admin','admin@example.com','$2b$12$fake_hash_for_honeypot_only'),
('2','testuser','test@example.com','$2b$12$another_fake_hash_for_testing');
                """,
                "content_type": "application/sql",
                "status_code": 200
            },
            "config_file": {
                "content": """
# Application Configuration
DEBUG=true
SECRET_KEY=fake_secret_key_for_honeypot
DATABASE_URL=mysql://admin:password123@localhost/volunteer_app
API_KEY=sk-fake-api-key-for-honeypot-detection
JWT_SECRET=fake_jwt_secret_key
REDIS_URL=redis://localhost:6379
SMTP_PASSWORD=fake_smtp_password

# Third-party integrations
STRIPE_SECRET_KEY=sk_test_fake_stripe_key
AWS_ACCESS_KEY_ID=AKIAFAKEACCESSKEY
AWS_SECRET_ACCESS_KEY=fake_aws_secret_access_key
                """,
                "content_type": "text/plain",
                "status_code": 200
            },
            "api_error": {
                "json": {
                    "error": "Unauthorized access",
                    "message": "Valid API key required",
                    "endpoints": [
                        "/api/v1/users",
                        "/api/v1/admin/stats",
                        "/api/v1/export/data"
                    ],
                    "debug_info": {
                        "server": "nginx/1.18.0",
                        "php_version": "8.1.2",
                        "timestamp": "{{ timestamp }}"
                    }
                },
                "status_code": 401
            },
            "directory_listing": {
                "html": """
                <html>
                <head><title>Index of /</title></head>
                <body>
                <h1>Index of /</h1>
                <ul>
                    <li><a href="../">../</a></li>
                    <li><a href="admin/">admin/</a></li>
                    <li><a href="config/">config/</a></li>
                    <li><a href="backup/">backup/</a></li>
                    <li><a href="logs/">logs/</a></li>
                    <li><a href=".env">.env</a></li>
                    <li><a href="dump.sql">dump.sql</a></li>
                </ul>
                </body>
                </html>
                """,
                "status_code": 200
            },
            "vulnerable_endpoint": {
                "json": {
                    "status": "success",
                    "data": {
                        "users": [
                            {"id": 1, "username": "admin", "role": "administrator"},
                            {"id": 2, "username": "operator", "role": "operator"}
                        ]
                    },
                    "query": "{{ query }}",
                    "execution_time": "0.045s"
                },
                "status_code": 200
            }
        }
        
    def generate_response(self, endpoint_type: str, context: Dict[str, Any]) -> Response:
        """Generate realistic response for honeypot endpoint"""
        template_data = self.response_templates.get(endpoint_type, {})
        
        if "html" in template_data:
            content = Template(template_data["html"]).render(**context)
            return HTMLResponse(
                content=content,
                status_code=template_data.get("status_code", 200)
            )
        elif "json" in template_data:
            content = json.loads(Template(json.dumps(template_data["json"])).render(**context))
            return JSONResponse(
                content=content,
                status_code=template_data.get("status_code", 200)
            )
        elif "content" in template_data:
            content = Template(template_data["content"]).render(**context)
            return PlainTextResponse(
                content=content,
                status_code=template_data.get("status_code", 200),
                media_type=template_data.get("content_type", "text/plain")
            )
        else:
            # Default response
            return JSONResponse(
                content={"error": "Not found"},
                status_code=404
            )

class AttackerBehaviorAnalyzer:
    """Analyzes attacker behavior for profiling and attribution"""
    
    def __init__(self):
        self.attacker_profiles: Dict[str, AttackerProfile] = {}
        self.attack_patterns = {
            "sql_injection": [
                r"union\s+select", r"or\s+1=1", r"and\s+1=1",
                r"drop\s+table", r"insert\s+into", r"update\s+.*\s+set"
            ],
            "xss": [
                r"<script", r"javascript:", r"on\w+\s*=",
                r"alert\s*\(", r"document\.cookie"
            ],
            "directory_traversal": [
                r"\.\./", r"\.\.\\", r"\.\.%2f", r"\.\.%5c"
            ],
            "command_injection": [
                r"[;&|]\s*(cat|ls|pwd|id|whoami)", r"nc\s+-", r"wget\s+", r"curl\s+"
            ],
            "reconnaissance": [
                r"robots\.txt", r"sitemap\.xml", r"\.htaccess",
                r"phpinfo", r"server-status", r"server-info"
            ]
        }
        self.tool_signatures = {
            "sqlmap": ["sqlmap", "testparameter"],
            "nikto": ["nikto"],
            "nmap": ["nmap scripting engine"],
            "burp": ["burp suite"],
            "dirb": ["dirb"],
            "gobuster": ["gobuster"],
            "nessus": ["nessus"],
            "acunetix": ["acunetix"],
            "shodan": ["shodan"]
        }
        
    def analyze_request(self, ip_address: str, request_data: Dict) -> Dict[str, Any]:
        """Analyze individual request for attack patterns"""
        attacker_id = self.get_or_create_attacker_id(ip_address)
        profile = self.get_attacker_profile(attacker_id, ip_address)
        
        analysis = {
            "attacker_id": attacker_id,
            "attack_patterns": [],
            "tools_detected": [],
            "sophistication_indicators": [],
            "threat_indicators": []
        }
        
        # Analyze request content
        request_text = self.extract_request_text(request_data)
        
        # Check for attack patterns
        for pattern_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, request_text, re.IGNORECASE):
                    analysis["attack_patterns"].append(pattern_type)
                    profile.attack_patterns.append(pattern_type)
                    break
                    
        # Check for tool signatures
        user_agent = request_data.get("user_agent", "").lower()
        for tool, signatures in self.tool_signatures.items():
            for signature in signatures:
                if signature in user_agent or signature in request_text.lower():
                    analysis["tools_detected"].append(tool)
                    profile.tools_detected.add(tool)
                    break
                    
        # Analyze sophistication
        sophistication_score = self.calculate_sophistication(analysis, request_data)
        analysis["sophistication_score"] = sophistication_score
        
        # Update attacker profile
        self.update_attacker_profile(profile, request_data, analysis)
        
        return analysis
        
    def get_or_create_attacker_id(self, ip_address: str) -> str:
        """Get or create unique attacker ID"""
        # Check if IP already has an attacker profile
        for attacker_id, profile in self.attacker_profiles.items():
            if profile.ip_address == ip_address:
                return attacker_id
                
        # Create new attacker ID
        return f"ATK_{uuid.uuid4().hex[:8].upper()}"
        
    def get_attacker_profile(self, attacker_id: str, ip_address: str) -> AttackerProfile:
        """Get or create attacker profile"""
        if attacker_id not in self.attacker_profiles:
            self.attacker_profiles[attacker_id] = AttackerProfile(
                attacker_id=attacker_id,
                ip_address=ip_address,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
        return self.attacker_profiles[attacker_id]
        
    def extract_request_text(self, request_data: Dict) -> str:
        """Extract all text content from request for analysis"""
        text_parts = []
        
        text_parts.append(request_data.get("request_path", ""))
        text_parts.append(request_data.get("query_string", ""))
        text_parts.append(request_data.get("user_agent", ""))
        text_parts.append(str(request_data.get("payload", "")))
        
        headers = request_data.get("headers", {})
        if isinstance(headers, dict):
            text_parts.extend(headers.values())
            
        return " ".join(text_parts)
        
    def calculate_sophistication(self, analysis: Dict, request_data: Dict) -> float:
        """Calculate attack sophistication score"""
        score = 0.0
        
        # Multiple attack patterns indicate higher sophistication
        unique_patterns = set(analysis["attack_patterns"])
        score += len(unique_patterns) * 0.2
        
        # Tool usage indicates automation/expertise
        if analysis["tools_detected"]:
            score += 0.3
            
        # Custom headers suggest manual testing
        headers = request_data.get("headers", {})
        custom_headers = [h for h in headers.keys() if h.lower().startswith("x-")]
        score += len(custom_headers) * 0.1
        
        # Evasion techniques
        request_text = self.extract_request_text(request_data)
        if self.detect_evasion_techniques(request_text):
            score += 0.4
            
        return min(score, 1.0)
        
    def detect_evasion_techniques(self, text: str) -> bool:
        """Detect evasion techniques in request"""
        evasion_patterns = [
            r"%[0-9a-f]{2}",  # URL encoding
            r"\\x[0-9a-f]{2}",  # Hex encoding
            r"&#\d+;",  # HTML entity encoding
            r"char\(\d+\)",  # SQL char() function
            r"0x[0-9a-f]+",  # Hex literals
        ]
        
        for pattern in evasion_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
        
    def update_attacker_profile(self, profile: AttackerProfile, 
                               request_data: Dict, analysis: Dict):
        """Update attacker profile with new information"""
        profile.last_seen = datetime.utcnow()
        profile.total_requests += 1
        
        # Update user agents
        user_agent = request_data.get("user_agent", "")
        if user_agent:
            profile.user_agents.add(user_agent)
            
        # Update threat score based on behavior
        pattern_score = len(set(analysis["attack_patterns"])) * 0.1
        tool_score = len(analysis["tools_detected"]) * 0.2
        sophistication_score = analysis.get("sophistication_score", 0) * 0.3
        
        profile.threat_score = min(
            profile.threat_score + pattern_score + tool_score + sophistication_score,
            1.0
        )
        
        # Determine attack sophistication level
        if profile.threat_score > 0.8:
            profile.attack_sophistication = "advanced"
        elif profile.threat_score > 0.6:
            profile.attack_sophistication = "high"
        elif profile.threat_score > 0.4:
            profile.attack_sophistication = "medium"
        else:
            profile.attack_sophistication = "low"

class IntelligentHoneypotManager:
    """Advanced honeypot management with adaptive strategies"""
    
    def __init__(self):
        self.honeypots: Dict[str, HoneypotEndpoint] = {}
        self.response_generator = HoneypotResponseGenerator()
        self.behavior_analyzer = AttackerBehaviorAnalyzer()
        self.deception_strategies: Dict[str, DeceptionStrategy] = {}
        
        # Honeypot categories
        self.honeypot_categories = {
            "administrative": {
                "paths": ["/admin", "/administrator", "/admin.php", "/wp-admin"],
                "response_type": "admin_login",
                "threat_level": "HIGH",
                "intelligence_value": "CRITICAL"
            },
            "configuration": {
                "paths": ["/.env", "/config.php", "/configuration.txt", "/settings.ini"],
                "response_type": "config_file",
                "threat_level": "CRITICAL",
                "intelligence_value": "HIGH"
            },
            "backup": {
                "paths": ["/backup.sql", "/dump.sql", "/database.sql", "/backup.zip"],
                "response_type": "database_backup",
                "threat_level": "HIGH",
                "intelligence_value": "HIGH"
            },
            "development": {
                "paths": ["/test", "/dev", "/debug", "/phpinfo.php"],
                "response_type": "vulnerable_endpoint",
                "threat_level": "MEDIUM",
                "intelligence_value": "MEDIUM"
            },
            "reconnaissance": {
                "paths": ["/robots.txt", "/sitemap.xml", "/.htaccess", "/server-status"],
                "response_type": "directory_listing",
                "threat_level": "LOW",
                "intelligence_value": "LOW"
            }
        }
        
    async def initialize(self):
        """Initialize honeypot system"""
        await self.deploy_initial_honeypots()
        await self.load_deception_strategies()
        logger.info("Intelligent honeypot manager initialized")
        
    async def deploy_initial_honeypots(self):
        """Deploy initial set of honeypots"""
        for category, config in self.honeypot_categories.items():
            for path in config["paths"]:
                await self.deploy_honeypot(
                    path=path,
                    response_type=config["response_type"],
                    threat_level=config["threat_level"],
                    intelligence_value=config["intelligence_value"]
                )
                
    async def deploy_honeypot(self, path: str, response_type: str, 
                             threat_level: str, intelligence_value: str,
                             methods: List[str] = None) -> str:
        """Deploy a new honeypot endpoint"""
        if methods is None:
            methods = ["GET", "POST", "PUT", "DELETE"]
            
        honeypot_id = f"HP_{uuid.uuid4().hex[:8].upper()}"
        
        honeypot = HoneypotEndpoint(
            path=path,
            methods=methods,
            response_type=response_type,
            response_data={},
            threat_level=threat_level,
            intelligence_value=intelligence_value
        )
        
        self.honeypots[path] = honeypot
        
        logger.info(f"Deployed honeypot: {path} (ID: {honeypot_id})")
        return honeypot_id
        
    async def check_honeypot_hit(self, request: Request) -> Tuple[bool, Optional[Dict]]:
        """Check if request hits a honeypot and handle accordingly"""
        path = request.url.path
        
        if path in self.honeypots:
            honeypot = self.honeypots[path]
            
            # Extract request information
            client_ip = self.get_client_ip(request)
            request_data = await self.extract_request_data(request)
            
            # Analyze attacker behavior
            behavior_analysis = self.behavior_analyzer.analyze_request(client_ip, request_data)
            
            # Update honeypot statistics
            honeypot.hit_count += 1
            honeypot.unique_attackers.add(client_ip)
            honeypot.attack_patterns.append({
                "timestamp": datetime.utcnow(),
                "ip_address": client_ip,
                "request_data": request_data,
                "behavior_analysis": behavior_analysis
            })
            
            # Log security event
            await self.log_honeypot_hit(honeypot, client_ip, request_data, behavior_analysis)
            
            # Generate intelligent response
            response = await self.generate_intelligent_response(
                honeypot, request_data, behavior_analysis
            )
            
            return True, {
                "honeypot": honeypot,
                "response": response,
                "behavior_analysis": behavior_analysis
            }
            
        return False, None
        
    def get_client_ip(self, request: Request) -> str:
        """Extract real client IP considering proxies"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"
        
    async def extract_request_data(self, request: Request) -> Dict[str, Any]:
        """Extract comprehensive request data for analysis"""
        data = {
            "request_path": request.url.path,
            "query_string": str(request.url.query),
            "method": request.method,
            "user_agent": request.headers.get("user-agent", ""),
            "headers": dict(request.headers),
            "timestamp": datetime.utcnow()
        }
        
        # Try to read request body if present
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    data["payload"] = body.decode('utf-8', errors='ignore')
        except Exception:
            data["payload"] = ""
            
        return data
        
    async def generate_intelligent_response(self, honeypot: HoneypotEndpoint,
                                          request_data: Dict, behavior_analysis: Dict) -> Response:
        """Generate intelligent response based on attacker profile"""
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": request_data.get("query_string", ""),
            "user_agent": request_data.get("user_agent", ""),
            "ip_address": behavior_analysis.get("attacker_id", "unknown")
        }
        
        # Adapt response based on attacker sophistication
        sophistication = behavior_analysis.get("sophistication_score", 0)
        
        if sophistication > 0.7:
            # High sophistication - provide more convincing responses
            response_type = honeypot.response_type
        elif sophistication > 0.4:
            # Medium sophistication - standard responses
            response_type = honeypot.response_type
        else:
            # Low sophistication - basic responses
            response_type = honeypot.response_type
            
        # Generate response using template
        response = self.response_generator.generate_response(response_type, context)
        
        # Add realistic headers
        response.headers["server"] = "nginx/1.18.0 (Ubuntu)"
        response.headers["x-powered-by"] = "PHP/8.1.2"
        
        return response
        
    async def log_honeypot_hit(self, honeypot: HoneypotEndpoint, client_ip: str,
                              request_data: Dict, behavior_analysis: Dict):
        """Log honeypot hit as security event"""
        async with get_db_session() as session:
            event = SecurityEvent(
                event_type="HONEYPOT_HIT",
                category="deception",
                severity=honeypot.threat_level,
                description=f"Honeypot hit on {honeypot.path} from {client_ip}",
                source_ip=client_ip,
                user_agent=request_data.get("user_agent", ""),
                request_path=honeypot.path,
                request_method=request_data.get("method", ""),
                attack_vector=", ".join(behavior_analysis.get("attack_patterns", [])),
                payload=request_data.get("payload", ""),
                threat_score=behavior_analysis.get("sophistication_score", 0),
                confidence_level=0.9,  # High confidence for honeypot hits
                metadata={
                    "honeypot_type": honeypot.response_type,
                    "attacker_id": behavior_analysis.get("attacker_id"),
                    "tools_detected": behavior_analysis.get("tools_detected", []),
                    "intelligence_value": honeypot.intelligence_value
                },
                timestamp=datetime.utcnow()
            )
            session.add(event)
            await session.commit()
            
        logger.warning(f"Honeypot hit: {honeypot.path} from {client_ip}")
        
    async def load_deception_strategies(self):
        """Load deception strategies for adaptive responses"""
        self.deception_strategies = {
            "credential_harvesting": DeceptionStrategy(
                strategy_id="CRED_001",
                name="Credential Harvesting Detection",
                description="Deploy fake login forms to detect credential harvesting",
                trigger_conditions={"path_patterns": ["/admin", "/login"]},
                response_template="admin_login",
                intelligence_goals=["collect_credentials", "identify_tools"],
                success_metrics={"engagement_rate": 0.7, "data_collection": 0.8}
            ),
            "data_exfiltration": DeceptionStrategy(
                strategy_id="DATA_001",
                name="Data Exfiltration Detection",
                description="Deploy fake sensitive files to detect data theft attempts",
                trigger_conditions={"path_patterns": ["/.env", "/backup", "/dump"]},
                response_template="config_file",
                intelligence_goals=["track_exfiltration", "identify_targets"],
                success_metrics={"download_rate": 0.6, "persistence": 0.5}
            ),
            "vulnerability_scanning": DeceptionStrategy(
                strategy_id="VULN_001",
                name="Vulnerability Scanner Detection",
                description="Deploy fake vulnerabilities to detect scanning activity",
                trigger_conditions={"user_agent_patterns": ["scanner", "bot"]},
                response_template="vulnerable_endpoint",
                intelligence_goals=["identify_scanners", "map_techniques"],
                success_metrics={"detection_rate": 0.9, "attribution": 0.6}
            )
        }
        
    async def adapt_honeypots(self):
        """Adapt honeypot deployment based on threat intelligence"""
        # Analyze recent attacks to identify new threats
        recent_attacks = await self.analyze_recent_attacks()
        
        # Deploy targeted honeypots based on attack patterns
        for attack_pattern in recent_attacks:
            if attack_pattern["frequency"] > 10:  # Deploy if seen frequently
                await self.deploy_targeted_honeypot(attack_pattern)
                
    async def analyze_recent_attacks(self) -> List[Dict]:
        """Analyze recent attacks to identify patterns"""
        async with get_db_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(hours=24)
            result = await session.execute(
                f"""
                SELECT request_path, COUNT(*) as frequency,
                       ARRAY_AGG(DISTINCT source_ip) as attackers
                FROM security_events 
                WHERE timestamp > '{cutoff_date}' 
                AND event_type != 'HONEYPOT_HIT'
                GROUP BY request_path
                ORDER BY frequency DESC
                LIMIT 20
                """
            )
            
            patterns = []
            for row in result:
                patterns.append({
                    "path": row[0],
                    "frequency": row[1],
                    "unique_attackers": len(row[2] or [])
                })
                
            return patterns
            
    async def deploy_targeted_honeypot(self, attack_pattern: Dict):
        """Deploy honeypot targeting specific attack pattern"""
        path = attack_pattern["path"]
        
        # Don't deploy if already exists
        if path in self.honeypots:
            return
            
        # Determine appropriate response type based on path
        response_type = "vulnerable_endpoint"
        if any(admin_path in path for admin_path in ["/admin", "/manage"]):
            response_type = "admin_login"
        elif any(config_path in path for config_path in [".env", "config", "settings"]):
            response_type = "config_file"
        elif any(backup_path in path for backup_path in ["backup", "dump", ".sql"]):
            response_type = "database_backup"
            
        await self.deploy_honeypot(
            path=path,
            response_type=response_type,
            threat_level="HIGH",
            intelligence_value="HIGH"
        )
        
        logger.info(f"Deployed targeted honeypot for attack pattern: {path}")
        
    async def get_honeypot_statistics(self) -> Dict[str, Any]:
        """Get comprehensive honeypot statistics"""
        total_honeypots = len(self.honeypots)
        total_hits = sum(hp.hit_count for hp in self.honeypots.values())
        unique_attackers = set()
        
        for hp in self.honeypots.values():
            unique_attackers.update(hp.unique_attackers)
            
        most_hit_honeypot = max(
            self.honeypots.values(),
            key=lambda hp: hp.hit_count,
            default=None
        )
        
        return {
            "total_honeypots": total_honeypots,
            "total_hits": total_hits,
            "unique_attackers": len(unique_attackers),
            "most_targeted_path": most_hit_honeypot.path if most_hit_honeypot else None,
            "attacker_profiles": len(self.behavior_analyzer.attacker_profiles),
            "deception_strategies": len(self.deception_strategies),
            "intelligence_collected": {
                "attack_patterns": sum(
                    len(profile.attack_patterns) 
                    for profile in self.behavior_analyzer.attacker_profiles.values()
                ),
                "tools_detected": sum(
                    len(profile.tools_detected)
                    for profile in self.behavior_analyzer.attacker_profiles.values()
                )
            }
        }

# Global honeypot manager instance
honeypot_manager = IntelligentHoneypotManager()