"""SQLAlchemy ORM models for Voluntier application.

This package contains all database models organized by domain:
- User: Authentication and profile information
- Opportunity: Volunteer opportunities with geospatial data
- Match: Matching results between users and opportunities
- Review: Reputation and feedback system

All models inherit from the Base class in app.database and use
SQLAlchemy 2.0+ declarative mapping with type annotations.
"""

from app.models.user import User
from app.models.opportunity import Opportunity
from app.models.match import Match
from app.models.review import Review

__all__ = ["User", "Opportunity", "Match", "Review"]
