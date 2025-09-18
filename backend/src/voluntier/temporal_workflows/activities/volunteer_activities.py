"""Volunteer management activities."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from temporalio import activity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from voluntier.database import get_db_session_context
from voluntier.models import User, VerificationStatus, UserRole
from voluntier.services.auth import AuthService
from voluntier.services.verification import VerificationService
from voluntier.services.graph import GraphService
from voluntier.utils.validation import validate_email, validate_phone
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)


class VolunteerActivities:
    """Activities related to volunteer management."""
    
    @activity.defn
    async def validate_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate user profile data.
        
        Args:
            profile_data: User profile data to validate
            
        Returns:
            Validation result with errors if any
        """
        logger.info(f"Validating user profile for email: {profile_data.get('email')}")
        
        errors = []
        warnings = []
        
        # Required fields validation
        required_fields = ["name", "email", "password"]
        for field in required_fields:
            if not profile_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Email validation
        email = profile_data.get("email")
        if email and not validate_email(email):
            errors.append("Invalid email format")
        
        # Phone validation (if provided)
        phone = profile_data.get("phone")
        if phone and not validate_phone(phone):
            errors.append("Invalid phone number format")
        
        # Name validation
        name = profile_data.get("name", "")
        if len(name) < 2:
            errors.append("Name must be at least 2 characters long")
        if len(name) > 100:
            errors.append("Name must be less than 100 characters")
        
        # Skills validation
        skills = profile_data.get("skills", [])
        if not isinstance(skills, list):
            errors.append("Skills must be provided as a list")
        elif len(skills) > 20:
            warnings.append("Consider limiting skills to most relevant ones (current: >20)")
        
        # Interests validation
        interests = profile_data.get("interests", [])
        if not isinstance(interests, list):
            errors.append("Interests must be provided as a list")
        elif len(interests) > 15:
            warnings.append("Consider limiting interests to most relevant ones (current: >15)")
        
        # Bio length validation
        bio = profile_data.get("bio", "")
        if len(bio) > 1000:
            errors.append("Bio must be less than 1000 characters")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": {
                "validation_timestamp": datetime.utcnow().isoformat(),
                "field_count": len(profile_data),
            },
        }
    
    @activity.defn
    async def check_duplicate_registration(self, email: str) -> Dict[str, Any]:
        """
        Check if a user with the given email already exists.
        
        Args:
            email: Email address to check
            
        Returns:
            Result indicating if duplicate exists
        """
        logger.info(f"Checking for duplicate registration: {email}")
        
        async with get_db_session_context() as session:
            # Check for existing user
            stmt = select(User).where(User.email == email.lower())
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                return {
                    "is_duplicate": True,
                    "existing_user_id": str(existing_user.id),
                    "existing_user_status": existing_user.verification_status.value,
                    "created_at": existing_user.created_at.isoformat(),
                }
            
            return {
                "is_duplicate": False,
                "email_available": True,
            }
    
    @activity.defn
    async def create_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user profile in the database.
        
        Args:
            profile_data: User profile data
            
        Returns:
            Created user information
        """
        logger.info(f"Creating user profile for: {profile_data.get('email')}")
        
        auth_service = AuthService()
        
        try:
            # Hash the password
            hashed_password = auth_service.hash_password(profile_data["password"])
            
            # Create user instance
            user = User(
                id=uuid.uuid4(),
                email=profile_data["email"].lower(),
                hashed_password=hashed_password,
                name=profile_data["name"],
                role=UserRole.VOLUNTEER,
                bio=profile_data.get("bio"),
                phone=profile_data.get("phone"),
                location=profile_data.get("location"),
                skills=profile_data.get("skills", []),
                interests=profile_data.get("interests", []),
                verification_status=VerificationStatus.PENDING,
                is_active=True,
                email_verified=False,
            )
            
            async with get_db_session_context() as session:
                session.add(user)
                await session.flush()  # Get the ID
                await session.commit()
                
                logger.info(f"Successfully created user profile: {user.id}")
                
                return {
                    "user_id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "verification_status": user.verification_status.value,
                    "created_at": user.created_at.isoformat(),
                }
        
        except Exception as e:
            logger.error(f"Failed to create user profile: {str(e)}")
            raise
    
    @activity.defn
    async def initiate_verification(self, verification_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate user verification process.
        
        Args:
            verification_request: Verification request details
            
        Returns:
            Verification initiation result
        """
        user_id = verification_request["user_id"]
        verification_type = verification_request["verification_type"]
        
        logger.info(f"Initiating {verification_type} verification for user: {user_id}")
        
        verification_service = VerificationService()
        
        try:
            if verification_type == "email":
                result = await verification_service.initiate_email_verification(
                    user_id=user_id,
                    email=verification_request["metadata"]["email"]
                )
            elif verification_type == "phone":
                result = await verification_service.initiate_phone_verification(
                    user_id=user_id,
                    phone=verification_request["metadata"]["phone"]
                )
            else:
                raise ValueError(f"Unsupported verification type: {verification_type}")
            
            return {
                "verification_initiated": True,
                "verification_type": verification_type,
                "token": result["verification_token"],
                "expires_at": result["expires_at"],
            }
        
        except Exception as e:
            logger.error(f"Failed to initiate verification: {str(e)}")
            raise
    
    @activity.defn
    async def find_matching_volunteers(self, matching_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find volunteers matching event criteria.
        
        Args:
            matching_request: Matching criteria and event details
            
        Returns:
            List of matching volunteer IDs with confidence scores
        """
        event_id = matching_request["event_id"]
        criteria = matching_request["criteria"]
        
        logger.info(f"Finding matching volunteers for event: {event_id}")
        
        try:
            graph_service = GraphService()
            
            # Use graph-based matching for better results
            matching_result = await graph_service.find_volunteer_matches(
                event_id=event_id,
                required_skills=criteria.get("skills", []),
                interests=criteria.get("interests", []),
                location=criteria.get("location"),
                max_distance=criteria.get("max_distance", 50),  # 50km default
                min_confidence=0.3,  # 30% minimum confidence
            )
            
            # Also do SQL-based backup matching
            async with get_db_session_context() as session:
                # Build query for volunteers with matching skills/interests
                stmt = select(User).where(
                    User.role == UserRole.VOLUNTEER,
                    User.is_active == True,
                    User.verification_status == VerificationStatus.VERIFIED,
                )
                
                result = await session.execute(stmt)
                all_volunteers = result.scalars().all()
                
                sql_matches = []
                for volunteer in all_volunteers:
                    confidence = self._calculate_match_confidence(volunteer, criteria)
                    if confidence >= 0.3:  # 30% minimum confidence
                        sql_matches.append({
                            "volunteer_id": str(volunteer.id),
                            "confidence": confidence,
                        })
                
                # Sort by confidence
                sql_matches.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Combine and deduplicate results
            combined_matches = []
            seen_volunteers = set()
            
            # Add graph matches first (typically higher quality)
            for match in matching_result.get("matches", []):
                volunteer_id = match["volunteer_id"]
                if volunteer_id not in seen_volunteers:
                    combined_matches.append(volunteer_id)
                    seen_volunteers.add(volunteer_id)
            
            # Add SQL matches that weren't already included
            for match in sql_matches[:20]:  # Limit to top 20 SQL matches
                volunteer_id = match["volunteer_id"]
                if volunteer_id not in seen_volunteers:
                    combined_matches.append(volunteer_id)
                    seen_volunteers.add(volunteer_id)
            
            logger.info(f"Found {len(combined_matches)} matching volunteers for event {event_id}")
            
            return {
                "matches": combined_matches[:50],  # Limit to top 50 overall
                "total_candidates": len(all_volunteers) if 'all_volunteers' in locals() else 0,
                "graph_matches": len(matching_result.get("matches", [])),
                "sql_matches": len(sql_matches),
                "matching_criteria": criteria,
            }
        
        except Exception as e:
            logger.error(f"Failed to find matching volunteers: {str(e)}")
            raise
    
    def _calculate_match_confidence(self, volunteer: User, criteria: Dict[str, Any]) -> float:
        """
        Calculate confidence score for volunteer-event match.
        
        Args:
            volunteer: Volunteer user object
            criteria: Matching criteria
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0
        
        # Skills matching (40% weight)
        required_skills = set(criteria.get("skills", []))
        volunteer_skills = set(volunteer.skills or [])
        if required_skills:
            skill_overlap = len(required_skills.intersection(volunteer_skills))
            skill_confidence = skill_overlap / len(required_skills)
            confidence += skill_confidence * 0.4
        
        # Interest matching (30% weight)
        interests = set(criteria.get("interests", []))
        volunteer_interests = set(volunteer.interests or [])
        if interests:
            interest_overlap = len(interests.intersection(volunteer_interests))
            interest_confidence = interest_overlap / len(interests)
            confidence += interest_confidence * 0.3
        
        # Location proximity (20% weight)
        # Simplified - in production would use proper geolocation
        if criteria.get("location") and volunteer.location:
            if criteria["location"].lower() in volunteer.location.lower():
                confidence += 0.2
            else:
                confidence += 0.1  # Partial credit for having location
        
        # Volunteer activity level (10% weight)
        if volunteer.events_attended > 0:
            activity_score = min(volunteer.events_attended / 10, 1.0)  # Max out at 10 events
            confidence += activity_score * 0.1
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    @activity.defn
    async def update_volunteer_stats(self, user_id: str, stat_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update volunteer statistics.
        
        Args:
            user_id: Volunteer user ID
            stat_updates: Statistics to update
            
        Returns:
            Updated statistics
        """
        logger.info(f"Updating volunteer stats for user: {user_id}")
        
        try:
            async with get_db_session_context() as session:
                # Get user
                stmt = select(User).where(User.id == uuid.UUID(user_id))
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    raise ValueError(f"User not found: {user_id}")
                
                # Update statistics
                if "hours_logged" in stat_updates:
                    user.hours_logged += stat_updates["hours_logged"]
                
                if "events_attended" in stat_updates:
                    user.events_attended += stat_updates["events_attended"]
                
                if "trust_score_delta" in stat_updates:
                    user.trust_score = max(0, min(1, user.trust_score + stat_updates["trust_score_delta"]))
                
                user.updated_at = datetime.utcnow()
                await session.commit()
                
                return {
                    "user_id": str(user.id),
                    "hours_logged": user.hours_logged,
                    "events_attended": user.events_attended,
                    "trust_score": user.trust_score,
                    "updated_at": user.updated_at.isoformat(),
                }
        
        except Exception as e:
            logger.error(f"Failed to update volunteer stats: {str(e)}")
            raise
    
    @activity.defn
    async def get_volunteer_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        Get personalized volunteer opportunity recommendations.
        
        Args:
            user_id: Volunteer user ID
            
        Returns:
            Recommended opportunities
        """
        logger.info(f"Getting recommendations for volunteer: {user_id}")
        
        try:
            graph_service = GraphService()
            
            # Get recommendations from graph service
            recommendations = await graph_service.get_volunteer_recommendations(
                user_id=user_id,
                limit=20,
                include_metadata=True,
            )
            
            return {
                "recommendations": recommendations,
                "user_id": user_id,
                "generated_at": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Failed to get volunteer recommendations: {str(e)}")
            raise