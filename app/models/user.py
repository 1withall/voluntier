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
        email: Unique email address for login.
        hashed_password: Bcrypt hashed password (never store plain text).
        full_name: User's full name.
        is_active: Account enabled/disabled flag.
        is_verified: Email verification status.
        is_superuser: Admin privileges flag.

        # Identity Verification (Phase 1 Priority)
        verification_status: Multi-factor verification state (pending/partial/verified).
        verification_methods: JSON array of completed verification methods.
        document_verified: Document upload verification complete.
        community_verified: Community validation complete.
        in_person_verified: In-person verification complete.

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

    Relationships:
        opportunities_created: Opportunities posted by this user.
        matches_as_volunteer: Matches where user is the volunteer.
        reviews_received: Reviews about this user.
        reviews_given: Reviews written by this user.

    Indexes:
        - ix_users_email: Fast lookup by email for authentication.
        - ix_users_location: GiST index for geospatial queries.
        - ix_users_reputation_score: Fast sorting by reputation.

    Example:
        >>> user = User(
        ...     email="volunteer@example.com",
        ...     hashed_password=hash_password("secret"),
        ...     full_name="Jane Smith",
        ...     skills=["teaching", "mentoring"],
        ...     location="SRID=4326;POINT(-122.4194 37.7749)",  # San Francisco
        ... )
        >>> db.add(user)
        >>> await db.commit()
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
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
    verification_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",  # pending, partial, verified, rejected
        nullable=False,
    )
    document_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    community_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    in_person_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

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
        Index("ix_users_verification_status", "verification_status"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, reputation={self.reputation_score})>"
