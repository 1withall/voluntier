"""Match model for connecting volunteers with opportunities.

This module defines matches between users and opportunities with:
- Matching score calculation (location, skills, availability, reputation)
- Distance tracking in kilometers
- Status workflow (pending/accepted/rejected/completed)
- Timestamps for tracking match lifecycle
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.opportunity import Opportunity


class Match(Base):
    """Match between a volunteer and an opportunity.
    
    Represents the result of the matching algorithm connecting users
    to opportunities based on location, skills, availability, and reputation.
    
    Attributes:
        id: Primary key.
        volunteer_id: Foreign key to User (the volunteer).
        opportunity_id: Foreign key to Opportunity.
        
        # Matching Algorithm Results (PRD §3.1.3)
        match_score: Overall matching score (0-100).
        location_score: Location compatibility score (40% weight).
        skills_score: Skills match score (30% weight).
        availability_score: Time availability score (20% weight).
        reputation_score: Reputation score (10% weight).
        distance_km: Physical distance between volunteer and opportunity.
        
        # Status & Workflow
        status: Match state (pending/accepted/rejected/completed/cancelled).
        volunteer_accepted: Whether volunteer accepted the match.
        organizer_accepted: Whether opportunity creator accepted the match.
        
        # Timestamps
        created_at: When the match was created (UTC).
        updated_at: Last status update (UTC).
        accepted_at: When both parties accepted (UTC).
        completed_at: When the opportunity was completed (UTC).
        
    Relationships:
        volunteer: The User volunteering.
        opportunity: The Opportunity being matched.
        
    Indexes:
        - ix_matches_volunteer_id: Fast lookup by volunteer.
        - ix_matches_opportunity_id: Fast lookup by opportunity.
        - ix_matches_status: Filter by status.
        - ix_matches_score: Sort by match quality.
        
    Example:
        >>> match = Match(
        ...     volunteer_id=2,
        ...     opportunity_id=1,
        ...     match_score=87.5,
        ...     location_score=95.0,  # 40% weight
        ...     skills_score=85.0,    # 30% weight
        ...     availability_score=80.0,  # 20% weight
        ...     reputation_score=88.0,    # 10% weight
        ...     distance_km=3.2,
        ...     status="pending",
        ... )
        >>> db.add(match)
        >>> await db.commit()
    """
    
    __tablename__ = "matches"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign Keys
    volunteer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Matching Algorithm Scores (PRD §3.1.3 - Phase 1 Priority)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    location_score: Mapped[float] = mapped_column(Float, nullable=False)  # 40% weight
    skills_score: Mapped[float] = mapped_column(Float, nullable=False)    # 30% weight
    availability_score: Mapped[float] = mapped_column(Float, nullable=False)  # 20% weight
    reputation_score: Mapped[float] = mapped_column(Float, nullable=False)    # 10% weight
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Status & Acceptance
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",  # pending, accepted, rejected, completed, cancelled
        nullable=False,
    )
    volunteer_accepted: Mapped[bool] = mapped_column(default=False, nullable=False)
    organizer_accepted: Mapped[bool] = mapped_column(default=False, nullable=False)
    
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
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    volunteer: Mapped["User"] = relationship(
        foreign_keys=[volunteer_id],
        back_populates="matches_as_volunteer",
    )
    opportunity: Mapped["Opportunity"] = relationship(
        back_populates="matches",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_matches_volunteer_id", "volunteer_id"),
        Index("ix_matches_opportunity_id", "opportunity_id"),
        Index("ix_matches_status", "status"),
        Index("ix_matches_score", "match_score"),
    )
    
    def __repr__(self) -> str:
        return f"<Match(id={self.id}, volunteer={self.volunteer_id}, opportunity={self.opportunity_id}, score={self.match_score})>"
