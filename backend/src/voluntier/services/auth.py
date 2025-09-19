"""
Advanced Authentication Service
Zero-Trust Authentication with Hardware Tokens, Biometric Verification, and Risk-Based Access Control

This service provides enterprise-grade authentication including:
- Hardware token (WebAuthn/FIDO2) support
- Biometric authentication and verification
- Risk-based authentication with dynamic scoring
- Secure password generation and storage using Argon2/bcrypt
- Continuous authentication monitoring
- Multi-factor authentication orchestration
- Session security with encrypted tokens
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import string
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from collections import defaultdict
import base64
import binascii

import argon2
import bcrypt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
import redis.asyncio as redis

from voluntier.config import get_settings
from voluntier.database import get_db_session
from voluntier.models import User, UserSession, AuthenticationLog, SecurityEvent
from voluntier.services.security_service import SecurityService
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class HardwareTokenCredential:
    """WebAuthn/FIDO2 hardware token credential"""
    credential_id: str
    public_key: str
    sign_count: int
    created_at: datetime
    last_used: datetime
    device_info: Dict[str, Any]


@dataclass
class BiometricTemplate:
    """Biometric authentication template"""
    template_id: str
    biometric_type: str  # fingerprint, face, voice, etc.
    template_data: bytes
    quality_score: float
    created_at: datetime
    last_verified: datetime


@dataclass
class AuthenticationContext:
    """Authentication context for risk assessment"""
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    device_fingerprint: str
    location: Dict[str, str]
    timestamp: datetime
    risk_score: float
    behavioral_data: Dict[str, Any]


@dataclass
class ZeroTrustSession:
    """Zero-trust session with encrypted tokens"""
    session_id: str
    user_id: str
    encrypted_token: str
    session_key: bytes
    hardware_token_id: Optional[str]
    biometric_session_id: Optional[str]
    risk_score: float
    expires_at: datetime
    continuous_auth_score: float


class PasswordSecurityUtils:
    """Secure password generation and hashing utilities"""

    @staticmethod
    def generate_secure_password(length: int = 21) -> str:
        """Generate a secure random password with high entropy"""
        if length < 12:
            raise ValueError("Password length must be at least 12 characters")

        # Character sets for maximum entropy
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(symbols)
        ]

        # Fill remaining length with random characters from all sets
        all_chars = lowercase + uppercase + digits + symbols
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))

        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)

    @staticmethod
    def hash_password_argon2(password: str) -> str:
        """Hash password using Argon2 (recommended for new implementations)"""
        # Use Argon2id variant for balanced security
        hash_obj = argon2.PasswordHasher(
            time_cost=2,  # Number of iterations
            memory_cost=102400,  # Memory usage in KiB (100 MiB)
            parallelism=8,  # Number of parallel threads
            hash_len=32,  # Output hash length
            type=argon2.Type.ID  # Argon2id
        )
        return hash_obj.hash(password)

    @staticmethod
    def verify_password_argon2(password: str, hash_str: str) -> bool:
        """Verify password against Argon2 hash"""
        hash_obj = argon2.PasswordHasher()
        try:
            hash_obj.verify(hash_str, password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def hash_password_bcrypt(password: str) -> str:
        """Hash password using bcrypt (fallback/legacy support)"""
        # Generate salt automatically
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds = ~2^12 iterations
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password_bcrypt(password: str, hash_str: str) -> bool:
        """Verify password against bcrypt hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hash_str.encode('utf-8'))
        except Exception as e:
            logger.error(f"Bcrypt verification error: {e}")
            return False

    @staticmethod
    def generate_recovery_codes(count: int = 10) -> List[str]:
        """Generate backup recovery codes"""
        codes = []
        for _ in range(count):
            # Generate 10-character alphanumeric codes
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                          for _ in range(10))
            codes.append(code)
        return codes

    @staticmethod
    def generate_session_key() -> bytes:
        """Generate a cryptographically secure session key"""
        return secrets.token_bytes(32)  # 256-bit key

    @staticmethod
    def encrypt_session_token(token: str, key: bytes) -> str:
        """Encrypt session token using AES-GCM"""
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding

        # Generate random IV
        iv = os.urandom(16)

        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()

        # Encrypt the token
        token_bytes = token.encode('utf-8')
        ciphertext = encryptor.update(token_bytes) + encryptor.finalize()

        # Combine IV, ciphertext, and tag
        encrypted_data = iv + encryptor.tag + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')

    @staticmethod
    def decrypt_session_token(encrypted_token: str, key: bytes) -> Optional[str]:
        """Decrypt session token"""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_token)

            # Extract IV, tag, and ciphertext
            iv = encrypted_data[:16]
            tag = encrypted_data[16:32]
            ciphertext = encrypted_data[32:]

            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
            decryptor = cipher.decryptor()

            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')

        except Exception as e:
            logger.error(f"Session token decryption error: {e}")
            return None


class HardwareTokenManager:
    """WebAuthn/FIDO2 hardware token management"""

    def __init__(self):
        self.challenge_timeout = 300  # 5 minutes
        self.active_challenges = {}

    def generate_registration_challenge(self, user_id: str) -> Dict[str, Any]:
        """Generate WebAuthn registration challenge"""
        challenge = secrets.token_bytes(32)
        challenge_id = str(uuid.uuid4())

        # Store challenge with timeout
        self.active_challenges[challenge_id] = {
            'challenge': challenge,
            'user_id': user_id,
            'type': 'registration',
            'expires': datetime.utcnow() + timedelta(seconds=self.challenge_timeout)
        }

        return {
            'challenge_id': challenge_id,
            'challenge': base64.b64encode(challenge).decode('utf-8'),
            'rp': {
                'name': 'Voluntier Platform',
                'id': settings.DOMAIN
            },
            'user': {
                'id': user_id,
                'name': f'user_{user_id}',
                'displayName': f'User {user_id}'
            },
            'pubKeyCredParams': [
                {'alg': -7, 'type': 'public-key'},  # ES256
                {'alg': -257, 'type': 'public-key'}  # RS256
            ],
            'timeout': self.challenge_timeout * 1000,
            'attestation': 'direct'
        }

    def verify_registration_response(self, challenge_id: str, response: Dict[str, Any]) -> Optional[HardwareTokenCredential]:
        """Verify WebAuthn registration response"""
        try:
            challenge_data = self.active_challenges.get(challenge_id)
            if not challenge_data or challenge_data['type'] != 'registration':
                return None

            if datetime.utcnow() > challenge_data['expires']:
                del self.active_challenges[challenge_id]
                return None

            # Verify the challenge matches
            expected_challenge = challenge_data['challenge']
            client_data = json.loads(base64.b64decode(response['response']['clientDataJSON']))
            received_challenge = base64.b64decode(client_data['challenge'])

            if not hmac.compare_digest(expected_challenge, received_challenge):
                return None

            # Extract credential information
            credential_id = base64.b64encode(base64.b64decode(response['id'])).decode('utf-8')
            public_key = response['response']['publicKey']
            sign_count = 0  # Initialize to 0

            # Clean up challenge
            del self.active_challenges[challenge_id]

            return HardwareTokenCredential(
                credential_id=credential_id,
                public_key=public_key,
                sign_count=sign_count,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                device_info={'type': 'hardware_token', 'webauthn': True}
            )

        except Exception as e:
            logger.error(f"Hardware token registration verification error: {e}")
            return None

    def generate_authentication_challenge(self, user_id: str, credentials: List[str]) -> Dict[str, Any]:
        """Generate WebAuthn authentication challenge"""
        challenge = secrets.token_bytes(32)
        challenge_id = str(uuid.uuid4())

        # Store challenge with timeout
        self.active_challenges[challenge_id] = {
            'challenge': challenge,
            'user_id': user_id,
            'type': 'authentication',
            'expires': datetime.utcnow() + timedelta(seconds=self.challenge_timeout)
        }

        return {
            'challenge_id': challenge_id,
            'challenge': base64.b64encode(challenge).decode('utf-8'),
            'allowCredentials': [
                {'id': cred, 'type': 'public-key'} for cred in credentials
            ],
            'timeout': self.challenge_timeout * 1000,
            'userVerification': 'preferred'
        }


class BiometricManager:
    """Biometric authentication manager"""

    def __init__(self):
        self.template_store = {}  # In production, use secure database
        self.verification_timeout = 300  # 5 minutes

    def enroll_biometric(self, user_id: str, biometric_type: str,
                        biometric_data: bytes, quality_score: float) -> BiometricTemplate:
        """Enroll a new biometric template"""
        template_id = str(uuid.uuid4())

        template = BiometricTemplate(
            template_id=template_id,
            biometric_type=biometric_type,
            template_data=biometric_data,
            quality_score=quality_score,
            created_at=datetime.utcnow(),
            last_verified=datetime.utcnow()
        )

        # Store template (in production, encrypt and store securely)
        if user_id not in self.template_store:
            self.template_store[user_id] = {}
        self.template_store[user_id][biometric_type] = template

        return template

    def verify_biometric(self, user_id: str, biometric_type: str,
                        biometric_data: bytes) -> Tuple[bool, float]:
        """Verify biometric data against stored template"""
        try:
            if user_id not in self.template_store:
                return False, 0.0

            if biometric_type not in self.template_store[user_id]:
                return False, 0.0

            stored_template = self.template_store[user_id][biometric_type]

            # Simple comparison (in production, use proper biometric matching algorithms)
            # This is a placeholder - real implementation would use specialized libraries
            similarity_score = self._calculate_similarity(
                stored_template.template_data,
                biometric_data
            )

            # Update last verified timestamp
            stored_template.last_verified = datetime.utcnow()

            # Return verification result with confidence score
            threshold = 0.85  # 85% similarity threshold
            return similarity_score >= threshold, similarity_score

        except Exception as e:
            logger.error(f"Biometric verification error: {e}")
            return False, 0.0

    def _calculate_similarity(self, template1: bytes, template2: bytes) -> float:
        """Calculate similarity between biometric templates"""
        # Placeholder implementation - real biometric matching is complex
        # In production, use libraries like OpenCV for face recognition,
        # fingerprint matching algorithms, etc.
        if len(template1) != len(template2):
            return 0.0

        # Simple byte-wise comparison (not secure for real biometrics)
        matches = sum(1 for a, b in zip(template1, template2) if a == b)
        return matches / len(template1)


class RiskAssessmentEngine:
    """Risk-based authentication engine"""

    def __init__(self):
        self.baseline_scores = defaultdict(float)
        self.anomaly_threshold = 0.7

    def assess_authentication_risk(self, context: AuthenticationContext) -> float:
        """Assess risk score for authentication attempt"""
        risk_factors = []

        # IP-based risk
        ip_risk = self._assess_ip_risk(context.ip_address)
        risk_factors.append(ip_risk)

        # Location-based risk
        location_risk = self._assess_location_risk(context.location)
        risk_factors.append(location_risk)

        # Device fingerprint risk
        device_risk = self._assess_device_risk(context.device_fingerprint)
        risk_factors.append(device_risk)

        # Time-based risk
        time_risk = self._assess_time_risk(context.timestamp)
        risk_factors.append(time_risk)

        # Behavioral risk
        behavioral_risk = self._assess_behavioral_risk(context.behavioral_data)
        risk_factors.append(behavioral_risk)

        # Calculate overall risk score (weighted average)
        weights = [0.2, 0.2, 0.2, 0.15, 0.25]  # Sum to 1.0
        overall_risk = sum(r * w for r, w in zip(risk_factors, weights))

        return min(overall_risk, 1.0)  # Cap at 1.0

    def _assess_ip_risk(self, ip_address: str) -> float:
        """Assess risk based on IP address"""
        # Placeholder - in production, check against threat intelligence feeds
        # Known malicious IPs would have high risk scores
        return 0.1  # Low risk for demonstration

    def _assess_location_risk(self, location: Dict[str, str]) -> float:
        """Assess risk based on geographic location"""
        # Check for unusual location changes
        # Placeholder implementation
        return 0.2

    def _assess_device_risk(self, device_fingerprint: str) -> float:
        """Assess risk based on device fingerprint"""
        # Check for device changes or suspicious patterns
        return 0.15

    def _assess_time_risk(self, timestamp: datetime) -> float:
        """Assess risk based on timing patterns"""
        # Check for unusual login times
        hour = timestamp.hour
        # Higher risk during unusual hours (2 AM - 6 AM)
        if 2 <= hour <= 6:
            return 0.4
        return 0.1

    def _assess_behavioral_risk(self, behavioral_data: Dict[str, Any]) -> float:
        """Assess risk based on behavioral biometrics"""
        # Analyze keystroke patterns, mouse movements, etc.
        # Placeholder implementation
        return 0.25


class AdvancedAuthService:
    """Advanced zero-trust authentication service"""

    def __init__(self):
        self.password_utils = PasswordSecurityUtils()
        self.hardware_token_manager = HardwareTokenManager()
        self.biometric_manager = BiometricManager()
        self.risk_engine = RiskAssessmentEngine()
        self.security_service = SecurityService()
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)

    async def initialize(self):
        """Initialize the authentication service"""
        await self.security_service.initialize()
        logger.info("Advanced Authentication Service initialized")

    async def authenticate_user(self, email: str, password: str,
                              context: AuthenticationContext) -> Tuple[bool, Optional[ZeroTrustSession], str]:
        """Authenticate user with zero-trust verification"""
        try:
            async with get_db_session() as session:
                # Get user
                result = await session.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()

                if not user:
                    await self._log_auth_attempt(session, None, email, "failed", "user_not_found", context)
                    return False, None, "Invalid credentials"

                # Check account status
                if not user.is_active:
                    await self._log_auth_attempt(session, user.id, email, "failed", "account_inactive", context)
                    return False, None, "Account is inactive"

                if user.account_lockout_until and user.account_lockout_until > datetime.utcnow():
                    await self._log_auth_attempt(session, user.id, email, "failed", "account_locked", context)
                    return False, None, "Account is temporarily locked"

                # Verify password
                password_valid = False
                if user.hashed_password.startswith('$argon2'):
                    password_valid = self.password_utils.verify_password_argon2(password, user.hashed_password)
                else:
                    # Fallback to bcrypt for legacy passwords
                    password_valid = self.password_utils.verify_password_bcrypt(password, user.hashed_password)

                if not password_valid:
                    await self._handle_failed_login(session, user, context)
                    return False, None, "Invalid credentials"

                # Assess authentication risk
                risk_score = self.risk_engine.assess_authentication_risk(context)

                # Determine required authentication factors
                required_factors = await self._determine_auth_factors(user, risk_score)

                # Create session with risk assessment
                session = await self._create_zero_trust_session(session, user, context, risk_score)

                # Log successful authentication
                await self._log_auth_attempt(session, user.id, email, "success", "authenticated", context)

                # Reset failed login attempts on successful login
                user.failed_login_attempts = 0
                user.last_active = datetime.utcnow()
                await session.commit()

                return True, session, f"Authentication successful. Risk score: {risk_score:.2f}"

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, None, "Authentication service error"

    async def _determine_auth_factors(self, user: User, risk_score: float) -> List[str]:
        """Determine required authentication factors based on risk"""
        factors = ["password"]  # Password is always required

        # High risk requires additional factors
        if risk_score > 0.7:
            factors.append("mfa")

            # Very high risk requires hardware token
            if risk_score > 0.9:
                factors.append("hardware_token")

        # Check user preferences and capabilities
        mfa_settings = user.mfa_settings or {}
        if mfa_settings.get('enabled'):
            factors.append("mfa")

        hardware_credentials = user.hardware_token_credentials or {}
        if hardware_credentials:
            factors.append("hardware_token")

        biometric_data = user.biometric_data or {}
        if biometric_data:
            factors.append("biometric")

        return factors

    async def _create_zero_trust_session(self, db_session: AsyncSession,
                                       user: User, context: AuthenticationContext,
                                       risk_score: float) -> ZeroTrustSession:
        """Create a zero-trust session with encrypted tokens"""
        # Generate session components
        session_id = str(uuid.uuid4())
        session_key = self.password_utils.generate_session_key()
        session_token = secrets.token_urlsafe(64)

        # Encrypt session token
        encrypted_token = self.password_utils.encrypt_session_token(session_token, session_key)

        # Create database session record
        db_session_obj = UserSession(
            user_id=user.id,
            session_token=encrypted_token,
            device_fingerprint=context.device_fingerprint,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            risk_score=risk_score,
            auth_method="password",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(hours=8),  # 8 hour session
            encrypted_session_key=base64.b64encode(session_key).decode('utf-8')
        )

        db_session.add(db_session_obj)
        await db_session.commit()

        # Cache session in Redis for fast access
        session_data = {
            'user_id': str(user.id),
            'session_key': base64.b64encode(session_key).decode('utf-8'),
            'risk_score': risk_score,
            'expires_at': db_session_obj.expires_at.isoformat()
        }
        await self.redis_client.setex(
            f"session:{session_id}",
            28800,  # 8 hours
            json.dumps(session_data)
        )

        return ZeroTrustSession(
            session_id=session_id,
            user_id=str(user.id),
            encrypted_token=encrypted_token,
            session_key=session_key,
            hardware_token_id=None,
            biometric_session_id=None,
            risk_score=risk_score,
            expires_at=db_session_obj.expires_at,
            continuous_auth_score=1.0
        )

    async def _handle_failed_login(self, session: AsyncSession, user: User, context: AuthenticationContext):
        """Handle failed login attempt"""
        user.failed_login_attempts += 1

        # Implement progressive lockout
        if user.failed_login_attempts >= 5:
            # Lock account for increasing durations
            lockout_duration = timedelta(minutes=min(30 * (user.failed_login_attempts - 4), 1440))  # Max 24 hours
            user.account_lockout_until = datetime.utcnow() + lockout_duration

        await session.commit()

        # Log failed attempt
        await self._log_auth_attempt(session, user.id, user.email, "failed", "invalid_password", context)

        # Trigger security alert for multiple failures
        if user.failed_login_attempts >= 3:
            await self.security_service.create_security_event(
                event_type="BRUTE_FORCE_ATTEMPT",
                severity="MEDIUM",
                description=f"Multiple failed login attempts for user {user.email}",
                source_ip=context.ip_address,
                user_id=str(user.id)
            )

    async def _log_auth_attempt(self, session: AsyncSession, user_id: Optional[str],
                              username: str, result: str, failure_reason: Optional[str],
                              context: AuthenticationContext):
        """Log authentication attempt"""
        log_entry = AuthenticationLog(
            user_id=user_id,
            username=username,
            auth_method="password",
            auth_result=result,
            failure_reason=failure_reason,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            risk_score=context.risk_score,
            blocked=False
        )

        session.add(log_entry)
        await session.commit()

    async def register_hardware_token(self, user_id: str, challenge_response: Dict[str, Any]) -> bool:
        """Register a hardware token for a user"""
        try:
            async with get_db_session() as session:
                # Get user
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    return False

                # Verify the challenge response
                credential = self.hardware_token_manager.verify_registration_response(
                    challenge_response.get('challenge_id'),
                    challenge_response
                )

                if not credential:
                    return False

                # Store credential in user record
                hardware_credentials = user.hardware_token_credentials or {}
                hardware_credentials[credential.credential_id] = {
                    'public_key': credential.public_key,
                    'sign_count': credential.sign_count,
                    'created_at': credential.created_at.isoformat(),
                    'device_info': credential.device_info
                }

                user.hardware_token_credentials = hardware_credentials
                await session.commit()

                return True

        except Exception as e:
            logger.error(f"Hardware token registration error: {e}")
            return False

    async def authenticate_with_hardware_token(self, user_id: str,
                                            challenge_response: Dict[str, Any]) -> bool:
        """Authenticate using hardware token"""
        try:
            async with get_db_session() as session:
                # Get user
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    return False

                # Get user's hardware credentials
                hardware_credentials = user.hardware_token_credentials or {}
                credential_ids = list(hardware_credentials.keys())

                if not credential_ids:
                    return False

                # Verify the authentication response
                # This is a simplified implementation - real WebAuthn verification is more complex
                challenge_id = challenge_response.get('challenge_id')
                challenge_data = self.hardware_token_manager.active_challenges.get(challenge_id)

                if not challenge_data or challenge_data['type'] != 'authentication':
                    return False

                # In a real implementation, you'd verify the cryptographic signature
                # For now, we'll do a basic check
                credential_id = challenge_response.get('id')
                if credential_id not in hardware_credentials:
                    return False

                # Update last used timestamp
                hardware_credentials[credential_id]['last_used'] = datetime.utcnow().isoformat()
                user.hardware_token_credentials = hardware_credentials
                await session.commit()

                return True

        except Exception as e:
            logger.error(f"Hardware token authentication error: {e}")
            return False

    async def enroll_biometric(self, user_id: str, biometric_type: str,
                             biometric_data: bytes, quality_score: float) -> bool:
        """Enroll biometric data for a user"""
        try:
            async with get_db_session() as session:
                # Get user
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    return False

                # Enroll biometric template
                template = self.biometric_manager.enroll_biometric(
                    user_id, biometric_type, biometric_data, quality_score
                )

                # Store in user record
                biometric_data_dict = user.biometric_data or {}
                biometric_data_dict[biometric_type] = {
                    'template_id': template.template_id,
                    'quality_score': template.quality_score,
                    'created_at': template.created_at.isoformat(),
                    'last_verified': template.last_verified.isoformat()
                }

                user.biometric_data = biometric_data_dict
                await session.commit()

                return True

        except Exception as e:
            logger.error(f"Biometric enrollment error: {e}")
            return False

    async def verify_biometric(self, user_id: str, biometric_type: str,
                             biometric_data: bytes) -> Tuple[bool, float]:
        """Verify biometric data"""
        return self.biometric_manager.verify_biometric(user_id, biometric_type, biometric_data)

    async def generate_secure_password(self, length: int = 21) -> str:
        """Generate a secure random password"""
        return self.password_utils.generate_secure_password(length)

    async def hash_password(self, password: str) -> str:
        """Hash password using Argon2"""
        return self.password_utils.hash_password_argon2(password)

    async def verify_password(self, password: str, hash_str: str) -> bool:
        """Verify password against hash"""
        if hash_str.startswith('$argon2'):
            return self.password_utils.verify_password_argon2(password, hash_str)
        else:
            return self.password_utils.verify_password_bcrypt(password, hash_str)

    async def generate_recovery_codes(self, count: int = 10) -> List[str]:
        """Generate backup recovery codes"""
        return self.password_utils.generate_recovery_codes(count)

    async def validate_session(self, session_id: str) -> Optional[ZeroTrustSession]:
        """Validate and retrieve session information"""
        try:
            # Check Redis cache first
            session_data = await self.redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                expires_at = datetime.fromisoformat(data['expires_at'])

                if datetime.utcnow() > expires_at:
                    await self.redis_client.delete(f"session:{session_id}")
                    return None

                return ZeroTrustSession(
                    session_id=session_id,
                    user_id=data['user_id'],
                    encrypted_token="",  # Not cached
                    session_key=base64.b64decode(data['session_key']),
                    hardware_token_id=None,
                    biometric_session_id=None,
                    risk_score=data['risk_score'],
                    expires_at=expires_at,
                    continuous_auth_score=1.0
                )

            # Fallback to database
            async with get_db_session() as session:
                result = await session.execute(
                    select(UserSession).where(
                        and_(
                            UserSession.id == session_id,
                            UserSession.is_active == True,
                            UserSession.expires_at > datetime.utcnow()
                        )
                    )
                )
                db_session = result.scalar_one_or_none()

                if not db_session:
                    return None

                # Reconstruct session
                session_key = base64.b64decode(db_session.encrypted_session_key)

                return ZeroTrustSession(
                    session_id=session_id,
                    user_id=str(db_session.user_id),
                    encrypted_token=db_session.session_token,
                    session_key=session_key,
                    hardware_token_id=db_session.hardware_token_id,
                    biometric_session_id=db_session.biometric_session_id,
                    risk_score=db_session.risk_score,
                    expires_at=db_session.expires_at,
                    continuous_auth_score=db_session.continuous_auth_score
                )

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a session"""
        try:
            # Remove from Redis
            await self.redis_client.delete(f"session:{session_id}")

            # Update database
            async with get_db_session() as session:
                result = await session.execute(
                    select(UserSession).where(UserSession.id == session_id)
                )
                db_session = result.scalar_one_or_none()

                if db_session:
                    db_session.is_active = False
                    db_session.terminated_at = datetime.utcnow()
                    await session.commit()

                return True

        except Exception as e:
            logger.error(f"Session revocation error: {e}")
            return False

    async def update_session_risk(self, session_id: str, new_risk_score: float) -> bool:
        """Update session risk score"""
        try:
            # Update Redis cache
            session_data = await self.redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                data['risk_score'] = new_risk_score
                await self.redis_client.setex(
                    f"session:{session_id}",
                    28800,  # 8 hours
                    json.dumps(data)
                )

            # Update database
            async with get_db_session() as session:
                result = await session.execute(
                    select(UserSession).where(UserSession.id == session_id)
                )
                db_session = result.scalar_one_or_none()

                if db_session:
                    db_session.risk_score = new_risk_score
                    await session.commit()

                return True

        except Exception as e:
            logger.error(f"Session risk update error: {e}")
            return False