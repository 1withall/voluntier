"""Authentication and authorization activities."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from temporalio import activity
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from voluntier.database import get_db_session_context
from voluntier.models import User, AdminUser, UserSession, SecurityLog
from voluntier.services.auth import AdvancedAuthService
from voluntier.services.security import SecurityService
from voluntier.utils.validation import validate_email, validate_password_strength
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)


class AuthActivities:
    """Activities related to authentication and authorization."""
    
    @activity.defn
    async def validate_login_attempt(self, login_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate login attempt with security checks.
        
        Args:
            login_data: Login attempt data
            
        Returns:
            Validation result with security metadata
        """
        logger.info(f"Validating login attempt for: {login_data.get('email')}")
        
        email = login_data.get("email", "").lower()
        password = login_data.get("password", "")
        ip_address = login_data.get("ip_address", "unknown")
        user_agent = login_data.get("user_agent", "unknown")
        
        errors = []
        security_flags = []
        
        # Basic validation
        if not email or not validate_email(email):
            errors.append("Invalid email format")
        
        if not password:
            errors.append("Password is required")
        
        # Security checks
        security_service = SecurityService()
        
        # Check for brute force attempts
        brute_force_check = await security_service.check_brute_force_attempt(
            email=email,
            ip_address=ip_address,
            time_window_minutes=15,
            max_attempts=5
        )
        
        if brute_force_check["is_blocked"]:
            errors.append("Too many login attempts. Account temporarily locked.")
            security_flags.append("brute_force_detected")
        
        # Check for suspicious IP patterns
        ip_check = await security_service.analyze_ip_reputation(ip_address)
        if ip_check["risk_score"] > 0.7:
            security_flags.append("suspicious_ip")
        
        # Check for unusual login patterns
        login_pattern_check = await security_service.analyze_login_pattern(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if login_pattern_check["anomaly_score"] > 0.8:
            security_flags.append("unusual_pattern")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "security_flags": security_flags,
            "requires_additional_verification": len(security_flags) > 0,
            "metadata": {
                "validation_timestamp": datetime.utcnow().isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "brute_force_check": brute_force_check,
                "ip_reputation": ip_check,
            },
        }
    
    @activity.defn
    async def authenticate_user(self, auth_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate user credentials.
        
        Args:
            auth_request: Authentication request data
            
        Returns:
            Authentication result
        """
        email = auth_request["email"].lower()
        password = auth_request["password"]
        
        logger.info(f"Authenticating user: {email}")
        
        try:
            auth_service = AdvancedAuthService()
            
            async with get_db_session_context() as session:
                # Find user
                stmt = select(User).where(User.email == email)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    # Record failed login attempt
                    await self._log_security_event(
                        session, 
                        "failed_login", 
                        {"email": email, "reason": "user_not_found"}
                    )
                    return {
                        "authenticated": False,
                        "reason": "invalid_credentials",
                        "user_id": None,
                    }
                
                # Verify password
                is_valid_password = auth_service.verify_password(password, user.hashed_password)
                
                if not is_valid_password:
                    # Increment failed attempts
                    user.failed_login_attempts += 1
                    user.last_failed_login = datetime.utcnow()
                    
                    # Lock account if too many attempts
                    if user.failed_login_attempts >= 5:
                        user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                    
                    await session.commit()
                    
                    await self._log_security_event(
                        session,
                        "failed_login",
                        {"user_id": str(user.id), "reason": "invalid_password"}
                    )
                    
                    # Integrate with security monitoring for failed attempt
                    await auth_service.integrate_with_security_monitoring({
                        "event_type": "failed_authentication",
                        "description": f"Failed authentication attempt for user {user.email}",
                        "user_id": str(user.id),
                        "auth_method": "password",
                        "ip_address": auth_request.get("ip_address", "unknown"),
                        "user_agent": auth_request.get("user_agent", "unknown"),
                        "risk_score": 0.8,  # High risk for failed auth
                        "location": {},
                        "behavioral_data": {}
                    })
                    
                    return {
                        "authenticated": False,
                        "reason": "invalid_credentials",
                        "user_id": str(user.id),
                        "attempts_remaining": max(0, 5 - user.failed_login_attempts),
                    }
                
                # Check if account is locked
                if user.locked_until and user.locked_until > datetime.utcnow():
                    return {
                        "authenticated": False,
                        "reason": "account_locked",
                        "user_id": str(user.id),
                        "locked_until": user.locked_until.isoformat(),
                    }
                
                # Check if account is active
                if not user.is_active:
                    return {
                        "authenticated": False,
                        "reason": "account_disabled",
                        "user_id": str(user.id),
                    }
                
                # Successful authentication
                user.failed_login_attempts = 0
                user.last_login = datetime.utcnow()
                user.locked_until = None
                await session.commit()
                
                await self._log_security_event(
                    session,
                    "successful_login",
                    {"user_id": str(user.id)}
                )
                
                # Integrate with security monitoring
                await auth_service.integrate_with_security_monitoring({
                    "event_type": "successful_authentication",
                    "description": f"User {user.email} successfully authenticated",
                    "user_id": str(user.id),
                    "auth_method": "password",
                    "ip_address": auth_request.get("ip_address", "unknown"),
                    "user_agent": auth_request.get("user_agent", "unknown"),
                    "risk_score": 0.1,  # Low risk for successful auth
                    "location": {},  # Would be populated from IP geolocation
                    "behavioral_data": {}
                })
                
                return {
                    "authenticated": True,
                    "user_id": str(user.id),
                    "user_type": user.role.value,
                    "user_data": {
                        "email": user.email,
                        "name": user.name,
                        "verification_status": user.verification_status.value,
                        "is_email_verified": user.email_verified,
                    },
                }
        
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    @activity.defn
    async def create_user_session(self, session_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user session.
        
        Args:
            session_request: Session creation request
            
        Returns:
            Session creation result
        """
        user_id = session_request["user_id"]
        ip_address = session_request.get("ip_address", "unknown")
        user_agent = session_request.get("user_agent", "unknown")
        
        logger.info(f"Creating session for user: {user_id}")
        
        try:
            auth_service = AdvancedAuthService()
            
            # Generate session token
            session_token = auth_service.generate_session_token()
            session_id = str(uuid.uuid4())
            
            # Set session expiry (8 hours default)
            expires_at = datetime.utcnow() + timedelta(hours=8)
            
            async with get_db_session_context() as session:
                # Create session record
                user_session = UserSession(
                    id=uuid.UUID(session_id),
                    user_id=uuid.UUID(user_id),
                    token=session_token,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    expires_at=expires_at,
                    is_active=True,
                )
                
                session.add(user_session)
                await session.commit()
                
                # Log session creation
                await self._log_security_event(
                    session,
                    "session_created",
                    {
                        "user_id": user_id,
                        "session_id": session_id,
                        "ip_address": ip_address,
                    }
                )
                
                return {
                    "session_created": True,
                    "session_id": session_id,
                    "session_token": session_token,
                    "expires_at": expires_at.isoformat(),
                    "user_id": user_id,
                }
        
        except Exception as e:
            logger.error(f"Failed to create user session: {str(e)}")
            raise
    
    @activity.defn
    async def validate_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an existing user session.
        
        Args:
            session_data: Session validation data
            
        Returns:
            Session validation result
        """
        session_token = session_data["session_token"]
        ip_address = session_data.get("ip_address", "unknown")
        
        logger.info(f"Validating session token: {session_token[:10]}...")
        
        try:
            async with get_db_session_context() as session:
                # Find session
                stmt = select(UserSession).where(
                    UserSession.token == session_token,
                    UserSession.is_active == True
                )
                result = await session.execute(stmt)
                user_session = result.scalar_one_or_none()
                
                if not user_session:
                    return {
                        "valid": False,
                        "reason": "session_not_found",
                    }
                
                # Check if session has expired
                if user_session.expires_at < datetime.utcnow():
                    # Deactivate expired session
                    user_session.is_active = False
                    await session.commit()
                    
                    return {
                        "valid": False,
                        "reason": "session_expired",
                        "expired_at": user_session.expires_at.isoformat(),
                    }
                
                # Update last activity
                user_session.last_activity = datetime.utcnow()
                await session.commit()
                
                # Get user data
                user_stmt = select(User).where(User.id == user_session.user_id)
                user_result = await session.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                
                if not user or not user.is_active:
                    return {
                        "valid": False,
                        "reason": "user_inactive",
                    }
                
                return {
                    "valid": True,
                    "user_id": str(user.id),
                    "user_type": user.role.value,
                    "session_id": str(user_session.id),
                    "expires_at": user_session.expires_at.isoformat(),
                    "user_data": {
                        "email": user.email,
                        "name": user.name,
                        "verification_status": user.verification_status.value,
                    },
                }
        
        except Exception as e:
            logger.error(f"Session validation failed: {str(e)}")
            raise
    
    @activity.defn
    async def revoke_session(self, revocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Revoke a user session.
        
        Args:
            revocation_data: Session revocation data
            
        Returns:
            Revocation result
        """
        session_token = revocation_data.get("session_token")
        user_id = revocation_data.get("user_id")
        revoke_all = revocation_data.get("revoke_all", False)
        
        logger.info(f"Revoking session(s) for user: {user_id}")
        
        try:
            async with get_db_session_context() as session:
                if revoke_all:
                    # Revoke all sessions for user
                    stmt = update(UserSession).where(
                        UserSession.user_id == uuid.UUID(user_id),
                        UserSession.is_active == True
                    ).values(
                        is_active=False,
                        revoked_at=datetime.utcnow()
                    )
                    result = await session.execute(stmt)
                    revoked_count = result.rowcount
                else:
                    # Revoke specific session
                    stmt = update(UserSession).where(
                        UserSession.token == session_token,
                        UserSession.is_active == True
                    ).values(
                        is_active=False,
                        revoked_at=datetime.utcnow()
                    )
                    result = await session.execute(stmt)
                    revoked_count = result.rowcount
                
                await session.commit()
                
                # Log session revocation
                await self._log_security_event(
                    session,
                    "session_revoked",
                    {
                        "user_id": user_id,
                        "revoked_count": revoked_count,
                        "revoke_all": revoke_all,
                    }
                )
                
                return {
                    "revoked": revoked_count > 0,
                    "revoked_count": revoked_count,
                    "user_id": user_id,
                }
        
        except Exception as e:
            logger.error(f"Session revocation failed: {str(e)}")
            raise
    
    @activity.defn
    async def check_user_privileges(self, privilege_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check user privileges for specific actions.
        
        Args:
            privilege_request: Privilege check request
            
        Returns:
            Privilege check result
        """
        user_id = privilege_request["user_id"]
        required_privilege = privilege_request["privilege"]
        required_level = privilege_request.get("level", "read")
        resource_id = privilege_request.get("resource_id")
        
        logger.info(f"Checking privileges for user {user_id}: {required_privilege}:{required_level}")
        
        try:
            async with get_db_session_context() as session:
                # Get user
                stmt = select(User).where(User.id == uuid.UUID(user_id))
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    return {
                        "has_privilege": False,
                        "reason": "user_not_found",
                    }
                
                # Check if user is super admin (has all privileges)
                if hasattr(user, 'is_super_admin') and user.is_super_admin:
                    return {
                        "has_privilege": True,
                        "level": "super_admin",
                        "reason": "super_admin_access",
                    }
                
                # Check specific privileges (simplified - would check against privilege system)
                privilege_mapping = {
                    "security_dashboard": ["admin", "super_admin"],
                    "telemetry_dashboard": ["admin", "super_admin"],
                    "user_management": ["admin", "super_admin"],
                    "event_management": ["organization_admin", "admin", "super_admin"],
                    "verification_management": ["admin", "super_admin"],
                }
                
                required_roles = privilege_mapping.get(required_privilege, [])
                user_role = user.role.value
                
                has_privilege = user_role in required_roles
                
                return {
                    "has_privilege": has_privilege,
                    "user_role": user_role,
                    "required_roles": required_roles,
                    "privilege": required_privilege,
                    "level": required_level,
                }
        
        except Exception as e:
            logger.error(f"Privilege check failed: {str(e)}")
            raise
    
        except Exception as e:
            logger.error(f"Privilege check failed: {str(e)}")
            raise
    
    @activity.defn
    async def zero_trust_authenticate(self, auth_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform zero-trust authentication with risk assessment.
        
        Args:
            auth_request: Authentication request with context
            
        Returns:
            Zero-trust authentication result
        """
        from voluntier.services.auth import AdvancedAuthService, AuthenticationContext
        
        email = auth_request["email"].lower()
        password = auth_request["password"]
        
        logger.info(f"Zero-trust authentication for: {email}")
        
        try:
            # Create authentication context
            context = AuthenticationContext(
                user_id=None,  # Will be set after user lookup
                ip_address=auth_request.get("ip_address", "unknown"),
                user_agent=auth_request.get("user_agent", "unknown"),
                device_fingerprint=auth_request.get("device_fingerprint", ""),
                location=auth_request.get("location", {}),
                timestamp=datetime.utcnow(),
                risk_score=0.0,  # Will be calculated
                behavioral_data=auth_request.get("behavioral_data", {})
            )
            
            auth_service = AdvancedAuthService()
            await auth_service.initialize()
            
            # Perform authentication
            success, session, message = await auth_service.authenticate_user(email, password, context)
            
            result = {
                "authenticated": success,
                "message": message,
                "session_id": session.session_id if session else None,
                "user_id": session.user_id if session else None,
                "risk_score": session.risk_score if session else 0.0,
                "requires_additional_factors": False,
                "additional_factors": []
            }
            
            if success and session:
                # Check if additional factors are required
                async with get_db_session_context() as db_session:
                    stmt = select(User).where(User.email == email)
                    db_result = await db_session.execute(stmt)
                    user = db_result.scalar_one_or_none()
                    
                    if user:
                        required_factors = await auth_service._determine_auth_factors(user, session.risk_score)
                        result["requires_additional_factors"] = len(required_factors) > 1
                        result["additional_factors"] = required_factors[1:]  # Exclude password
                
                # Log successful authentication
                logger.info(f"Zero-trust authentication successful for {email}, risk: {session.risk_score:.2f}")
            else:
                # Log failed authentication
                logger.warning(f"Zero-trust authentication failed for {email}: {message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Zero-trust authentication error: {str(e)}")
            return {
                "authenticated": False,
                "message": "Authentication service error",
                "session_id": None,
                "user_id": None,
                "risk_score": 1.0,
                "requires_additional_factors": False,
                "additional_factors": []
            }
    
    @activity.defn
    async def register_hardware_token(self, token_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a hardware token for zero-trust authentication.
        
        Args:
            token_request: Hardware token registration request
            
        Returns:
            Registration result
        """
        from voluntier.services.auth import AdvancedAuthService
        
        user_id = token_request["user_id"]
        challenge_response = token_request["challenge_response"]
        
        logger.info(f"Registering hardware token for user: {user_id}")
        
        try:
            auth_service = AdvancedAuthService()
            await auth_service.initialize()
            
            success = await auth_service.register_hardware_token(user_id, challenge_response)
            
            return {
                "registered": success,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Hardware token registration error: {str(e)}")
            return {
                "registered": False,
                "user_id": user_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @activity.defn
    async def authenticate_with_hardware_token(self, token_auth_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate using hardware token.
        
        Args:
            token_auth_request: Hardware token authentication request
            
        Returns:
            Authentication result
        """
        from voluntier.services.auth import AdvancedAuthService
        
        user_id = token_auth_request["user_id"]
        challenge_response = token_auth_request["challenge_response"]
        
        logger.info(f"Hardware token authentication for user: {user_id}")
        
        try:
            auth_service = AdvancedAuthService()
            await auth_service.initialize()
            
            success = await auth_service.authenticate_with_hardware_token(user_id, challenge_response)
            
            # Integrate with security monitoring
            event_type = "successful_hardware_token_auth" if success else "failed_hardware_token_auth"
            risk_score = 0.1 if success else 0.7
            
            await auth_service.integrate_with_security_monitoring({
                "event_type": event_type,
                "description": f"Hardware token authentication {'successful' if success else 'failed'} for user {user_id}",
                "user_id": user_id,
                "auth_method": "hardware_token",
                "ip_address": token_auth_request.get("ip_address", "unknown"),
                "user_agent": token_auth_request.get("user_agent", "unknown"),
                "risk_score": risk_score,
                "location": {},
                "behavioral_data": {},
                "device_fingerprint": challenge_response.get("device_fingerprint")
            })
            
            return {
                "authenticated": success,
                "user_id": user_id,
                "auth_method": "hardware_token",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Hardware token authentication error: {str(e)}")
            return {
                "authenticated": False,
                "user_id": user_id,
                "auth_method": "hardware_token",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @activity.defn
    async def enroll_biometric_data(self, biometric_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enroll biometric data for authentication.
        
        Args:
            biometric_request: Biometric enrollment request
            
        Returns:
            Enrollment result
        """
        from voluntier.services.auth import AdvancedAuthService
        
        user_id = biometric_request["user_id"]
        biometric_type = biometric_request["biometric_type"]
        biometric_data = biometric_request["biometric_data"]  # base64 encoded
        quality_score = biometric_request.get("quality_score", 0.8)
        
        logger.info(f"Enrolling {biometric_type} biometric for user: {user_id}")
        
        try:
            # Decode biometric data
            import base64
            decoded_data = base64.b64decode(biometric_data)
            
            auth_service = AdvancedAuthService()
            await auth_service.initialize()
            
            success = await auth_service.enroll_biometric(
                user_id, biometric_type, decoded_data, quality_score
            )
            
            return {
                "enrolled": success,
                "user_id": user_id,
                "biometric_type": biometric_type,
                "quality_score": quality_score,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Biometric enrollment error: {str(e)}")
            return {
                "enrolled": False,
                "user_id": user_id,
                "biometric_type": biometric_type,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @activity.defn
    async def verify_biometric_data(self, biometric_verify_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify biometric data for authentication.
        
        Args:
            biometric_verify_request: Biometric verification request
            
        Returns:
            Verification result
        """
        from voluntier.services.auth import AdvancedAuthService
        
        user_id = biometric_verify_request["user_id"]
        biometric_type = biometric_verify_request["biometric_type"]
        biometric_data = biometric_verify_request["biometric_data"]  # base64 encoded
        
        logger.info(f"Verifying {biometric_type} biometric for user: {user_id}")
        
        try:
            # Decode biometric data
            import base64
            decoded_data = base64.b64decode(biometric_data)
            
            auth_service = AdvancedAuthService()
            await auth_service.initialize()
            
            success, confidence = await auth_service.verify_biometric(
                user_id, biometric_type, decoded_data
            )
            
            # Integrate with security monitoring
            event_type = "successful_biometric_auth" if success else "failed_biometric_auth"
            risk_score = 0.1 if success else 0.6
            
            await auth_service.integrate_with_security_monitoring({
                "event_type": event_type,
                "description": f"Biometric authentication {'successful' if success else 'failed'} for user {user_id}",
                "user_id": user_id,
                "auth_method": "biometric",
                "ip_address": biometric_verify_request.get("ip_address", "unknown"),
                "user_agent": biometric_verify_request.get("user_agent", "unknown"),
                "risk_score": risk_score,
                "location": {},
                "behavioral_data": {},
                "biometric_type": biometric_type,
                "confidence_score": confidence
            })
            
            return {
                "verified": success,
                "user_id": user_id,
                "biometric_type": biometric_type,
                "confidence_score": confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Biometric verification error: {str(e)}")
            return {
                "verified": False,
                "user_id": user_id,
                "biometric_type": biometric_type,
                "confidence_score": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @activity.defn
    async def assess_authentication_risk(self, risk_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess authentication risk for continuous monitoring.
        
        Args:
            risk_request: Risk assessment request
            
        Returns:
            Risk assessment result
        """
        from voluntier.services.auth import AuthenticationContext, RiskAssessmentEngine
        
        user_id = risk_request.get("user_id")
        session_id = risk_request.get("session_id")
        
        logger.info(f"Assessing authentication risk for session: {session_id}")
        
        try:
            # Create risk context
            context = AuthenticationContext(
                user_id=user_id,
                ip_address=risk_request.get("ip_address", "unknown"),
                user_agent=risk_request.get("user_agent", "unknown"),
                device_fingerprint=risk_request.get("device_fingerprint", ""),
                location=risk_request.get("location", {}),
                timestamp=datetime.utcnow(),
                risk_score=0.0,  # Will be calculated
                behavioral_data=risk_request.get("behavioral_data", {})
            )
            
            risk_engine = RiskAssessmentEngine()
            risk_score = risk_engine.assess_authentication_risk(context)
            
            # Determine risk level
            if risk_score >= 0.8:
                risk_level = "CRITICAL"
                actions = ["require_mfa", "notify_security", "log_incident"]
            elif risk_score >= 0.6:
                risk_level = "HIGH"
                actions = ["require_mfa", "log_warning"]
            elif risk_score >= 0.4:
                risk_level = "MEDIUM"
                actions = ["monitor_session", "log_info"]
            else:
                risk_level = "LOW"
                actions = ["normal_operation"]
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "recommended_actions": actions,
                "assessment_timestamp": datetime.utcnow().isoformat(),
                "context": {
                    "ip_address": context.ip_address,
                    "location": context.location,
                    "device_fingerprint": context.device_fingerprint
                }
            }
            
        except Exception as e:
            logger.error(f"Risk assessment error: {str(e)}")
            return {
                "session_id": session_id,
                "user_id": user_id,
                "risk_score": 1.0,
                "risk_level": "CRITICAL",
                "recommended_actions": ["block_session", "notify_security"],
                "error": str(e),
                "assessment_timestamp": datetime.utcnow().isoformat()
            }
    
    @activity.defn
    async def generate_secure_credentials(self, credential_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate secure credentials for user.
        
        Args:
            credential_request: Credential generation request
            
        Returns:
            Generated credentials
        """
        from voluntier.services.auth import AdvancedAuthService
        
        user_id = credential_request["user_id"]
        include_password = credential_request.get("include_password", True)
        include_recovery_codes = credential_request.get("include_recovery_codes", True)
        password_length = credential_request.get("password_length", 21)
        
        logger.info(f"Generating secure credentials for user: {user_id}")
        
        try:
            auth_service = AdvancedAuthService()
            await auth_service.initialize()
            
            credentials = {
                "user_id": user_id,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            if include_password:
                password = await auth_service.generate_secure_password(password_length)
                hashed_password = await auth_service.hash_password(password)
                
                credentials["password"] = password  # Plain text for initial delivery
                credentials["hashed_password"] = hashed_password
                credentials["password_length"] = len(password)
            
            if include_recovery_codes:
                recovery_codes = await auth_service.generate_recovery_codes()
                credentials["recovery_codes"] = recovery_codes
            
            return credentials
            
        except Exception as e:
            logger.error(f"Credential generation error: {str(e)}")
            return {
                "user_id": user_id,
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    @activity.defn
    async def validate_session_security(self, session_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate session security and continuous authentication.
        
        Args:
            session_request: Session validation request
            
        Returns:
            Session validation result
        """
        from voluntier.services.auth import AdvancedAuthService
        
        session_id = session_request["session_id"]
        
        logger.info(f"Validating session security for: {session_id}")
        
        try:
            auth_service = AdvancedAuthService()
            await auth_service.initialize()
            
            session = await auth_service.validate_session(session_id)
            
            if not session:
                return {
                    "valid": False,
                    "session_id": session_id,
                    "reason": "session_not_found_or_expired",
                    "validation_timestamp": datetime.utcnow().isoformat()
                }
            
            # Check continuous authentication score
            continuous_auth_ok = session.continuous_auth_score >= 0.7
            
            # Check risk score
            risk_ok = session.risk_score <= 0.6
            
            # Overall validation
            valid = continuous_auth_ok and risk_ok
            
            return {
                "valid": valid,
                "session_id": session_id,
                "user_id": session.user_id,
                "risk_score": session.risk_score,
                "continuous_auth_score": session.continuous_auth_score,
                "expires_at": session.expires_at.isoformat(),
                "validation_timestamp": datetime.utcnow().isoformat(),
                "issues": [] if valid else [
                    "low_continuous_auth_score" if not continuous_auth_ok else None,
                    "high_risk_score" if not risk_ok else None
                ]
            }
            
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return {
                "valid": False,
                "session_id": session_id,
                "error": str(e),
                "validation_timestamp": datetime.utcnow().isoformat()
            }
    
    @activity.defn
    async def update_user_password(self, password_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user password hash.
        
        Args:
            password_request: Password update request
            
        Returns:
            Update result
        """
        user_id = password_request["user_id"]
        hashed_password = password_request["hashed_password"]
        
        logger.info(f"Updating password hash for user: {user_id}")
        
        try:
            async with get_db_session_context() as session:
                # Get user
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    return {
                        "updated": False,
                        "user_id": user_id,
                        "reason": "user_not_found"
                    }
                
                # Update password
                user.hashed_password = hashed_password
                user.password_last_changed = datetime.utcnow()
                user.failed_login_attempts = 0  # Reset failed attempts
                user.account_lockout_until = None  # Clear any lockout
                
                await session.commit()
                
                return {
                    "updated": True,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Password update error: {str(e)}")
            return {
                "updated": False,
                "user_id": user_id,
                "error": str(e)
            }
    
    async def _log_security_event(self, session: AsyncSession, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log security event to database."""
        try:
            security_log = SecurityLog(
                id=uuid.uuid4(),
                event_type=event_type,
                event_data=event_data,
                timestamp=datetime.utcnow(),
                ip_address=event_data.get("ip_address", "unknown"),
                user_id=uuid.UUID(event_data["user_id"]) if event_data.get("user_id") else None,
            )
            session.add(security_log)
            await session.flush()
        except Exception as e:
            logger.warning(f"Failed to log security event: {str(e)}")


# Export activities instance
auth_activities = AuthActivities()