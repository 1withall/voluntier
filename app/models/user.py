"""User model for authentication and profile management.

This module defines the User model with:
- Authentication: email/password with bcrypt hashing
- Identity verification: multi-factor verification status
- Profile: name, location, skills, availability
- Reputation: calculated score from reviews
- Timestamps: created_at, updated_at tracking
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Float, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.database import Base

if TYPE_CHECKING:
    from app.models.opportunity import Opportunity
    from app.models.match import Match
    from app.models.review import Review


class User(Base):
    """User account with authentication and profile data.

    Attributes:
        id: Primary key.
        email: Optional email address for login (NOT required).
        hashed_password: Bcrypt hashed password (never store plain text).
        full_name: User's full name or pseudonym.
        is_active: Account enabled/disabled flag.
        is_verified: Deprecated - use verification_score instead.
        is_superuser: Admin privileges flag.

        # Identity Verification (Phase 1 Priority - Scaled 0-100)
        verification_score: Composite score (0-100) from multiple verification methods.
        verification_methods: JSON array of completed verification methods with weights.
        verification_workflow_id: Temporal workflow ID for active verification process.
        trust_network: JSON array of users who vouch for this user with trust strength.
        activity_score: Score derived from volunteer history and platform activity.

        # Profile
        bio: User biography/description.
        skills: Array of skills (e.g., ["teaching", "construction", "translation"]).
        location: PostGIS Point for geospatial matching.
        location_name: Human-readable location (e.g., "San Francisco, CA").
        availability: Serialized availability schedule (JSON).

        # Reputation (Phase 1 Priority)
        reputation_score: Calculated reputation (0-100 scale).
        total_reviews: Number of reviews received.
        total_hours_volunteered: Cumulative volunteer hours.

        # Timestamps
        created_at: Account creation timestamp (UTC).
        updated_at: Last modification timestamp (UTC).
        last_active_at: Last login or activity timestamp.

    Verification Methods (Multiple pathways, not mutually exclusive):
        - Document Upload: Gov ID, utility bills (+20-30 points)
        - Community Validation: Trusted users vouch (+15-25 points per voucher)
        - In-Person Verification: Meet at community center (+30-40 points)
        - Trust Network: Connections to verified users (+5-15 points)
        - Activity History: Successful volunteer hours (+10-20 points)

    Note: NO email requirement. Users can verify through any combination of methods.

    Relationships:
        opportunities_created: Opportunities posted by this user.
        matches_as_volunteer: Matches where user is the volunteer.
        reviews_received: Reviews about this user.
        reviews_given: Reviews written by this user.

    Indexes:
        - ix_users_email: Fast lookup by email for authentication.
        - ix_users_location: GiST index for geospatial queries.
        - ix_users_reputation_score: Fast sorting by reputation.
        - ix_users_verification_score: Fast filtering by verification level.

    Example:
        >>> user = User(
        ...     full_name="Jane Smith",
        ...     skills=["teaching", "mentoring"],
        ...     location="SRID=4326;POINT(-122.4194 37.7749)",  # San Francisco
        ...     verification_score=45.0,  # Community + activity verification
        ... )
        >>> db.add(user)
        >>> await db.commit()
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Authentication (Email is OPTIONAL - users can verify other ways)
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Basic Profile
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Identity Verification (Phase 1 Priority - PRD §3.1.1)
    # Scaled verification score (0-100) instead of binary yes/no
    verification_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,  # 0=no verification, 100=fully verified
        nullable=False,
    )
    # Verification methods completed (JSON array of method names and weights)
    verification_methods: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON: [{"method": "community", "weight": 30, "completed_at": "..."}]
    # Temporal workflow ID for active verification process
    verification_workflow_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    # Trust network connections (JSON array of user IDs who vouch for this user)
    trust_network: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON: [{"user_id": 123, "strength": 0.8, "since": "..."}]
    # Activity-based verification score (derived from volunteer history)
    activity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Location (PostGIS Point - WGS84 coordinates)
    location: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Skills & Availability (stored as JSON in production, simplified for Phase 1)
    skills: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON array as text
    availability: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON object as text

    # Reputation (Phase 1 Priority - PRD §3.1.2)
    reputation_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_reviews: Mapped[int] = mapped_column(default=0, nullable=False)
    total_hours_volunteered: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )

    # Timestamps (UTC)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships (use TYPE_CHECKING to avoid circular imports)
    opportunities_created: Mapped[list["Opportunity"]] = relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
    )
    matches_as_volunteer: Mapped[list["Match"]] = relationship(
        foreign_keys="Match.volunteer_id",
        back_populates="volunteer",
    )
    reviews_received: Mapped[list["Review"]] = relationship(
        foreign_keys="Review.reviewee_id",
        back_populates="reviewee",
    )
    reviews_given: Mapped[list["Review"]] = relationship(
        foreign_keys="Review.reviewer_id",
        back_populates="reviewer",
    )

    # Indexes
    __table_args__ = (
        Index("ix_users_reputation_score", "reputation_score"),
        Index("ix_users_location", "location", postgresql_using="gist"),
        Index("ix_users_verification_score", "verification_score"),
        Index("ix_users_workflow_id", "verification_workflow_id"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, reputation={self.reputation_score})>"
