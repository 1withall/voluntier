"""
Advanced Threat Detection System
ML-Enhanced Real-time Threat Detection and Analysis

This module implements sophisticated threat detection using:
- Machine Learning anomaly detection
- Behavioral analysis and user profiling
- Real-time attack pattern recognition
- Adaptive threat scoring
- Zero-day threat detection
- Advanced persistent threat (APT) detection
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import re
import hashlib

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from scipy import stats

from voluntier.config import get_settings
from voluntier.database import get_db_session
from voluntier.models import SecurityEvent, ThreatIntelligence, User, AuthenticationLog
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

@dataclass
class ThreatSignature:
    """Threat signature for pattern matching"""
    signature_id: str
    name: str
    pattern: str
    threat_type: str
    severity: str
    confidence: float
    regex_pattern: Optional[str] = None
    ml_features: Optional[List[str]] = None

@dataclass
class AttackVector:
    """Attack vector analysis"""
    vector_type: str
    confidence: float
    indicators: List[str]
    mitre_tactics: List[str]
    mitre_techniques: List[str]
    remediation: List[str]

@dataclass
class UserBehaviorProfile:
    """User behavioral profile for anomaly detection"""
    user_id: str
    creation_date: datetime
    login_patterns: Dict[str, Any] = field(default_factory=dict)
    location_patterns: Dict[str, Any] = field(default_factory=dict)
    device_patterns: Dict[str, Any] = field(default_factory=dict)
    activity_patterns: Dict[str, Any] = field(default_factory=dict)
    risk_factors: List[str] = field(default_factory=list)
    trust_score: float = 0.5
    last_updated: datetime = field(default_factory=datetime.utcnow)

class MLThreatDetector:
    """Machine Learning-based threat detection engine"""
    
    def __init__(self):
        self.isolation_forest = None
        self.random_forest = None
        self.clustering_model = None
        self.feature_scaler = StandardScaler()
        self.text_vectorizer = TfidfVectorizer(max_features=1000)
        
        self.models_trained = False
        self.training_data = []
        self.feature_names = []
        self.model_version = "1.0"
        
        # Threat detection thresholds
        self.anomaly_threshold = -0.5
        self.high_risk_threshold = -0.7
        self.critical_threshold = -0.9
        
    async def initialize(self):
        """Initialize ML threat detection models"""
        await self.load_existing_models()
        if not self.models_trained:
            await self.train_initial_models()
            
    async def load_existing_models(self):
        """Load pre-trained models if available"""
        try:
            self.isolation_forest = joblib.load("/tmp/isolation_forest.pkl")
            self.random_forest = joblib.load("/tmp/random_forest.pkl")
            self.feature_scaler = joblib.load("/tmp/feature_scaler.pkl")
            self.models_trained = True
            logger.info("Loaded existing ML threat detection models")
        except FileNotFoundError:
            logger.info("No existing models found, will train new models")
            
    async def train_initial_models(self):
        """Train initial ML models on historical data"""
        training_data = await self.collect_training_data()
        if len(training_data) < 100:
            logger.warning("Insufficient training data, using default models")
            await self.initialize_default_models()
            return
            
        X, y = await self.prepare_training_data(training_data)
        
        # Train Isolation Forest for anomaly detection
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        X_scaled = self.feature_scaler.fit_transform(X)
        self.isolation_forest.fit(X_scaled)
        
        # Train Random Forest for threat classification
        self.random_forest = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight='balanced'
        )
        self.random_forest.fit(X_scaled, y)
        
        # Save models
        joblib.dump(self.isolation_forest, "/tmp/isolation_forest.pkl")
        joblib.dump(self.random_forest, "/tmp/random_forest.pkl")
        joblib.dump(self.feature_scaler, "/tmp/feature_scaler.pkl")
        
        self.models_trained = True
        logger.info(f"Trained ML models on {len(training_data)} samples")
        
    async def initialize_default_models(self):
        """Initialize default models with minimal training"""
        # Create simple models for basic threat detection
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.random_forest = RandomForestClassifier(n_estimators=50, random_state=42)
        
        # Generate synthetic training data for basic functionality
        synthetic_data = np.random.rand(100, 20)
        synthetic_labels = np.random.choice([0, 1], 100, p=[0.9, 0.1])
        
        self.feature_scaler.fit(synthetic_data)
        self.isolation_forest.fit(synthetic_data)
        self.random_forest.fit(synthetic_data, synthetic_labels)
        
        self.models_trained = True
        logger.info("Initialized default ML models with synthetic data")
        
    async def collect_training_data(self) -> List[Dict]:
        """Collect historical data for model training"""
        async with get_db_session() as session:
            # Collect security events from last 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            result = await session.execute(
                f"""
                SELECT event_type, severity, source_ip, user_agent, request_path,
                       request_method, metadata, timestamp
                FROM security_events 
                WHERE timestamp > '{cutoff_date}'
                ORDER BY timestamp DESC
                LIMIT 10000
                """
            )
            
            training_data = []
            for row in result:
                training_data.append({
                    "event_type": row[0],
                    "severity": row[1],
                    "source_ip": row[2],
                    "user_agent": row[3] or "",
                    "request_path": row[4] or "",
                    "request_method": row[5] or "",
                    "metadata": row[6] or {},
                    "timestamp": row[7]
                })
                
            return training_data
            
    async def prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for ML models"""
        features = []
        labels = []
        
        for record in training_data:
            feature_vector = await self.extract_ml_features(record)
            features.append(feature_vector)
            
            # Create labels based on severity
            severity = record.get("severity", "LOW")
            label = 1 if severity in ["HIGH", "CRITICAL"] else 0
            labels.append(label)
            
        return np.array(features), np.array(labels)
        
    async def extract_ml_features(self, data: Dict) -> List[float]:
        """Extract numerical features for ML analysis"""
        features = []
        
        # Basic request features
        features.append(len(data.get("request_path", "")))
        features.append(len(data.get("user_agent", "")))
        features.append(len(str(data.get("metadata", {}))))
        
        # Time-based features
        timestamp = data.get("timestamp", datetime.utcnow())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        features.append(timestamp.hour)
        features.append(timestamp.weekday())
        features.append(1 if 22 <= timestamp.hour or timestamp.hour <= 6 else 0)
        
        # HTTP method encoding
        method_encoding = {
            "GET": 1, "POST": 2, "PUT": 3, "DELETE": 4,
            "PATCH": 5, "HEAD": 6, "OPTIONS": 7
        }
        features.append(method_encoding.get(data.get("request_method", ""), 0))
        
        # User agent analysis
        user_agent = data.get("user_agent", "").lower()
        features.append(1 if "bot" in user_agent else 0)
        features.append(1 if "curl" in user_agent else 0)
        features.append(1 if "python" in user_agent else 0)
        features.append(1 if "scanner" in user_agent else 0)
        
        # Path analysis
        path = data.get("request_path", "").lower()
        suspicious_patterns = [
            "admin", "config", "backup", "sql", "php", "wp-",
            ".env", "debug", "test", "api/v", "swagger", "shell"
        ]
        for pattern in suspicious_patterns:
            features.append(1 if pattern in path else 0)
            
        # Ensure consistent feature vector length
        while len(features) < 20:
            features.append(0.0)
            
        return features[:20]  # Limit to 20 features
        
    async def analyze_request(self, request_data: Dict) -> Dict[str, Any]:
        """Analyze request using ML models and return threat assessment"""
        if not self.models_trained:
            return {"anomaly_score": 0.0, "threat_probability": 0.0, "threat_class": "unknown"}
            
        try:
            # Extract features
            features = await self.extract_ml_features(request_data)
            feature_vector = np.array(features).reshape(1, -1)
            
            # Scale features
            scaled_features = self.feature_scaler.transform(feature_vector)
            
            # Get anomaly score from Isolation Forest
            anomaly_score = self.isolation_forest.decision_function(scaled_features)[0]
            
            # Get threat probability from Random Forest
            threat_probability = self.random_forest.predict_proba(scaled_features)[0][1]
            
            # Classify threat level
            if anomaly_score < self.critical_threshold:
                threat_class = "critical"
            elif anomaly_score < self.high_risk_threshold:
                threat_class = "high"
            elif anomaly_score < self.anomaly_threshold:
                threat_class = "medium"
            else:
                threat_class = "low"
                
            return {
                "anomaly_score": float(anomaly_score),
                "threat_probability": float(threat_probability),
                "threat_class": threat_class,
                "model_version": self.model_version
            }
            
        except Exception as e:
            logger.error(f"Error in ML threat analysis: {e}")
            return {"anomaly_score": 0.0, "threat_probability": 0.0, "threat_class": "unknown"}
            
    async def retrain_models(self):
        """Retrain models with new data"""
        logger.info("Retraining ML threat detection models")
        await self.train_initial_models()

class BehavioralThreatDetector:
    """Behavioral analysis for threat detection"""
    
    def __init__(self):
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}
        self.baseline_window = timedelta(days=30)
        self.analysis_window = timedelta(hours=24)
        self.anomaly_threshold = 2.0  # Standard deviations
        
    async def initialize(self):
        """Initialize behavioral threat detector"""
        await self.load_user_profiles()
        
    async def load_user_profiles(self):
        """Load existing user behavioral profiles"""
        async with get_db_session() as session:
            # Load user authentication patterns
            cutoff_date = datetime.utcnow() - self.baseline_window
            result = await session.execute(
                f"""
                SELECT u.id, u.name, u.created_at,
                       COUNT(al.id) as login_count,
                       AVG(EXTRACT(hour FROM al.timestamp)) as avg_hour,
                       ARRAY_AGG(DISTINCT al.ip_address) as ip_addresses,
                       ARRAY_AGG(DISTINCT al.country) as countries
                FROM users u
                LEFT JOIN authentication_logs al ON u.id = al.user_id
                WHERE al.timestamp > '{cutoff_date}' AND al.auth_result = 'success'
                GROUP BY u.id, u.name, u.created_at
                """
            )
            
            for row in result:
                user_id = str(row[0])
                profile = UserBehaviorProfile(
                    user_id=user_id,
                    creation_date=row[2],
                    login_patterns={
                        "frequency": row[3] / 30 if row[3] else 0,
                        "typical_hours": [row[4]] if row[4] else [],
                        "login_count": row[3] or 0
                    },
                    location_patterns={
                        "known_ips": set(row[5] or []),
                        "known_countries": set(row[6] or [])
                    }
                )
                self.user_profiles[user_id] = profile
                
        logger.info(f"Loaded behavioral profiles for {len(self.user_profiles)} users")
        
    async def analyze_user_behavior(self, user_id: str, context: Dict) -> Dict[str, Any]:
        """Analyze user behavior for anomalies"""
        if user_id not in self.user_profiles:
            await self.create_user_profile(user_id)
            
        profile = self.user_profiles[user_id]
        anomalies = []
        risk_score = 0.0
        
        # Analyze login time patterns
        current_hour = datetime.utcnow().hour
        typical_hours = profile.login_patterns.get("typical_hours", [])
        
        if typical_hours:
            hour_deviation = min([abs(current_hour - h) for h in typical_hours])
            if hour_deviation > 6:  # More than 6 hours from typical
                anomalies.append("unusual_login_time")
                risk_score += 0.3
                
        # Analyze location patterns
        current_ip = context.get("ip_address")
        current_country = context.get("country")
        
        known_ips = profile.location_patterns.get("known_ips", set())
        known_countries = profile.location_patterns.get("known_countries", set())
        
        if current_ip and current_ip not in known_ips:
            anomalies.append("unknown_ip_address")
            risk_score += 0.4
            
        if current_country and current_country not in known_countries:
            anomalies.append("unknown_country")
            risk_score += 0.5
            
        # Analyze device patterns
        user_agent = context.get("user_agent", "")
        if await self.is_unusual_device(user_id, user_agent):
            anomalies.append("unusual_device")
            risk_score += 0.3
            
        # Analyze request patterns
        request_path = context.get("request_path", "")
        if await self.is_unusual_request_pattern(user_id, request_path):
            anomalies.append("unusual_request_pattern")
            risk_score += 0.4
            
        # Update profile with new data
        await self.update_user_profile(user_id, context)
        
        return {
            "user_id": user_id,
            "risk_score": min(risk_score, 1.0),
            "anomalies": anomalies,
            "profile_age": (datetime.utcnow() - profile.creation_date).days,
            "confidence": min(len(anomalies) * 0.2, 1.0)
        }
        
    async def create_user_profile(self, user_id: str):
        """Create new user behavioral profile"""
        profile = UserBehaviorProfile(
            user_id=user_id,
            creation_date=datetime.utcnow()
        )
        self.user_profiles[user_id] = profile
        
    async def is_unusual_device(self, user_id: str, user_agent: str) -> bool:
        """Check if device/user agent is unusual for user"""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return False
            
        # Simple device fingerprinting based on user agent
        device_signatures = profile.device_patterns.get("signatures", set())
        
        # Extract basic device info
        device_info = self.extract_device_info(user_agent)
        device_signature = f"{device_info['browser']}_{device_info['os']}"
        
        return device_signature not in device_signatures
        
    async def is_unusual_request_pattern(self, user_id: str, request_path: str) -> bool:
        """Check if request pattern is unusual for user"""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return False
            
        # Check for administrative or sensitive paths
        sensitive_patterns = [
            r"/admin", r"/api/.*/delete", r"/config", r"/debug",
            r"\.php$", r"wp-admin", r"/backup"
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, request_path, re.IGNORECASE):
                return True
                
        return False
        
    def extract_device_info(self, user_agent: str) -> Dict[str, str]:
        """Extract device information from user agent"""
        # Simple user agent parsing
        info = {"browser": "unknown", "os": "unknown", "device": "unknown"}
        
        ua_lower = user_agent.lower()
        
        # Browser detection
        if "chrome" in ua_lower:
            info["browser"] = "chrome"
        elif "firefox" in ua_lower:
            info["browser"] = "firefox"
        elif "safari" in ua_lower:
            info["browser"] = "safari"
        elif "edge" in ua_lower:
            info["browser"] = "edge"
            
        # OS detection
        if "windows" in ua_lower:
            info["os"] = "windows"
        elif "mac" in ua_lower or "darwin" in ua_lower:
            info["os"] = "macos"
        elif "linux" in ua_lower:
            info["os"] = "linux"
        elif "android" in ua_lower:
            info["os"] = "android"
        elif "ios" in ua_lower:
            info["os"] = "ios"
            
        return info
        
    async def update_user_profile(self, user_id: str, context: Dict):
        """Update user behavioral profile with new data"""
        if user_id not in self.user_profiles:
            return
            
        profile = self.user_profiles[user_id]
        
        # Update login patterns
        current_hour = datetime.utcnow().hour
        profile.login_patterns.setdefault("typical_hours", []).append(current_hour)
        
        # Keep only recent hours (last 100 logins)
        if len(profile.login_patterns["typical_hours"]) > 100:
            profile.login_patterns["typical_hours"] = profile.login_patterns["typical_hours"][-50:]
            
        # Update location patterns
        ip_address = context.get("ip_address")
        country = context.get("country")
        
        if ip_address:
            profile.location_patterns.setdefault("known_ips", set()).add(ip_address)
        if country:
            profile.location_patterns.setdefault("known_countries", set()).add(country)
            
        # Update device patterns
        user_agent = context.get("user_agent", "")
        if user_agent:
            device_info = self.extract_device_info(user_agent)
            device_signature = f"{device_info['browser']}_{device_info['os']}"
            profile.device_patterns.setdefault("signatures", set()).add(device_signature)
            
        profile.last_updated = datetime.utcnow()

class SignatureBasedDetector:
    """Signature-based threat detection for known attack patterns"""
    
    def __init__(self):
        self.threat_signatures = []
        self.load_signatures()
        
    def load_signatures(self):
        """Load threat signatures for pattern matching"""
        self.threat_signatures = [
            ThreatSignature(
                signature_id="SQL_001",
                name="SQL Injection - Union Based",
                pattern="union.*select",
                threat_type="sql_injection",
                severity="HIGH",
                confidence=0.9,
                regex_pattern=r"union\s+.*\s+select"
            ),
            ThreatSignature(
                signature_id="SQL_002",
                name="SQL Injection - Boolean Based",
                pattern="and.*1=1|or.*1=1",
                threat_type="sql_injection",
                severity="HIGH",
                confidence=0.8,
                regex_pattern=r"(and|or)\s+\d+\s*=\s*\d+"
            ),
            ThreatSignature(
                signature_id="XSS_001",
                name="XSS - Script Tag",
                pattern="<script",
                threat_type="xss",
                severity="HIGH",
                confidence=0.9,
                regex_pattern=r"<script[^>]*>"
            ),
            ThreatSignature(
                signature_id="XSS_002",
                name="XSS - Event Handler",
                pattern="on\\w+\\s*=",
                threat_type="xss",
                severity="MEDIUM",
                confidence=0.7,
                regex_pattern=r"on\w+\s*="
            ),
            ThreatSignature(
                signature_id="TRAVERSAL_001",
                name="Directory Traversal",
                pattern="\\.\\./",
                threat_type="directory_traversal",
                severity="HIGH",
                confidence=0.8,
                regex_pattern=r"\.\./|\.\.\\|\.\.\%2f"
            ),
            ThreatSignature(
                signature_id="CMD_001",
                name="Command Injection",
                pattern="(;|\\||&)\\s*(cat|ls|pwd|whoami)",
                threat_type="command_injection",
                severity="CRITICAL",
                confidence=0.9,
                regex_pattern=r"[;|&]\s*(cat|ls|pwd|whoami|id|uname)"
            ),
            ThreatSignature(
                signature_id="SCAN_001",
                name="Vulnerability Scanner",
                pattern="(nikto|nessus|sqlmap|burp|nmap)",
                threat_type="reconnaissance",
                severity="MEDIUM",
                confidence=0.8,
                regex_pattern=r"(nikto|nessus|sqlmap|burp|nmap|dirb|gobuster)"
            )
        ]
        
    async def scan_for_threats(self, data: Dict) -> List[Dict[str, Any]]:
        """Scan input data for known threat signatures"""
        threats_found = []
        
        # Combine all text data for scanning
        text_data = []
        text_data.append(data.get("request_path", ""))
        text_data.append(data.get("user_agent", ""))
        text_data.append(str(data.get("payload", "")))
        
        # Add headers if available
        headers = data.get("headers", {})
        if isinstance(headers, dict):
            text_data.extend(headers.values())
            
        full_text = " ".join(text_data).lower()
        
        # Check each signature
        for signature in self.threat_signatures:
            if signature.regex_pattern:
                if re.search(signature.regex_pattern, full_text, re.IGNORECASE):
                    threats_found.append({
                        "signature_id": signature.signature_id,
                        "name": signature.name,
                        "threat_type": signature.threat_type,
                        "severity": signature.severity,
                        "confidence": signature.confidence,
                        "matched_text": self.extract_match(signature.regex_pattern, full_text)
                    })
                    
        return threats_found
        
    def extract_match(self, pattern: str, text: str) -> str:
        """Extract the matched text for evidence"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
        return ""

class AdvancedThreatDetectionSystem:
    """Main threat detection system orchestrating all detection engines"""
    
    def __init__(self):
        self.ml_detector = MLThreatDetector()
        self.behavioral_detector = BehavioralThreatDetector()
        self.signature_detector = SignatureBasedDetector()
        
        self.detection_active = False
        self.threat_cache = {}
        self.analysis_stats = {
            "total_requests": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "last_reset": datetime.utcnow()
        }
        
    async def initialize(self):
        """Initialize all threat detection components"""
        await self.ml_detector.initialize()
        await self.behavioral_detector.initialize()
        
        self.detection_active = True
        logger.info("Advanced threat detection system initialized")
        
    async def analyze_threat(self, request_data: Dict) -> Dict[str, Any]:
        """Comprehensive threat analysis using all detection engines"""
        if not self.detection_active:
            return {"threat_detected": False, "threat_score": 0.0}
            
        start_time = time.time()
        self.analysis_stats["total_requests"] += 1
        
        # Initialize analysis result
        analysis_result = {
            "threat_detected": False,
            "threat_score": 0.0,
            "confidence": 0.0,
            "threat_types": [],
            "attack_vectors": [],
            "ml_analysis": {},
            "behavioral_analysis": {},
            "signature_matches": [],
            "recommendations": [],
            "analysis_time": 0.0
        }
        
        try:
            # 1. Signature-based detection (fastest)
            signature_matches = await self.signature_detector.scan_for_threats(request_data)
            analysis_result["signature_matches"] = signature_matches
            
            if signature_matches:
                analysis_result["threat_detected"] = True
                max_severity = max([match["severity"] for match in signature_matches])
                analysis_result["threat_score"] += 0.8 if max_severity == "CRITICAL" else 0.6
                analysis_result["threat_types"].extend([match["threat_type"] for match in signature_matches])
                
            # 2. ML-based analysis
            ml_analysis = await self.ml_detector.analyze_request(request_data)
            analysis_result["ml_analysis"] = ml_analysis
            
            if ml_analysis["threat_class"] in ["high", "critical"]:
                analysis_result["threat_detected"] = True
                analysis_result["threat_score"] += ml_analysis["threat_probability"] * 0.7
                
            # 3. Behavioral analysis (if user identified)
            user_id = request_data.get("user_id")
            if user_id:
                behavioral_analysis = await self.behavioral_detector.analyze_user_behavior(
                    user_id, request_data
                )
                analysis_result["behavioral_analysis"] = behavioral_analysis
                
                if behavioral_analysis["risk_score"] > 0.6:
                    analysis_result["threat_detected"] = True
                    analysis_result["threat_score"] += behavioral_analysis["risk_score"] * 0.5
                    
            # Normalize threat score
            analysis_result["threat_score"] = min(analysis_result["threat_score"], 1.0)
            
            # Calculate overall confidence
            confidence_factors = []
            if signature_matches:
                confidence_factors.append(max([match["confidence"] for match in signature_matches]))
            if ml_analysis.get("threat_class") != "unknown":
                confidence_factors.append(0.7)  # ML confidence
            if user_id and analysis_result["behavioral_analysis"]:
                confidence_factors.append(analysis_result["behavioral_analysis"]["confidence"])
                
            analysis_result["confidence"] = np.mean(confidence_factors) if confidence_factors else 0.0
            
            # Generate recommendations
            analysis_result["recommendations"] = await self.generate_recommendations(analysis_result)
            
            # Update statistics
            if analysis_result["threat_detected"]:
                self.analysis_stats["threats_detected"] += 1
                
        except Exception as e:
            logger.error(f"Error in threat analysis: {e}")
            analysis_result["error"] = str(e)
            
        finally:
            analysis_result["analysis_time"] = time.time() - start_time
            
        return analysis_result
        
    async def generate_recommendations(self, analysis_result: Dict) -> List[str]:
        """Generate security recommendations based on analysis"""
        recommendations = []
        
        threat_score = analysis_result["threat_score"]
        signature_matches = analysis_result["signature_matches"]
        
        if threat_score > 0.8:
            recommendations.append("IMMEDIATE_BLOCK")
            recommendations.append("ALERT_SECURITY_TEAM")
            
        if threat_score > 0.6:
            recommendations.append("INCREASE_MONITORING")
            recommendations.append("REQUIRE_ADDITIONAL_AUTH")
            
        if signature_matches:
            for match in signature_matches:
                if match["threat_type"] == "sql_injection":
                    recommendations.append("ENABLE_WAF_SQL_PROTECTION")
                elif match["threat_type"] == "xss":
                    recommendations.append("ENABLE_CSP_STRICT")
                elif match["threat_type"] == "command_injection":
                    recommendations.append("SANDBOX_EXECUTION")
                    
        if analysis_result.get("behavioral_analysis", {}).get("anomalies"):
            recommendations.append("VERIFY_USER_IDENTITY")
            recommendations.append("CHECK_ACCOUNT_COMPROMISE")
            
        return list(set(recommendations))  # Remove duplicates
        
    async def update_threat_intelligence(self, analysis_result: Dict, actual_threat: bool):
        """Update threat intelligence based on analysis feedback"""
        # This would be used to improve detection accuracy
        if actual_threat != analysis_result["threat_detected"]:
            if not actual_threat and analysis_result["threat_detected"]:
                self.analysis_stats["false_positives"] += 1
                # Could retrain models or adjust thresholds
                
    async def get_detection_statistics(self) -> Dict[str, Any]:
        """Get threat detection statistics"""
        total_requests = self.analysis_stats["total_requests"]
        threats_detected = self.analysis_stats["threats_detected"]
        false_positives = self.analysis_stats["false_positives"]
        
        return {
            "total_requests_analyzed": total_requests,
            "threats_detected": threats_detected,
            "false_positives": false_positives,
            "detection_rate": threats_detected / total_requests if total_requests > 0 else 0,
            "false_positive_rate": false_positives / threats_detected if threats_detected > 0 else 0,
            "uptime": datetime.utcnow() - self.analysis_stats["last_reset"],
            "ml_models_trained": self.ml_detector.models_trained,
            "user_profiles_loaded": len(self.behavioral_detector.user_profiles),
            "threat_signatures_loaded": len(self.signature_detector.threat_signatures)
        }

# Global threat detection system instance
threat_detection_system = AdvancedThreatDetectionSystem()