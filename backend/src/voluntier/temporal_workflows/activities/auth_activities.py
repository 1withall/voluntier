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
from voluntier.services.auth import AuthService
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
            auth_service = AuthService()
            
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
            auth_service = AuthService()
            
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