"""Opportunity model for volunteer opportunities with geospatial data.

This module defines volunteer opportunities with:
- PostGIS location for geospatial matching
- Time/duration requirements
- Skills required
- Creator relationship to User
- Status tracking (open/filled/cancelled)
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.match import Match


class Opportunity(Base):
    """Volunteer opportunity with geospatial location.
    
    Attributes:
        id: Primary key.
        title: Opportunity title/summary.
        description: Detailed description of the opportunity.
        creator_id: Foreign key to User who created this opportunity.
        
        # Location (PostGIS - Phase 1 Priority)
        location: PostGIS Point for geospatial matching with ST_DWithin.
        location_name: Human-readable address.
        max_distance_km: Maximum distance volunteers can be from location.
        
        # Time & Duration
        start_time: When the opportunity starts (UTC).
        end_time: When the opportunity ends (UTC).
        duration_hours: Expected time commitment in hours.
        
        # Requirements
        skills_required: JSON array of required skills.
        min_reputation: Minimum reputation score required (0-100).
        volunteers_needed: Number of volunteers needed.
        volunteers_confirmed: Number of confirmed matches.
        
        # Status
        status: Opportunity state (open/filled/cancelled/completed).
        is_remote: Whether opportunity can be done remotely.
        
        # Timestamps
        created_at: Creation timestamp (UTC).
        updated_at: Last modification timestamp (UTC).
        
    Relationships:
        creator: User who posted this opportunity.
        matches: Matching results for this opportunity.
        
    Indexes:
        - ix_opportunities_location: GiST index for ST_DWithin queries (Phase 1 critical).
        - ix_opportunities_start_time: Fast sorting by start time.
        - ix_opportunities_status: Filter by status.
        
    Example:
        >>> opportunity = Opportunity(
        ...     title="Food Bank Volunteer",
        ...     description="Help sort and distribute food to families in need",
        ...     creator_id=1,
        ...     location="SRID=4326;POINT(-122.4194 37.7749)",  # San Francisco
        ...     location_name="SF-Marin Food Bank, 900 Pennsylvania Ave",
        ...     start_time=datetime(2025, 11, 15, 9, 0),
        ...     duration_hours=4.0,
        ...     skills_required='["physical labor", "customer service"]',
        ...     volunteers_needed=10,
        ... )
        >>> db.add(opportunity)
        >>> await db.commit()
    """
    
    __tablename__ = "opportunities"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic Info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Creator (User who posted this)
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Location (PostGIS Point - WGS84 coordinates)
    location: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    location_name: Mapped[str] = mapped_column(String(500), nullable=False)
    max_distance_km: Mapped[float] = mapped_column(
        Float,
        default=50.0,  # Default 50km radius
        nullable=False,
    )
    
    # Time & Duration
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Requirements
    skills_required: Mapped[str | None] = mapped_column(
        Text,  # JSON array as text for Phase 1
        nullable=True,
    )
    min_reputation: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    volunteers_needed: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    volunteers_confirmed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="open",  # open, filled, cancelled, completed
        nullable=False,
    )
    is_remote: Mapped[bool] = mapped_column(default=False, nullable=False)
    
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
    
    # Relationships
    creator: Mapped["User"] = relationship(
        back_populates="opportunities_created",
    )
    matches: Mapped[list["Match"]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
    
    # Indexes (Phase 1 Priority - PRD §3.1.3 Geospatial Matching)
    __table_args__ = (
        Index("ix_opportunities_location", "location", postgresql_using="gist"),
        Index("ix_opportunities_start_time", "start_time"),
        Index("ix_opportunities_status", "status"),
        Index("ix_opportunities_creator_id", "creator_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Opportunity(id={self.id}, title={self.title}, status={self.status})>"
