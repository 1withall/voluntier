"""Review model for reputation and feedback system.

This module defines reviews for the community-based reputation system with:
- Bidirectional reviews (volunteers review organizers, organizers review volunteers)
- Rating scores and detailed feedback
- Time-decay support for reputation calculation
- Appeal/dispute tracking
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Review(Base):
    """Review/feedback for reputation system.
    
    Supports community-based, non-competitive reputation tracking with:
    - Time-decay on old reviews
    - Weighted by reviewer reputation
    - Appeal/dispute process
    - Recovery pathways for negative feedback
    
    Attributes:
        id: Primary key.
        reviewer_id: Foreign key to User who wrote the review.
        reviewee_id: Foreign key to User being reviewed.
        match_id: Optional foreign key to Match this review is about.
        
        # Ratings (1-5 scale)
        overall_rating: Overall experience rating.
        communication_rating: Communication quality rating.
        reliability_rating: Reliability/punctuality rating.
        skill_rating: Skill/competence rating.
        
        # Feedback
        comment: Written feedback (optional).
        is_positive: Whether this is positive feedback.
        
        # Reputation Calculation (PRD §3.1.2 - Phase 1 Priority)
        weight: Calculated weight for this review (based on reviewer reputation).
        time_decay_factor: Time decay multiplier (reduces with age).
        
        # Appeal/Dispute (Phase 1 Feature)
        is_disputed: Whether reviewee disputed this review.
        dispute_reason: Reason for dispute.
        dispute_status: Status of dispute (pending/resolved/rejected).
        dispute_resolved_at: When dispute was resolved.
        
        # Timestamps
        created_at: Review creation timestamp (UTC).
        updated_at: Last modification timestamp (UTC).
        
    Relationships:
        reviewer: User who wrote the review.
        reviewee: User being reviewed.
        
    Indexes:
        - ix_reviews_reviewee_id: Fast lookup of reviews about a user.
        - ix_reviews_reviewer_id: Fast lookup of reviews by a user.
        - ix_reviews_created_at: Time-based queries for decay calculation.
        
    Example:
        >>> review = Review(
        ...     reviewer_id=1,  # Organizer
        ...     reviewee_id=2,  # Volunteer
        ...     match_id=5,
        ...     overall_rating=5,
        ...     communication_rating=5,
        ...     reliability_rating=5,
        ...     skill_rating=4,
        ...     comment="Excellent volunteer, very reliable and skilled!",
        ...     is_positive=True,
        ...     weight=1.0,
        ... )
        >>> db.add(review)
        >>> await db.commit()
    """
    
    __tablename__ = "reviews"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign Keys
    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_id: Mapped[int | None] = mapped_column(
        ForeignKey("matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Ratings (1-5 scale)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    communication_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reliability_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skill_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Feedback
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_positive: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Reputation Calculation (PRD §3.1.2 - Phase 1 Priority)
    weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    time_decay_factor: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    
    # Appeal/Dispute Process (Phase 1 Feature)
    is_disputed: Mapped[bool] = mapped_column(default=False, nullable=False)
    dispute_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispute_status: Mapped[str | None] = mapped_column(
        String(50),  # pending, resolved, rejected
        nullable=True,
    )
    dispute_resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    
    # Relationships
    reviewer: Mapped["User"] = relationship(
        foreign_keys=[reviewer_id],
        back_populates="reviews_given",
    )
    reviewee: Mapped["User"] = relationship(
        foreign_keys=[reviewee_id],
        back_populates="reviews_received",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_reviews_reviewee_id", "reviewee_id"),
        Index("ix_reviews_reviewer_id", "reviewer_id"),
        Index("ix_reviews_created_at", "created_at"),
        Index("ix_reviews_match_id", "match_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, reviewer={self.reviewer_id}, reviewee={self.reviewee_id}, rating={self.overall_rating})>"
