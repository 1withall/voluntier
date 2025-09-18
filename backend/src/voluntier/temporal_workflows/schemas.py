"""Pydantic schemas for Temporal workflow requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VolunteerRegistrationRequest(BaseModel):
    """Request schema for volunteer registration workflow."""
    
    user_id: Optional[UUID] = None
    profile_data: Dict[str, Any] = Field(..., description="User profile data including name, email, skills, etc.")
    verification_level: str = Field(default="basic", description="Level of verification required")
    source: str = Field(default="web", description="Registration source (web, mobile, api)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EventCreationRequest(BaseModel):
    """Request schema for event creation workflow."""
    
    organizer_id: UUID = Field(..., description="ID of the event organizer")
    event_data: Dict[str, Any] = Field(..., description="Event details including title, description, date, etc.")
    auto_publish: bool = Field(default=False, description="Whether to auto-publish the event")
    notification_preferences: Dict[str, Any] = Field(default_factory=dict, description="Notification preferences")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class NotificationRequest(BaseModel):
    """Request schema for notification workflow."""
    
    user_id: UUID = Field(..., description="Target user ID")
    type: str = Field(..., description="Notification type (welcome, event_opportunity, etc.)")
    content: Dict[str, Any] = Field(..., description="Notification content")
    delivery_method: str = Field(default="email", description="Delivery method (email, sms, push)")
    priority: str = Field(default="normal", description="Priority level (low, normal, high, urgent)")
    scheduled_time: Optional[datetime] = Field(default=None, description="Scheduled delivery time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SecurityThreatAlert(BaseModel):
    """Schema for security threat alerts."""
    
    threat_type: str = Field(..., description="Type of threat detected")
    severity: str = Field(..., description="Threat severity (low, medium, high, critical)")
    source_ip: Optional[str] = Field(default=None, description="Source IP address")
    user_id: Optional[UUID] = Field(default=None, description="Associated user ID")
    endpoint: Optional[str] = Field(default=None, description="Affected endpoint")
    details: Dict[str, Any] = Field(..., description="Detailed threat information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DataSyncRequest(BaseModel):
    """Request schema for data synchronization workflow."""
    
    sync_type: str = Field(..., description="Type of sync (full, incremental, specific)")
    source: str = Field(..., description="Data source identifier")
    target: str = Field(..., description="Data target identifier")
    target_tables: List[str] = Field(default_factory=list, description="Tables to sync")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Sync filters")
    expected_changes: Optional[int] = Field(default=None, description="Expected number of changes")
    dry_run: bool = Field(default=False, description="Whether this is a dry run")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentDecisionRequest(BaseModel):
    """Request schema for agent decision-making workflow."""
    
    context: Dict[str, Any] = Field(..., description="Decision context and current state")
    available_actions: List[str] = Field(..., description="Available actions the agent can take")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Constraints and limitations")
    historical_data: Dict[str, Any] = Field(default_factory=dict, description="Historical context and data")
    urgency: str = Field(default="normal", description="Urgency level (low, normal, high, critical)")
    requester_id: Optional[UUID] = Field(default=None, description="ID of the requesting entity")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkflowResponse(BaseModel):
    """Generic workflow response schema."""
    
    status: str = Field(..., description="Workflow execution status")
    message: Optional[str] = Field(default=None, description="Status message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")


class ActivityRequest(BaseModel):
    """Base schema for activity requests."""
    
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ActivityResponse(BaseModel):
    """Base schema for activity responses."""
    
    success: bool = Field(..., description="Whether the activity succeeded")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")


class VolunteerProfileValidationRequest(ActivityRequest):
    """Request schema for volunteer profile validation activity."""
    
    profile_data: Dict[str, Any] = Field(..., description="Profile data to validate")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules to apply")


class EventValidationRequest(ActivityRequest):
    """Request schema for event validation activity."""
    
    event_data: Dict[str, Any] = Field(..., description="Event data to validate")
    organizer_id: UUID = Field(..., description="Event organizer ID")
    validation_level: str = Field(default="standard", description="Validation level")


class NotificationDeliveryRequest(ActivityRequest):
    """Request schema for notification delivery activity."""
    
    user_id: UUID = Field(..., description="Target user ID")
    content: Dict[str, Any] = Field(..., description="Notification content")
    delivery_method: str = Field(..., description="Delivery method")
    priority: str = Field(default="normal", description="Priority level")


class SecurityAnalysisRequest(ActivityRequest):
    """Request schema for security analysis activity."""
    
    alert_data: Dict[str, Any] = Field(..., description="Security alert data")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    analysis_type: str = Field(default="threat_assessment", description="Type of analysis to perform")


class LLMAnalysisRequest(ActivityRequest):
    """Request schema for LLM analysis activity."""
    
    prompt: str = Field(..., description="Analysis prompt")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context data")
    model: str = Field(default="default", description="LLM model to use")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, description="Temperature for generation")


class GraphUpdateRequest(ActivityRequest):
    """Request schema for graph database update activity."""
    
    entity_type: str = Field(..., description="Type of entity (user, event, organization)")
    entity_id: UUID = Field(..., description="Entity ID")
    action: str = Field(..., description="Action to perform (create, update, delete)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Entity properties")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Relationships to create/update")


class BackupRequest(ActivityRequest):
    """Request schema for backup activity."""
    
    backup_type: str = Field(..., description="Type of backup (full, incremental, table-specific)")
    target_tables: List[str] = Field(default_factory=list, description="Tables to backup")
    retention_days: int = Field(default=30, description="Backup retention period")
    compress: bool = Field(default=True, description="Whether to compress backup")


class ValidationResult(BaseModel):
    """Schema for validation results."""
    
    valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional validation metadata")


class MatchingResult(BaseModel):
    """Schema for volunteer matching results."""
    
    matches: List[UUID] = Field(..., description="List of matched volunteer IDs")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores for matches")
    matching_criteria: Dict[str, Any] = Field(default_factory=dict, description="Criteria used for matching")
    total_candidates: int = Field(..., description="Total number of candidates evaluated")


class SecurityAnalysisResult(BaseModel):
    """Schema for security analysis results."""
    
    threat_level: str = Field(..., description="Assessed threat level")
    confidence: float = Field(..., description="Confidence in assessment")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended response actions")
    indicators: Dict[str, Any] = Field(default_factory=dict, description="Threat indicators found")
    context: Dict[str, Any] = Field(default_factory=dict, description="Analysis context")


class LLMAnalysisResult(BaseModel):
    """Schema for LLM analysis results."""
    
    analysis: str = Field(..., description="LLM analysis result")
    confidence: float = Field(..., description="Confidence in analysis")
    reasoning: str = Field(..., description="Reasoning behind analysis")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional analysis metadata")


class ExecutionResult(BaseModel):
    """Schema for execution results."""
    
    success: bool = Field(..., description="Whether execution succeeded")
    result_data: Dict[str, Any] = Field(default_factory=dict, description="Execution result data")
    side_effects: List[str] = Field(default_factory=list, description="Side effects of execution")
    rollback_info: Optional[Dict[str, Any]] = Field(default=None, description="Information for potential rollback")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional execution metadata")